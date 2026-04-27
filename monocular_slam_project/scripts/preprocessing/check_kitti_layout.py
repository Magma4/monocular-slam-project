#!/usr/bin/env python3
"""Check that a KITTI odometry folder matches the layout expected by DeepVO."""

import argparse
from pathlib import Path


DEFAULT_SEQUENCES = [f"{index:02d}" for index in range(11)]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Validate KITTI odometry folders for the DeepVO dataset loader."
    )
    parser.add_argument(
        "kitti_root",
        nargs="?",
        default="data/benchmark/kitti",
        help="KITTI odometry root folder. Default: data/benchmark/kitti",
    )
    parser.add_argument(
        "--sequences",
        nargs="+",
        default=DEFAULT_SEQUENCES,
        help="Sequence IDs to check. Default: 00 01 ... 10",
    )
    parser.add_argument(
        "--image-folder",
        default="image_0",
        help="KITTI camera folder to check. Default: image_0",
    )
    return parser.parse_args()


def status_line(ok, label, path):
    marker = "OK" if ok else "MISSING"
    print(f"[{marker}] {label}: {path}")


def main():
    args = parse_args()
    kitti_root = Path(args.kitti_root).expanduser()
    poses_dir = kitti_root / "poses"
    sequences_dir = kitti_root / "sequences"

    print(f"Checking KITTI root: {kitti_root}")
    print()

    root_ok = kitti_root.exists() and kitti_root.is_dir()
    poses_ok = poses_dir.exists() and poses_dir.is_dir()
    sequences_ok = sequences_dir.exists() and sequences_dir.is_dir()

    status_line(root_ok, "KITTI root", kitti_root)
    status_line(poses_ok, "poses folder", poses_dir)
    status_line(sequences_ok, "sequences folder", sequences_dir)
    print()

    missing_items = []
    present_sequences = 0

    for sequence in args.sequences:
        sequence_dir = sequences_dir / sequence
        image_dir = sequence_dir / args.image_folder
        pose_file = poses_dir / f"{sequence}.txt"

        image_ok = image_dir.exists() and image_dir.is_dir()
        pose_ok = pose_file.exists() and pose_file.is_file()

        if image_ok and pose_ok:
            present_sequences += 1

        if not image_ok:
            missing_items.append(str(image_dir))
        if not pose_ok:
            missing_items.append(str(pose_file))

        print(f"Sequence {sequence}")
        status_line(image_ok, f"{args.image_folder} folder", image_dir)
        status_line(pose_ok, "pose file", pose_file)
        print()

    print("Summary")
    print(f"Sequences checked: {len(args.sequences)}")
    print(f"Sequences with both {args.image_folder}/ and pose file: {present_sequences}")
    print(f"Missing items: {len(missing_items)}")

    if missing_items:
        print()
        print("Missing paths:")
        for item in missing_items:
            print(f"- {item}")
    else:
        print("KITTI layout looks ready for the DeepVO loader.")


if __name__ == "__main__":
    main()
