# Copyright (c) 2025, NVIDIA CORPORATION.  All rights reserved.
#
# Demo: RealSense D435 streaming + FoundationStereo depth estimation.

import argparse
import time

try:
    import cv2
except ImportError as exc:
    raise SystemExit(
        "opencv-python is not installed. "
        "Install it with: python -m pip install neuromeka_stereo[demo]"
    ) from exc
import numpy as np

try:
    import pyrealsense2 as rs
except ImportError as exc:
    raise SystemExit(
        "pyrealsense2 is not installed. "
        "Install it with: python -m pip install neuromeka_stereo[demo]"
    ) from exc

from neuromeka_stereo import StereoInference
from neuromeka_stereo.assets import DEFAULT_ASSET_NAME


def colorize_depth(depth_m, max_depth):
    depth = np.nan_to_num(depth_m, nan=0.0, posinf=0.0, neginf=0.0)
    if max_depth is None or max_depth <= 0:
        valid = depth > 0
        max_depth = np.percentile(depth[valid], 95) if np.any(valid) else 1.0
    max_depth = max(max_depth, 1e-6)
    depth = np.clip(depth, 0.0, max_depth)
    depth_u8 = (depth / max_depth * 255.0).astype(np.uint8)
    return cv2.applyColorMap(depth_u8, cv2.COLORMAP_TURBO)


def annotate(img, label):
    cv2.putText(
        img,
        label,
        (12, 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    return img


def _resize_to(img, width, height, interpolation):
    if img.shape[:2] != (height, width):
        return cv2.resize(img, (width, height), interpolation=interpolation)
    return img


def _start_pipeline(pipeline, args):
    ctx = rs.context()
    if len(ctx.query_devices()) == 0:
        raise RuntimeError("No RealSense device detected. Check USB connection/permissions.")

    config = rs.config()
    config.enable_stream(rs.stream.color, args.width, args.height, rs.format.bgr8, args.fps)
    config.enable_stream(rs.stream.depth, args.width, args.height, rs.format.z16, args.fps)
    config.enable_stream(rs.stream.infrared, 1, args.width, args.height, rs.format.y8, args.fps)
    config.enable_stream(rs.stream.infrared, 2, args.width, args.height, rs.format.y8, args.fps)

    profile = pipeline.start(config)
    print(
        "Using streams:"
        f" color {args.width}x{args.height}@{args.fps},"
        f" depth {args.width}x{args.height}@{args.fps},"
        f" ir {args.width}x{args.height}@{args.fps}"
    )
    return profile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--width", type=int, default=848)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument(
        "--trt_path",
        default=None,
        type=str,
        help=(
            "TensorRT engine path (.plan/.engine). "
            f"If omitted, uses {DEFAULT_ASSET_NAME}."
        ),
    )
    parser.add_argument("--trt_width", type=int, default=0, help="TRT input width override")
    parser.add_argument("--trt_height", type=int, default=0, help="TRT input height override")
    parser.add_argument("--z_far", type=float, default=10.0, help="max depth clip (m)")
    parser.add_argument(
        "--align_depth",
        type=int,
        default=1,
        help="align RealSense depth to color for display",
    )
    parser.add_argument(
        "--display_scale",
        type=float,
        default=1.0,
        help="resize output window for display",
    )
    parser.add_argument(
        "--no_display",
        action="store_true",
        help="disable GUI display (headless mode)",
    )
    # Step 1: Parse CLI arguments.
    args = parser.parse_args()

    # Step 2: Initialize inference engine and resolve input shape.
    fs = StereoInference(
        args.trt_path,
        trt_width=args.trt_width,
        trt_height=args.trt_height,
        z_far=args.z_far,
    )
    if fs.input_shape is None:
        fs.ensure_loaded()
    if fs.input_shape:
        h, w = fs.input_shape
        if (args.trt_height, args.trt_width) != (h, w):
            print(f"Overriding TRT input size to {w}x{h} from TensorRT engine.")
        args.trt_height = h
        args.trt_width = w
    elif args.trt_height <= 0 or args.trt_width <= 0:
        raise ValueError("Missing --trt_width/--trt_height for dynamic TensorRT engines.")

    # Step 3: Start RealSense pipeline (color, depth, IR1/IR2).
    pipeline = rs.pipeline()
    profile = _start_pipeline(pipeline, args)
    align = rs.align(rs.stream.color) if args.align_depth else None

    # Step 4: Read camera calibration and set inference calibration.
    depth_sensor = profile.get_device().first_depth_sensor()
    depth_scale = depth_sensor.get_depth_scale()

    ir1_profile = profile.get_stream(rs.stream.infrared, 1).as_video_stream_profile()
    ir2_profile = profile.get_stream(rs.stream.infrared, 2).as_video_stream_profile()
    color_profile = profile.get_stream(rs.stream.color).as_video_stream_profile()
    ir_intr = ir1_profile.get_intrinsics()
    color_intr = color_profile.get_intrinsics()
    extr = ir1_profile.get_extrinsics_to(ir2_profile)
    ir_to_color = ir1_profile.get_extrinsics_to(color_profile)
    fs.set_calibration(intrinsics=ir_intr, extrinsics=extr)
    fs.set_alignment(color_intrinsics=color_intr, extrinsics_ir_to_color=ir_to_color)

    window_name = "RealSense RGB / RS Depth / FS Depth (Raw/Aligned)"
    use_display = not args.no_display
    last_time = time.time()
    frame_count = 0
    fps_text = "FPS: --"

    if use_display:
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    try:
        while True:
            # Step 5: Acquire frames.
            frames = pipeline.wait_for_frames()
            if align is not None:
                frames = align.process(frames)

            depth_frame = frames.get_depth_frame()
            color_frame = frames.get_color_frame()
            ir1_frame = frames.get_infrared_frame(1)
            ir2_frame = frames.get_infrared_frame(2)
            if not depth_frame or not color_frame or not ir1_frame or not ir2_frame:
                continue

            color = np.asanyarray(color_frame.get_data())
            depth_raw = np.asanyarray(depth_frame.get_data())
            ir1 = np.asanyarray(ir1_frame.get_data())
            ir2 = np.asanyarray(ir2_frame.get_data())

            # Step 6: Run inference once per frame.
            tic = time.time()
            depth_fs = fs.infer(ir1, ir2, return_depth=True)
            toc = time.time()
            print(f"Latency: {toc - tic} sec")

            # Step 7: Convert to displayable depth maps.
            depth_rs = depth_raw.astype(np.float32) * depth_scale

            fs_vis_raw = colorize_depth(depth_fs, args.z_far)
            rs_vis = colorize_depth(depth_rs, args.z_far)

            depth_fs_aligned = fs.align_depth_splat(
                depth_fs,
                out_size=(color.shape[0], color.shape[1]),
                splat_size=2,
                z_far=args.z_far,
            )
            fs_vis_aligned = colorize_depth(depth_fs_aligned, args.z_far)

            # Step 8: Compose view.
            target_w, target_h = color.shape[1], color.shape[0]
            color = _resize_to(color, target_w, target_h, cv2.INTER_AREA)
            rs_vis = _resize_to(rs_vis, target_w, target_h, cv2.INTER_NEAREST)
            fs_vis_raw = _resize_to(fs_vis_raw, target_w, target_h, cv2.INTER_NEAREST)
            fs_vis_aligned = _resize_to(fs_vis_aligned, target_w, target_h, cv2.INTER_NEAREST)

            annotate(color, "RGB")
            annotate(rs_vis, "RS Depth")
            annotate(fs_vis_raw, "FS Depth (Raw)")
            annotate(fs_vis_aligned, "FS Depth (Aligned)")

            top_row = np.hstack([color, rs_vis])
            bottom_row = np.hstack([fs_vis_raw, fs_vis_aligned])
            stacked = np.vstack([top_row, bottom_row])
            if args.display_scale != 1.0:
                stacked = cv2.resize(
                    stacked,
                    None,
                    fx=args.display_scale,
                    fy=args.display_scale,
                    interpolation=cv2.INTER_AREA,
                )

            frame_count += 1
            now = time.time()
            if now - last_time >= 1.0:
                fps_text = f"FPS: {frame_count / (now - last_time):.1f}"
                frame_count = 0
                last_time = now
            cv2.putText(
                stacked,
                fps_text,
                (12, stacked.shape[0] - 12),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )

            if use_display:
                # Step 9: Show window and handle quit.
                cv2.imshow(window_name, stacked)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q") or key == 27:
                    break
    finally:
        pipeline.stop()
        if use_display:
            cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
