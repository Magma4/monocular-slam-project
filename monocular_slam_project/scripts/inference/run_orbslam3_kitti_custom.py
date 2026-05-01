#!/usr/bin/env python3
"""Run ORB-SLAM3 mono_kitti_old on existing custom extracted frames."""

import argparse
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ORB_SLAM3_ROOT = PROJECT_ROOT / "src" / "models" / "orb_slam3"

DEFAULT_FRAMES_ROOT = PROJECT_ROOT / "data" / "custom" / "extracted_frames"
DEFAULT_TRAJECTORY_ROOT = PROJECT_ROOT / "outputs" / "trajectories" / "orb_slam3"
DEFAULT_LOG_ROOT = PROJECT_ROOT / "outputs" / "logs" / "orb_slam3"
DEFAULT_BINARY = ORB_SLAM3_ROOT / "Examples_old" / "Monocular" / "mono_kitti_old"
DEFAULT_VOCABULARY = ORB_SLAM3_ROOT / "Vocabulary" / "ORBvoc.txt"
DEFAULT_SETTINGS = PROJECT_ROOT / "configs" / "orbslam3_custom_1280x720.yaml"
SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg"}


def natural_key(path):
    return [
        int(part) if part.isdigit() else part.lower()
        for part in re.split(r"(\d+)", path.name)
    ]


def resolve_frames_dir(sequence, frames):
    if frames:
        return Path(frames).expanduser().resolve()
    if sequence:
        return (DEFAULT_FRAMES_ROOT / sequence).resolve()
    raise ValueError("Provide either --sequence or --frames.")


def load_frame_paths(frames_dir):
    if not frames_dir.exists():
        raise FileNotFoundError(f"Frame folder does not exist: {frames_dir}")
    if not frames_dir.is_dir():
        raise ValueError(f"Frame path is not a folder: {frames_dir}")

    frame_paths = sorted(
        (
            path.resolve()
            for path in frames_dir.iterdir()
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
        ),
        key=natural_key,
    )

    if not frame_paths:
        raise ValueError(f"No supported image frames found in: {frames_dir}")

    return frame_paths


def validate_paths(binary, vocabulary, settings):
    missing = []
    for label, path in (
        ("ORB-SLAM3 mono_kitti_old binary", binary),
        ("ORB vocabulary", vocabulary),
        ("camera/settings YAML", settings),
    ):
        if not path.exists():
            missing.append(f"{label}: {path}")

    if missing:
        details = "\n".join(f"- {item}" for item in missing)
        raise FileNotFoundError(
            "Required ORB-SLAM3 file(s) are missing:\n"
            f"{details}\n\n"
            "Build ORB-SLAM3 first with:\n"
            "cd src/models/orb_slam3 && ./build.sh"
        )


def reset_generated_image_links(image_dir):
    image_dir.mkdir(parents=True, exist_ok=True)
    for path in image_dir.glob("*.png"):
        if path.is_symlink():
            path.unlink()
        else:
            raise FileExistsError(
                f"Refusing to overwrite non-symlink file in generated input folder: {path}"
            )


def prepare_kitti_sequence(frame_paths, sequence_root, fps):
    image_dir = sequence_root / "image_0"
    reset_generated_image_links(image_dir)

    for index, frame_path in enumerate(frame_paths):
        link_path = image_dir / f"{index:06d}.png"
        os.symlink(frame_path, link_path)

    times_path = sequence_root / "times.txt"
    with times_path.open("w", encoding="utf-8") as times_file:
        for index in range(len(frame_paths)):
            times_file.write(f"{index / fps:.6f}\n")

    return image_dir, times_path


def build_command(binary, vocabulary, settings, sequence_root, no_viewer):
    command = [str(binary), str(vocabulary), str(settings), str(sequence_root)]
    if no_viewer:
        command.append("--no-viewer")
    return command


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Run ORB-SLAM3 Examples_old/Monocular/mono_kitti_old on existing "
            "custom frames by creating a lightweight KITTI-style input folder."
        )
    )
    parser.add_argument(
        "--sequence",
        choices=["indoor_loop", "outdoor_loop", "outdoor_loop2"],
        help="Named sequence under data/custom/extracted_frames/.",
    )
    parser.add_argument(
        "--frames",
        help="Optional explicit folder containing extracted frames.",
    )
    parser.add_argument(
        "--fps",
        type=float,
        default=30.0,
        help="FPS used to synthesize KITTI-style timestamps. Default: 30.0",
    )
    parser.add_argument(
        "--settings",
        default=str(DEFAULT_SETTINGS),
        help=(
            "ORB-SLAM3 camera/settings YAML. Default uses "
            "configs/orbslam3_custom_1280x720.yaml for custom frames."
        ),
    )
    parser.add_argument(
        "--vocabulary",
        default=str(DEFAULT_VOCABULARY),
        help="Path to ORBvoc.txt.",
    )
    parser.add_argument(
        "--binary",
        default=str(DEFAULT_BINARY),
        help="Path to Examples_old/Monocular/mono_kitti_old.",
    )
    parser.add_argument(
        "--trajectory-root",
        default=str(DEFAULT_TRAJECTORY_ROOT),
        help="Root folder for trajectory outputs.",
    )
    parser.add_argument(
        "--log-root",
        default=str(DEFAULT_LOG_ROOT),
        help="Root folder for ORB-SLAM3 run logs.",
    )
    parser.add_argument(
        "--no-viewer",
        action="store_true",
        help="Run ORB-SLAM3 headless by disabling the Pangolin viewer window.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if args.fps <= 0:
        print("Error: --fps must be greater than zero.", file=sys.stderr)
        sys.exit(1)

    try:
        frames_dir = resolve_frames_dir(args.sequence, args.frames)
        frame_paths = load_frame_paths(frames_dir)
        sequence_name = args.sequence or frames_dir.name

        binary = Path(args.binary).expanduser().resolve()
        vocabulary = Path(args.vocabulary).expanduser().resolve()
        settings = Path(args.settings).expanduser().resolve()
        validate_paths(binary, vocabulary, settings)

        trajectory_dir = Path(args.trajectory_root).expanduser().resolve() / sequence_name
        log_dir = Path(args.log_root).expanduser().resolve()
        sequence_root = trajectory_dir / "kitti_input"
        trajectory_dir.mkdir(parents=True, exist_ok=True)
        log_dir.mkdir(parents=True, exist_ok=True)
        sequence_root.mkdir(parents=True, exist_ok=True)

        image_dir, times_path = prepare_kitti_sequence(frame_paths, sequence_root, args.fps)
        command = build_command(binary, vocabulary, settings, sequence_root, args.no_viewer)
        log_path = log_dir / f"{sequence_name}_mono_kitti_old.log"

        (trajectory_dir / "run_command.txt").write_text(
            shlex.join(command) + "\n",
            encoding="utf-8",
        )

        print(f"Sequence: {sequence_name}")
        print(f"Frames: {frames_dir}")
        print(f"Frame count: {len(frame_paths)}")
        print(f"KITTI-style image folder: {image_dir}")
        print(f"Timestamps: {times_path}")
        print(f"Trajectory output folder: {trajectory_dir}")
        print(f"Log file: {log_path}")
        print("Running ORB-SLAM3:")
        print(shlex.join(command))

        with log_path.open("w", encoding="utf-8") as log_file:
            log_file.write("Command:\n")
            log_file.write(shlex.join(command) + "\n\n")
            log_file.flush()
            subprocess.run(
                command,
                cwd=trajectory_dir,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                check=True,
            )

        raw_trajectory = trajectory_dir / "KeyFrameTrajectory.txt"
        final_trajectory = trajectory_dir / "keyframe_trajectory_tum.txt"
        if raw_trajectory.exists():
            raw_trajectory.replace(final_trajectory)
            print(f"Saved trajectory: {final_trajectory}")
        else:
            print(
                "Warning: ORB-SLAM3 finished, but KeyFrameTrajectory.txt was not found. "
                f"Check the log: {log_path}",
                file=sys.stderr,
            )

    except (FileNotFoundError, ValueError, FileExistsError, subprocess.CalledProcessError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
