import os
import numpy as np

from .assets import ensure_asset, resolve_asset_name


class TrtRunner:
    def __init__(self, engine_path):
        import tensorrt as trt
        try:
            from cuda.bindings import runtime as cudart
        except ImportError:
            try:
                from cuda import cudart
            except ImportError as exc:
                raise SystemExit(
                    "cuda-python is required for TensorRT engine execution. "
                    "Install it with: python -m pip install cuda-python"
                ) from exc

        self._trt = trt
        self._cudart = cudart
        logger = trt.Logger(trt.Logger.WARNING)
        runtime = trt.Runtime(logger)
        with open(engine_path, "rb") as file:
            engine_data = file.read()
        engine = runtime.deserialize_cuda_engine(engine_data)
        if engine is None:
            raise RuntimeError(f"Failed to deserialize TensorRT engine: {engine_path}")

        self._engine = engine
        self._context = engine.create_execution_context()
        if self._context is None:
            raise RuntimeError("Failed to create TensorRT execution context.")

        err, stream = self._cudart.cudaStreamCreate()
        self._check_cuda(err, "cudaStreamCreate")
        self._stream = stream

        self._inputs = []
        self._outputs = []
        self._name_to_index = {}
        self._dtype = {}
        self._buffers = {}
        self._static_shapes = {}

        if hasattr(engine, "num_io_tensors"):
            for i in range(engine.num_io_tensors):
                name = engine.get_tensor_name(i)
                mode = engine.get_tensor_mode(name)
                if mode == trt.TensorIOMode.INPUT:
                    self._inputs.append(name)
                else:
                    self._outputs.append(name)
                self._dtype[name] = trt.nptype(engine.get_tensor_dtype(name))
                if mode == trt.TensorIOMode.INPUT and hasattr(engine, "get_tensor_shape"):
                    shape = tuple(int(x) for x in engine.get_tensor_shape(name))
                    if all(dim > 0 for dim in shape):
                        self._static_shapes[name] = shape
        else:
            for i in range(engine.num_bindings):
                self._name_to_index[engine.get_binding_name(i)] = i
                if engine.binding_is_input(i):
                    self._inputs.append(engine.get_binding_name(i))
                else:
                    self._outputs.append(engine.get_binding_name(i))
                self._dtype[engine.get_binding_name(i)] = trt.nptype(engine.get_binding_dtype(i))
                if engine.binding_is_input(i):
                    shape = tuple(int(x) for x in engine.get_binding_shape(i))
                    if all(dim > 0 for dim in shape):
                        self._static_shapes[engine.get_binding_name(i)] = shape

    def _unwrap_err(self, err):
        if isinstance(err, tuple):
            err = err[0]
        return err

    def _cuda_error_string(self, err):
        try:
            msg = self._cudart.cudaGetErrorString(err)
            if isinstance(msg, tuple):
                if len(msg) > 1:
                    msg = msg[1]
                else:
                    msg = msg[0]
            return msg
        except Exception as exc:
            return str(exc)

    def _check_cuda(self, err, where):
        err = self._unwrap_err(err)
        if err != self._cudart.cudaError_t.cudaSuccess:
            raise RuntimeError(f"{where} failed: {self._cuda_error_string(err)}")

    def _set_input_shape(self, name, shape):
        shape = tuple(int(x) for x in shape)
        if name in self._static_shapes:
            if shape != self._static_shapes[name]:
                raise ValueError(
                    f"Input {name} shape {shape} does not match engine shape "
                    f"{self._static_shapes[name]}"
                )
            return
        if hasattr(self._context, "set_input_shape"):
            self._context.set_input_shape(name, shape)
        else:
            index = self._name_to_index[name]
            self._context.set_binding_shape(index, shape)

    def _get_tensor_shape(self, name):
        if hasattr(self._context, "get_tensor_shape"):
            return tuple(self._context.get_tensor_shape(name))
        index = self._name_to_index[name]
        return tuple(self._context.get_binding_shape(index))

    def _alloc(self, name, shape, dtype):
        shape = tuple(int(x) for x in shape)
        dtype = np.dtype(dtype)
        size = int(np.prod(shape)) * dtype.itemsize

        buf = self._buffers.get(name)
        if buf and buf["shape"] == shape and buf["dtype"] == dtype:
            return

        if buf:
            err = self._cudart.cudaFree(buf["device"])
            self._check_cuda(err, "cudaFree")

        err, device = self._cudart.cudaMalloc(size)
        self._check_cuda(err, "cudaMalloc")
        host = np.empty(shape, dtype=dtype)
        self._buffers[name] = {"host": host, "device": device, "shape": shape, "dtype": dtype}

    def infer(self, left, right):
        inputs = {"left": left, "right": right}
        for name in self._inputs:
            if name not in inputs:
                raise ValueError(f"Missing input tensor: {name}")

            arr = np.ascontiguousarray(inputs[name].astype(self._dtype[name], copy=False))
            self._set_input_shape(name, arr.shape)
            self._alloc(name, arr.shape, arr.dtype)
            self._buffers[name]["host"][...] = arr

        for name in self._outputs:
            shape = self._get_tensor_shape(name)
            self._alloc(name, shape, self._dtype[name])

        for name in self._inputs:
            buf = self._buffers[name]
            err = self._cudart.cudaMemcpyAsync(
                buf["device"],
                buf["host"],
                buf["host"].nbytes,
                self._cudart.cudaMemcpyKind.cudaMemcpyHostToDevice,
                self._stream,
            )
            self._check_cuda(err, "cudaMemcpyAsync H2D")
            if hasattr(self._context, "set_tensor_address"):
                self._context.set_tensor_address(name, buf["device"])

        for name in self._outputs:
            buf = self._buffers[name]
            if hasattr(self._context, "set_tensor_address"):
                self._context.set_tensor_address(name, buf["device"])

        if hasattr(self._context, "execute_async_v3"):
            ok = self._context.execute_async_v3(self._stream)
        else:
            bindings = []
            for name in self._inputs + self._outputs:
                bindings.append(int(self._buffers[name]["device"]))
            ok = self._context.execute_async_v2(bindings, self._stream)
        if not ok:
            raise RuntimeError("TensorRT execution failed.")

        for name in self._outputs:
            buf = self._buffers[name]
            err = self._cudart.cudaMemcpyAsync(
                buf["host"],
                buf["device"],
                buf["host"].nbytes,
                self._cudart.cudaMemcpyKind.cudaMemcpyDeviceToHost,
                self._stream,
            )
            self._check_cuda(err, "cudaMemcpyAsync D2H")

        err = self._cudart.cudaStreamSynchronize(self._stream)
        self._check_cuda(err, "cudaStreamSynchronize")

        return [self._buffers[name]["host"].copy() for name in self._outputs]

    def get_static_input_shape(self):
        if not self._static_shapes:
            return None
        shapes = list(self._static_shapes.values())
        h, w = shapes[0][2], shapes[0][3]
        return (h, w)


class StereoInference:
    def __init__(
        self,
        trt_path=None,
        trt_width=0,
        trt_height=0,
        intrinsics=None,
        extrinsics=None,
        color_intrinsics=None,
        extrinsics_ir_to_color=None,
        z_far=0.0,
    ):
        self._runner = None
        self._trt_path = None
        self._asset_name = None

        if trt_path and not str(trt_path).endswith((".engine", ".plan")):
            raise ValueError("Unsupported TensorRT model format. Use .engine or .plan.")

        if trt_path and os.path.exists(trt_path):
            self._trt_path = trt_path
            self._load_runner()
        else:
            asset_name = resolve_asset_name(trt_path)
            if asset_name is None:
                if trt_path:
                    raise FileNotFoundError(f"TensorRT model not found: {trt_path}")
                raise ValueError("Missing trt_path.")
            if not asset_name.endswith((".engine", ".plan")):
                raise ValueError("Unsupported TensorRT model format. Use .engine or .plan.")
            self._asset_name = asset_name
            if trt_width > 0 and trt_height > 0:
                self.input_shape = (int(trt_height), int(trt_width))
            else:
                self.input_shape = None
        self.intrinsics = None
        self.extrinsics = None
        self.color_intrinsics = None
        self.extrinsics_ir_to_color = None
        self.fx = None
        self.baseline = None
        self._fx_shape = None
        self.set_calibration(intrinsics=intrinsics, extrinsics=extrinsics)
        self.set_alignment(
            color_intrinsics=color_intrinsics,
            extrinsics_ir_to_color=extrinsics_ir_to_color,
        )
        self.z_far = float(z_far) if z_far is not None else 0.0

        if self.input_shape is None and trt_width > 0 and trt_height > 0:
            self.input_shape = (int(trt_height), int(trt_width))

    def _load_runner(self):
        if self._runner is not None:
            return
        trt_path = self._trt_path
        if not trt_path:
            if not self._asset_name:
                raise ValueError("Missing trt_path.")
            trt_path = ensure_asset(self._asset_name)
            self._trt_path = trt_path
        self._runner = TrtRunner(trt_path)
        self.input_shape = self._runner.get_static_input_shape()

    def ensure_loaded(self):
        self._load_runner()
        return self._runner

    def _to_3ch(self, img):
        if img.ndim == 2:
            return np.repeat(img[:, :, None], 3, axis=2)
        if img.ndim == 3 and img.shape[2] == 1:
            return np.repeat(img, 3, axis=2)
        return img

    def set_calibration(self, intrinsics=None, extrinsics=None):
        if intrinsics is not None:
            self.intrinsics = intrinsics
        if extrinsics is not None:
            self.extrinsics = extrinsics
        self.fx = None
        self.baseline = None
        self._fx_shape = None
        if self.extrinsics is not None:
            self.baseline = self._compute_baseline(self.extrinsics)

    def set_alignment(self, color_intrinsics=None, extrinsics_ir_to_color=None):
        if color_intrinsics is not None:
            self.color_intrinsics = color_intrinsics
        if extrinsics_ir_to_color is not None:
            self.extrinsics_ir_to_color = extrinsics_ir_to_color

    def _get_attr(self, obj, name, default=None):
        if obj is None:
            return default
        if isinstance(obj, dict):
            return obj.get(name, default)
        return getattr(obj, name, default)

    def _resolve_intrinsics(self, intr, target_shape=None):
        fx = self._get_attr(intr, "fx")
        fy = self._get_attr(intr, "fy")
        ppx = self._get_attr(intr, "ppx")
        ppy = self._get_attr(intr, "ppy")
        if fx is None or fy is None or ppx is None or ppy is None:
            raise ValueError("intrinsics must provide fx, fy, ppx, ppy.")

        width = self._get_attr(intr, "width")
        height = self._get_attr(intr, "height")
        if target_shape is None:
            if width is None or height is None:
                raise ValueError("intrinsics must provide width and height.")
            return {
                "fx": float(fx),
                "fy": float(fy),
                "ppx": float(ppx),
                "ppy": float(ppy),
                "width": int(width),
                "height": int(height),
            }

        target_h, target_w = target_shape
        if width is not None and height is not None:
            scale_x = float(target_w) / float(width)
            scale_y = float(target_h) / float(height)
        else:
            scale_x = 1.0
            scale_y = 1.0

        return {
            "fx": float(fx) * scale_x,
            "fy": float(fy) * scale_y,
            "ppx": float(ppx) * scale_x,
            "ppy": float(ppy) * scale_y,
            "width": int(target_w),
            "height": int(target_h),
        }

    def _compute_fx(self, in_shape):
        intr = self.intrinsics
        fx = self._get_attr(intr, "fx")
        if fx is None:
            return None
        width = self._get_attr(intr, "width")
        height = self._get_attr(intr, "height")
        in_h, in_w = in_shape
        if width and height:
            scale_x = float(in_w) / float(width)
        else:
            scale_x = 1.0
        return float(fx) * scale_x

    def _compute_baseline(self, extr):
        translation = self._get_attr(extr, "translation")
        if translation is None:
            return None
        vec = np.asarray(translation, dtype=np.float32)
        if vec.size < 3:
            return None
        return float(np.linalg.norm(vec[:3]))

    def align_depth_splat(
        self,
        depth_ir,
        color_intrinsics=None,
        extrinsics_ir_to_color=None,
        ir_intrinsics=None,
        out_size=None,
        splat_size=2,
        z_far=None,
    ):
        if depth_ir is None or np.ndim(depth_ir) != 2:
            raise ValueError("depth_ir must be a 2D array.")
        if splat_size < 1:
            raise ValueError("splat_size must be >= 1.")

        if ir_intrinsics is None:
            ir_intrinsics = self.intrinsics
        if ir_intrinsics is None:
            raise ValueError("ir_intrinsics is required for alignment.")

        if color_intrinsics is None:
            color_intrinsics = self.color_intrinsics
        if color_intrinsics is None:
            raise ValueError("color_intrinsics is required for alignment.")

        if extrinsics_ir_to_color is None:
            extrinsics_ir_to_color = self.extrinsics_ir_to_color
        if extrinsics_ir_to_color is None:
            raise ValueError("extrinsics_ir_to_color is required for alignment.")

        depth = np.asarray(depth_ir, dtype=np.float32)
        ir_intr = self._resolve_intrinsics(ir_intrinsics, target_shape=depth.shape)

        if out_size is None:
            color_intr = self._resolve_intrinsics(color_intrinsics, target_shape=None)
        else:
            color_intr = self._resolve_intrinsics(color_intrinsics, target_shape=out_size)

        ys, xs = np.indices(depth.shape, dtype=np.float32)
        zs = depth.reshape(-1)
        xs = xs.reshape(-1)
        ys = ys.reshape(-1)

        valid = np.isfinite(zs) & (zs > 0)
        if not np.any(valid):
            return np.full((color_intr["height"], color_intr["width"]), np.nan, dtype=np.float32)

        xs = xs[valid]
        ys = ys[valid]
        zs = zs[valid]

        x = (xs - ir_intr["ppx"]) * zs / ir_intr["fx"]
        y = (ys - ir_intr["ppy"]) * zs / ir_intr["fy"]

        r = self._get_attr(extrinsics_ir_to_color, "rotation")
        t = self._get_attr(extrinsics_ir_to_color, "translation")
        if r is None or t is None:
            raise ValueError("extrinsics_ir_to_color must provide rotation and translation.")

        x_c = r[0] * x + r[3] * y + r[6] * zs + t[0]
        y_c = r[1] * x + r[4] * y + r[7] * zs + t[1]
        z_c = r[2] * x + r[5] * y + r[8] * zs + t[2]

        valid = z_c > 0
        x_c = x_c[valid]
        y_c = y_c[valid]
        z_c = z_c[valid]

        u = (x_c * color_intr["fx"] / z_c) + color_intr["ppx"]
        v = (y_c * color_intr["fy"] / z_c) + color_intr["ppy"]

        u0 = np.floor(u).astype(np.int32)
        v0 = np.floor(v).astype(np.int32)

        color_h, color_w = color_intr["height"], color_intr["width"]
        depth_flat = np.full(color_h * color_w, np.inf, dtype=np.float32)

        offsets = range(splat_size)
        for ox in offsets:
            for oy in offsets:
                uu = u0 + ox
                vv = v0 + oy
                in_bounds = (uu >= 0) & (uu < color_w) & (vv >= 0) & (vv < color_h)
                if not np.any(in_bounds):
                    continue
                uu = uu[in_bounds]
                vv = vv[in_bounds]
                zz = z_c[in_bounds]
                flat = (vv * color_w + uu).astype(np.int64)
                np.minimum.at(depth_flat, flat, zz)

        depth_color = depth_flat.reshape(color_h, color_w)
        depth_color[~np.isfinite(depth_color)] = np.nan

        if z_far is None:
            z_far = self.z_far
        if z_far and z_far > 0:
            depth_color = np.clip(depth_color, 0.0, z_far)

        return depth_color

    def infer(self, left_ir, right_ir, return_depth=False):
        self._load_runner()
        left = self._to_3ch(left_ir)
        right = self._to_3ch(right_ir)
        if left.shape[:2] != right.shape[:2]:
            raise ValueError("left/right image sizes do not match.")

        if self.input_shape is None:
            self.input_shape = (left.shape[0], left.shape[1])

        in_h, in_w = self.input_shape
        if (left.shape[0], left.shape[1]) != (in_h, in_w):
            raise ValueError(
                f"Input size {(left.shape[0], left.shape[1])} does not match "
                f"engine input {(in_h, in_w)}. Resize left/right images before calling infer."
            )

        left = np.ascontiguousarray(left.astype(np.float32)[None].transpose(0, 3, 1, 2))
        right = np.ascontiguousarray(right.astype(np.float32)[None].transpose(0, 3, 1, 2))
        disp = self._runner.infer(left, right)[0]
        disp = np.asarray(disp).squeeze().astype(np.float32)
        if not return_depth:
            return disp

        if self._fx_shape != (in_h, in_w) or self.fx is None:
            self.fx = self._compute_fx((in_h, in_w))
            self._fx_shape = (in_h, in_w)
        if self.baseline is None and self.extrinsics is not None:
            self.baseline = self._compute_baseline(self.extrinsics)

        if self.fx is None or self.baseline is None:
            raise ValueError("intrinsics and extrinsics are required to return depth.")

        depth = (self.fx * self.baseline) / disp
        if self.z_far > 0:
            depth = np.clip(depth, 0.0, self.z_far)
        return depth
