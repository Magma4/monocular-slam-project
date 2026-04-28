#!/usr/bin/env python3
"""Run ORB-SLAM3 monocular on existing extracted custom video frames."""

import argparse
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ORB_SLAM3_ROOT = PROJECT_ROOT / "src" / "models" / "orb_slam3"

DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "trajectories" / "orb_slam3" / "custom"
DEFAULT_VOCABULARY = ORB_SLAM3_ROOT / "Vocabulary" / "ORBvoc.txt"
DEFAULT_SETTINGS = ORB_SLAM3_ROOT / "Examples" / "Monocular" / "TUM1.yaml"
DEFAULT_BINARY = ORB_SLAM3_ROOT / "Examples" / "Monocular" / "mono_tum"
DEFAULT_CUSTOM_FRAMES = PROJECT_ROOT / "data" / "custom" / "extracted_frames"

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
        return (DEFAULT_CUSTOM_FRAMES / sequence).resolve()
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


def validate_orbslam3_paths(binary, vocabulary, settings):
    missing = []
    for label, path in (
        ("ORB-SLAM3 monocular binary", binary),
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


def write_rgb_manifest(frame_paths, input_root, fps):
    input_root.mkdir(parents=True, exist_ok=True)
    manifest_path = input_root / "rgb.txt"

    with manifest_path.open("w", encoding="utf-8") as manifest:
        manifest.write("# TUM-style image list generated for ORB-SLAM3 custom frames\n")
        manifest.write("# timestamp filename\n")
        manifest.write("# Generated from existing extracted frame sequence\n")

        for index, frame_path in enumerate(frame_paths):
            timestamp = index / fps
            relative_frame = os.path.relpath(frame_path, start=input_root)
            manifest.write(f"{timestamp:.6f} {relative_frame}\n")

    return manifest_path


def build_command(binary, vocabulary, settings, input_root):
    return [
        str(binary),
        str(vocabulary),
        str(settings),
        str(input_root),
    ]


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Run ORB-SLAM3 monocular using an existing folder of extracted frames. "
            "The script generates a TUM-style rgb.txt manifest and does not copy frames."
        )
    )
    parser.add_argument(
        "--sequence",
        choices=["indoor_loop", "outdoor_loop"],
        help="Named custom sequence under data/custom/extracted_frames/.",
    )
    parser.add_argument(
        "--frames",
        help="Optional explicit folder containing extracted frames.",
    )
    parser.add_argument(
        "--output",
        help="Output folder. Defaults to outputs/trajectories/orb_slam3/custom/<sequence>.",
    )
    parser.add_argument(
        "--fps",
        type=float,
        default=30.0,
        help="Frame rate used to synthesize timestamps for ORB-SLAM3. Default: 30.0",
    )
    parser.add_argument(
        "--settings",
        default=str(DEFAULT_SETTINGS),
        help=(
            "ORB-SLAM3 monocular camera/settings YAML. "
            "Default uses the bundled TUM1.yaml as a smoke-test placeholder."
        ),
    )
    parser.add_argument(
        "--vocabulary",
        default=str(DEFAULT_VOCABULARY),
        help="Path to ORBvoc.txt. Default: src/models/orb_slam3/Vocabulary/ORBvoc.txt",
    )
    parser.add_argument(
        "--binary",
        default=str(DEFAULT_BINARY),
        help="Path to the built ORB-SLAM3 mono_tum binary.",
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
        output_dir = (
            Path(args.output).expanduser().resolve()
            if args.output
            else (DEFAULT_OUTPUT_ROOT / sequence_name).resolve()
        )
        input_root = output_dir / "orb_input"

        binary = Path(args.binary).expanduser().resolve()
        vocabulary = Path(args.vocabulary).expanduser().resolve()
        settings = Path(args.settings).expanduser().resolve()
        validate_orbslam3_paths(binary, vocabulary, settings)

        output_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = write_rgb_manifest(frame_paths, input_root, args.fps)
        command = build_command(binary, vocabulary, settings, input_root)

        (output_dir / "run_command.txt").write_text(
            shlex.join(command) + "\n",
            encoding="utf-8",
        )

        print(f"Sequence: {sequence_name}")
        print(f"Frames: {frames_dir}")
        print(f"Frame count: {len(frame_paths)}")
        print(f"FPS for timestamps: {args.fps}")
        print(f"Manifest: {manifest_path}")
        print(f"Output folder: {output_dir}")
        print("Running ORB-SLAM3:")
        print(shlex.join(command))

        subprocess.run(command, cwd=output_dir, check=True)

        raw_trajectory = output_dir / "KeyFrameTrajectory.txt"
        final_trajectory = output_dir / "keyframe_trajectory_tum.txt"
        if raw_trajectory.exists():
            raw_trajectory.replace(final_trajectory)
            print(f"Saved trajectory: {final_trajectory}")
        else:
            print(
                "Warning: ORB-SLAM3 finished, but KeyFrameTrajectory.txt was not found.",
                file=sys.stderr,
            )

    except (FileNotFoundError, ValueError, subprocess.CalledProcessError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
