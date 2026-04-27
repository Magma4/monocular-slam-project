#!/usr/bin/env python3
"""Extract ordered PNG frames from a .mov or .mp4 video."""

import argparse
import sys
from pathlib import Path

try:
    import cv2
except ImportError:
    print(
        "Error: OpenCV is not installed. Run `python -m pip install opencv-python`.",
        file=sys.stderr,
    )
    sys.exit(1)


SUPPORTED_EXTENSIONS = {".mov", ".mp4"}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract zero-padded PNG frames from a .mov or .mp4 video."
    )
    parser.add_argument("video_path", help="Path to the input .mov or .mp4 video.")
    parser.add_argument("output_folder", help="Folder where extracted PNG frames are saved.")
    return parser.parse_args()


def validate_video_path(video_path):
    if not video_path.exists():
        raise FileNotFoundError(f"Video file does not exist: {video_path}")
    if not video_path.is_file():
        raise ValueError(f"Video path is not a file: {video_path}")
    if video_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            "Unsupported video format. Please use a .mov or .mp4 file: "
            f"{video_path}"
        )


def extract_frames(video_path, output_folder):
    validate_video_path(video_path)
    output_folder.mkdir(parents=True, exist_ok=True)

    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise RuntimeError(
            "Could not open video with OpenCV. Check that the file is readable "
            f"and not corrupted: {video_path}"
        )

    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = capture.get(cv2.CAP_PROP_FPS)

    frame_count = 0
    while True:
        success, frame = capture.read()
        if not success:
            break

        frame_path = output_folder / f"frame_{frame_count:06d}.png"
        if not cv2.imwrite(str(frame_path), frame):
            capture.release()
            raise RuntimeError(f"Could not write frame to: {frame_path}")

        frame_count += 1

    capture.release()
    return frame_count, width, height, fps


def main():
    args = parse_args()
    video_path = Path(args.video_path).expanduser()
    output_folder = Path(args.output_folder).expanduser()

    try:
        frame_count, width, height, fps = extract_frames(video_path, output_folder)
    except (FileNotFoundError, ValueError, RuntimeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)

    print(f"Video: {video_path}")
    print(f"Output folder: {output_folder}")
    print(f"Total frames extracted: {frame_count}")
    print(f"Input resolution: {width}x{height}")
    if fps and fps > 0:
        print(f"FPS: {fps:.2f}")
    else:
        print("FPS: unavailable")


if __name__ == "__main__":
    main()
