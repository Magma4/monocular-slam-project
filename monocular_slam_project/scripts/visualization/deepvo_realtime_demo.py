#!/usr/bin/env python3
"""Pseudo-real-time DeepVO demo using saved frames and predicted trajectory CSV."""

import argparse
import csv
import os
import re
import sys
import time
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FRAMES_DIR = PROJECT_ROOT / "data" / "custom" / "extracted_frames" / "indoor_loop"
DEFAULT_TRAJECTORY = (
    PROJECT_ROOT
    / "outputs"
    / "trajectories"
    / "deepvo"
    / "custom_trained"
    / "indoor_loop"
    / "predicted_trajectory.csv"
)
SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg"}


def natural_key(path):
    return [
        int(part) if part.isdigit() else part.lower()
        for part in re.split(r"(\d+)", path.name)
    ]


def load_frames(frames_dir):
    if not frames_dir.exists():
        raise FileNotFoundError(f"Frame folder does not exist: {frames_dir}")
    frames = sorted(
        (
            path
            for path in frames_dir.iterdir()
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
        ),
        key=natural_key,
    )
    if not frames:
        raise ValueError(f"No supported frame images found in: {frames_dir}")
    return frames


def load_deepvo_trajectory(csv_path):
    if not csv_path.exists():
        raise FileNotFoundError(f"Trajectory CSV does not exist: {csv_path}")
    if not csv_path.is_file():
        raise ValueError(f"Trajectory path is not a file: {csv_path}")

    rows = []
    with csv_path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        required = {"x", "z"}
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            raise ValueError("DeepVO trajectory CSV must contain at least x and z columns.")
        for index, row in enumerate(reader, start=2):
            try:
                rows.append({
                    "frame": row.get("frame", ""),
                    "x": float(row["x"]),
                    "z": float(row["z"]),
                })
            except ValueError as error:
                raise ValueError(f"Invalid numeric trajectory value at CSV line {index}.") from error

    if not rows:
        raise ValueError(f"Trajectory CSV has no rows: {csv_path}")
    return rows


def resize_keep_aspect(image, target_width):
    import cv2

    if image.shape[1] <= target_width:
        return image
    scale = target_width / image.shape[1]
    target_height = int(image.shape[0] * scale)
    return cv2.resize(image, (target_width, target_height), interpolation=cv2.INTER_AREA)


def add_status_overlay(frame, frame_index, total_frames, visible_points, total_points, fps):
    import cv2

    overlay = frame.copy()
    lines = [
        "DeepVO monocular visual odometry demo",
        f"Frame: {frame_index + 1}/{total_frames}",
        f"Trajectory points shown: {visible_points}/{total_points}",
        f"Replay FPS: {fps:g} | Press q or Esc to quit",
    ]

    padding = 12
    line_height = 28
    box_height = padding * 2 + line_height * len(lines)
    cv2.rectangle(overlay, (0, 0), (frame.shape[1], box_height), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)

    for i, text in enumerate(lines):
        y = padding + 20 + i * line_height
        cv2.putText(
            frame,
            text,
            (padding, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
    return frame


def trajectory_axes_limits(trajectory):
    x_values = [row["x"] for row in trajectory]
    z_values = [row["z"] for row in trajectory]
    x_min, x_max = min(x_values), max(x_values)
    z_min, z_max = min(z_values), max(z_values)
    margin = max(x_max - x_min, z_max - z_min, 1e-3) * 0.15
    return (x_min - margin, x_max + margin), (z_min - margin, z_max + margin)


def render_trajectory_plot(trajectory, visible_count, size, axes_limits):
    import cv2
    import numpy as np
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    width, height = size
    figure = Figure(figsize=(width / 100, height / 100), dpi=100)
    canvas = FigureCanvasAgg(figure)
    axis = figure.add_subplot(111)

    x_limits, z_limits = axes_limits
    axis.set_xlim(*x_limits)
    axis.set_ylim(*z_limits)
    axis.set_aspect("equal", adjustable="box")
    axis.grid(True, alpha=0.3)
    axis.set_title("DeepVO predicted trajectory")
    axis.set_xlabel("x translation")
    axis.set_ylabel("z translation")

    all_x = [row["x"] for row in trajectory]
    all_z = [row["z"] for row in trajectory]
    axis.plot(all_x, all_z, color="0.82", linewidth=1.0, label="full saved path")

    if visible_count > 0:
        visible = trajectory[:visible_count]
        x_values = [row["x"] for row in visible]
        z_values = [row["z"] for row in visible]
        axis.plot(x_values, z_values, color="#ff7f0e", linewidth=2.2, label="revealed path")
        axis.scatter(x_values[0], z_values[0], color="#2ca02c", s=35, label="start")
        axis.scatter(x_values[-1], z_values[-1], color="#d62728", s=35, label="current")

    axis.legend(loc="upper right", fontsize=8)
    figure.tight_layout()
    canvas.draw()

    rgba = np.asarray(canvas.buffer_rgba())
    return cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGR)


def combine_frame_and_plot(frame, plot_image):
    import cv2

    target_height = min(frame.shape[0], plot_image.shape[0])
    frame_width = int(frame.shape[1] * target_height / frame.shape[0])
    plot_width = int(plot_image.shape[1] * target_height / plot_image.shape[0])
    frame_resized = cv2.resize(frame, (frame_width, target_height), interpolation=cv2.INTER_AREA)
    plot_resized = cv2.resize(plot_image, (plot_width, target_height), interpolation=cv2.INTER_AREA)
    return cv2.hconcat([frame_resized, plot_resized])


def visible_trajectory_count(frame_index, total_frames, total_points):
    progress = min(max((frame_index + 1) / total_frames, 0.0), 1.0)
    return min(total_points, max(1, int(round(progress * total_points))))


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Replay extracted frames with an updating DeepVO predicted trajectory. "
            "This is a pseudo-real-time visualization using saved inference output."
        )
    )
    parser.add_argument(
        "--frames",
        default=str(DEFAULT_FRAMES_DIR),
        help="Folder containing extracted frame images. Default: indoor_loop frames.",
    )
    parser.add_argument(
        "--trajectory",
        default=str(DEFAULT_TRAJECTORY),
        help="DeepVO predicted trajectory CSV. Default: custom trained indoor_loop result.",
    )
    parser.add_argument("--fps", type=float, default=30.0, help="Replay FPS. Default: 30.")
    parser.add_argument(
        "--stride",
        type=int,
        default=1,
        help="Display every Nth frame for faster playback. Default: 1.",
    )
    parser.add_argument(
        "--max-frame-width",
        type=int,
        default=720,
        help="Resize displayed video frame to this maximum width. Default: 720.",
    )
    parser.add_argument(
        "--plot-width",
        type=int,
        default=720,
        help="Rendered trajectory plot width in pixels. Default: 720.",
    )
    parser.add_argument(
        "--plot-height",
        type=int,
        default=720,
        help="Rendered trajectory plot height in pixels. Default: 720.",
    )
    parser.add_argument(
        "--plot-update-stride",
        type=int,
        default=5,
        help="Re-render the trajectory plot every N displayed frames. Default: 5.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    try:
        cache_root = Path(tempfile.gettempdir()) / "monocular_slam_matplotlib"
        os.environ.setdefault("MPLCONFIGDIR", str(cache_root / "config"))
        os.environ.setdefault("XDG_CACHE_HOME", str(cache_root / "cache"))
        import cv2
        import matplotlib

        matplotlib.use("Agg")
    except ImportError as error:
        missing = "OpenCV" if error.name == "cv2" else "matplotlib"
        print(
            f"Error: {missing} is not installed. Run `python -m pip install -r requirements.txt`.",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.fps <= 0:
        print("Error: --fps must be greater than zero.", file=sys.stderr)
        sys.exit(1)
    if args.stride <= 0 or args.plot_update_stride <= 0:
        print("Error: --stride and --plot-update-stride must be greater than zero.", file=sys.stderr)
        sys.exit(1)

    frames_dir = Path(args.frames).expanduser().resolve()
    trajectory_path = Path(args.trajectory).expanduser().resolve()

    try:
        frames = load_frames(frames_dir)
        trajectory = load_deepvo_trajectory(trajectory_path)
    except (FileNotFoundError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)

    axes_limits = trajectory_axes_limits(trajectory)
    window_name = "DeepVO pseudo-real-time demo"
    delay_seconds = 1.0 / args.fps
    cached_plot = None
    cached_visible_count = -1

    print(f"Frames: {frames_dir}")
    print(f"Frame count: {len(frames)}")
    print(f"Trajectory: {trajectory_path}")
    print(f"Trajectory points: {len(trajectory)}")
    print("Press q or Esc in the demo window to quit.")

    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    displayed_index = 0
    for frame_index in range(0, len(frames), args.stride):
        start_time = time.time()
        frame = cv2.imread(str(frames[frame_index]), cv2.IMREAD_COLOR)
        if frame is None:
            print(f"Warning: could not read frame: {frames[frame_index]}", file=sys.stderr)
            continue

        frame = resize_keep_aspect(frame, args.max_frame_width)
        visible_count = visible_trajectory_count(frame_index, len(frames), len(trajectory))
        frame = add_status_overlay(
            frame,
            frame_index,
            len(frames),
            visible_count,
            len(trajectory),
            args.fps,
        )

        should_update_plot = (
            cached_plot is None
            or displayed_index % args.plot_update_stride == 0
            or visible_count != cached_visible_count
        )
        if should_update_plot:
            cached_plot = render_trajectory_plot(
                trajectory,
                visible_count,
                (args.plot_width, args.plot_height),
                axes_limits,
            )
            cached_visible_count = visible_count

        demo_image = combine_frame_and_plot(frame, cached_plot)
        cv2.imshow(window_name, demo_image)

        elapsed = time.time() - start_time
        wait_ms = max(1, int((delay_seconds - elapsed) * 1000))
        key = cv2.waitKey(wait_ms) & 0xFF
        if key in (ord("q"), 27):
            break
        displayed_index += 1

    cv2.destroyAllWindows()
    print("Demo finished.")


if __name__ == "__main__":
    main()
