# neuromeka_stereo

TensorRT stereo inference utilities packaged for PyPI.

## 1. Install
### 1.1 Python package
```bash
pip install neuromeka_stereo
```

### 1.2 TensorRT runtime (plan execution)
```bash
python -m pip install --extra-index-url https://pypi.nvidia.com tensorrt-cu12==10.14.1.48.post1
python -m pip install "cuda-python<13"  # CUDA 12.x drivers
```

If your driver is CUDA 13.x, install the latest `cuda-python` instead.

### 1.3 Assets (manual placement required)
Until official download URLs are published, plan/onnx files must be placed
manually. If a required plan file is missing or empty, `StereoInference` raises
an error with the expected path and filename.

Place plan files here (preferred for this repo):
```
src/neuromeka_stereo/assets/
```

Or place them in the cache directory:
```
~/.cache/neuromeka_stereo
```

Expected filenames:
- `foundation_stereo_480x640_RTX4060.plan`
- `foundation_stereo_480x640_RTX5060.plan`
- `foundation_stereo_480x640_RTX5090.plan`

Default selection:
- If `trt_path` is omitted, `NEUROMEKA_STEREO_DEFAULT_PLAN` is used.
- If that is not set, the default is `foundation_stereo_480x640_RTX4060.plan`.

## 2. Usage
### 2.1 StereoInference API
Basic usage:
```python
from neuromeka_stereo import StereoInference

fs = StereoInference(
    trt_path="foundation_stereo_480x640_RTX4060.plan",
    trt_width=640,
    trt_height=480,
    intrinsics=intrinsics,
    extrinsics=extrinsics,
    color_intrinsics=color_intrinsics,
    extrinsics_ir_to_color=extrinsics_ir_to_color,
    z_far=10.0
)

disp = fs.infer(left_ir, right_ir)
depth_m = fs.infer(left_ir, right_ir, return_depth=True)
depth_aligned = fs.align_depth_splat(depth_m, out_size=(color_height, color_width))
```

`StereoInference(trt_path=None, trt_width=0, trt_height=0, intrinsics=None, extrinsics=None, color_intrinsics=None, extrinsics_ir_to_color=None, z_far=0.0)`
- `trt_path`: Path to a `.plan`/`.engine`. If omitted or not found, it is
  treated as an asset name. The default asset is `foundation_stereo_480x640_RTX4060.plan`.
  If no local asset exists, a `FileNotFoundError` is raised.
- `trt_width`, `trt_height`: Optional input size override. Required for dynamic
  engines that do not expose a fixed input shape. If the engine has a fixed
  shape, that shape is used instead.
- `intrinsics`: Camera intrinsics for the left IR image. Must provide `fx` and
  the source resolution (`width`, `height`). The class scales `fx` to the
  inference resolution internally. RealSense intrinsics objects are supported.
- `extrinsics`: Stereo extrinsics between IR1 and IR2. Must provide a
  `translation` vector (meters). The baseline is the translation norm.
- `color_intrinsics`: Intrinsics for the RGB camera used in alignment.
- `extrinsics_ir_to_color`: Extrinsics from IR1 to RGB for alignment.
- `z_far`: Depth clip in meters. Set to `0` to disable clipping.

`infer(left_ir, right_ir, return_depth=False)`
- `left_ir`, `right_ir`: NumPy arrays with matching `H x W`. Supported shapes
  are `(H, W)`, `(H, W, 1)`, `(H, W, 3)`. Grayscale inputs are replicated to
  3 channels. Values are converted to `float32` internally.
- If input size does not match the engine input, a `ValueError` is raised.
  Resize inputs to the engine shape before calling `infer()`.
- Output is a disparity map (`float32`) in pixels with shape `(H, W)`.
- If `return_depth=True`, `intrinsics` and `extrinsics` must be set. The
  returned depth is in meters and optionally clipped by `z_far`.

`align_depth_splat(depth_ir, color_intrinsics=None, extrinsics_ir_to_color=None, ir_intrinsics=None, out_size=None, splat_size=2, z_far=None)`
- Aligns a depth map (IR space) into the RGB frame using a splat projection.
- `depth_ir`: Depth map from `infer(..., return_depth=True)`.
- `color_intrinsics`: Intrinsics for the RGB camera (optional if set on the instance).
- `extrinsics_ir_to_color`: Extrinsics from IR1 to RGB (optional if set on the instance).
- `ir_intrinsics`: Intrinsics for the IR camera. If omitted, uses `self.intrinsics`.
- `out_size`: `(H, W)` output size override for the aligned map.
- `splat_size`: Splat kernel size (default 2 for a 2x2 splat).
- `z_far`: Optional clip distance. Defaults to `self.z_far` if not provided.

Notes:
- Create one `StereoInference` instance and reuse it for streaming to avoid
  reloading the TensorRT engine each frame.
- Call `ensure_loaded()` to force engine loading and shape detection early.
- Plan files are GPU model and TensorRT major-version specific.
- Use `set_calibration(intrinsics=..., extrinsics=...)` if camera calibration
  values change after initialization.
- Use `set_alignment(color_intrinsics=..., extrinsics_ir_to_color=...)` if RGB
  alignment parameters change after initialization.
- Make sure `intrinsics.width/height` match the raw input resolution before
  any resizing; the class scales to the inference resolution.

### 2.2 RealSense demo (camera quickstart)
This example connects to a RealSense camera and runs inference on the IR stereo
pair. It also compares the output with RealSense depth for visualization.

Install the dependency and run:
```bash
python -m pip install neuromeka_stereo[demo]
# or: python -m pip install opencv-python pyrealsense2
neuromeka-stereo-realsense \
  --trt_path foundation_stereo_480x640_RTX4060.plan \
  --width 640 --height 480 --fps 30 --z_far 10
```

If you are running from the repo:
```bash
python examples/run_realsense_demo.py \
  --trt_path foundation_stereo_480x640_RTX4060.plan \
  --width 640 --height 480 --fps 30 --z_far 10
```

Notes:
- Ensure the plan file exists in `src/neuromeka_stereo/assets/` or
  `~/.cache/neuromeka_stereo` before running.
- The plan input size is fixed; set `--width/--height` to match the plan.
- In the demo, `intrinsics` comes from the RealSense IR stream and is scaled
  internally to the inference resolution. `extrinsics` is IR1->IR2, and
  `z_far` comes from `--z_far` (default 10m).
- The display shows RGB, RS Depth, FS Depth (Raw), and FS Depth (Aligned).

## 3. Optional
### Rebuild plan from ONNX
If you also have an ONNX file on the new machine, build a fresh plan. Place the
ONNX file under `src/neuromeka_stereo/assets/onnx/` or adjust the path below.

Install `trtexec` (Ubuntu 22.04, CUDA 12.9 repo):
```bash
sudo apt-get install -y --allow-downgrades \
  libnvinfer-bin=10.14.1.48-1+cuda12.9 \
  libnvinfer10=10.14.1.48-1+cuda12.9 \
  libnvinfer-plugin10=10.14.1.48-1+cuda12.9 \
  libnvonnxparsers10=10.14.1.48-1+cuda12.9 \
  libnvinfer-lean10=10.14.1.48-1+cuda12.9 \
  libnvinfer-vc-plugin10=10.14.1.48-1+cuda12.9 \
  libnvinfer-dispatch10=10.14.1.48-1+cuda12.9
```

```bash
/usr/src/tensorrt/bin/trtexec \
  --onnx=./src/neuromeka_stereo/assets/onnx/foundation_stereo_23-51-11_640x480.onnx \
  --saveEngine=./src/neuromeka_stereo/assets/foundation_stereo_480x640_RTX4060.plan \
  --fp16 \
  --shapes=left:1x3x480x640,right:1x3x480x640 \
  --skipInference
```

### Local development setup (optional)
If you want to edit the package in-place or use the full dev stack:
```bash
python -m pip install -e .
```

```bash
cd /home/user/neuromeka-repo/nrmk_foundation_stereo
conda env create -f environment.yml
conda activate nrmk_fs
```

## Appendix: Folder layout
```
./
  src/
    neuromeka_stereo/
      fs_infer.py
      assets/
        (empty by default; place plan/onnx here)
      FoundationStereo_TRT/
        core/
        depth_anything_pretrained_models/
        Utils.py
  examples/
    run_realsense_demo.py
  pyproject.toml
  environment.yml
  README.md
```

## Appendix: Benchmark (D435 IR, 480x640)
Preliminary results; update for RTX 5060/5090 later.

| GPU | Backend | Input | Latency (sec) | Notes |
| --- | --- | --- | --- | --- |
| RTX 4060 | TensorRT plan | 480x640 | ~0.42 | TRT plan execution |
| RTX 5060 | TensorRT plan | 480x640 | ~0.30 | TRT plan execution |
| RTX 5090 | TensorRT plan | 480x640 | ~0.07 | TRT plan execution |
| RTX 4060 | Torch | 480x640 | ~1.12 | Torch inference |
