#!/usr/bin/env python3
"""Inspect a downloaded KITTI odometry folder and explain the DeepVO target layout."""

import argparse
from pathlib import Path


DEFAULT_SEQUENCES = [f"{index:02d}" for index in range(11)]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Inspect KITTI odometry files before placing them for DeepVO."
    )
    parser.add_argument(
        "downloaded_kitti_folder",
        help="Folder containing downloaded/extracted KITTI odometry files.",
    )
    parser.add_argument(
        "--target",
        default="data/benchmark/kitti",
        help="Target KITTI root expected by DeepVO. Default: data/benchmark/kitti",
    )
    parser.add_argument(
        "--sequences",
        nargs="+",
        default=DEFAULT_SEQUENCES,
        help="Sequence IDs to inspect. Default: 00 01 ... 10",
    )
    parser.add_argument(
        "--image-folder",
        default="image_0",
        help="KITTI camera folder to inspect. Default: image_0",
    )
    return parser.parse_args()


def print_target_layout(target_root, sequences, image_folder):
    print("Expected DeepVO target layout")
    print(f"{target_root}/")
    print("  poses/")
    for sequence in sequences[:3]:
        print(f"    {sequence}.txt")
    if len(sequences) > 3:
        print("    ...")
    print("  sequences/")
    for sequence in sequences[:3]:
        print(f"    {sequence}/")
        print(f"      {image_folder}/")
        print("        000000.png")
        print("        000001.png")
        print("        ...")
    if len(sequences) > 3:
        print("    ...")
    print()


def find_pose_file(root, sequence):
    candidates = [
        root / "poses" / f"{sequence}.txt",
        root / "dataset" / "poses" / f"{sequence}.txt",
    ]
    candidates.extend(root.rglob(f"poses/{sequence}.txt"))
    return first_existing_file(candidates)


def find_image_folder(root, sequence, image_folder):
    candidates = [
        root / "sequences" / sequence / image_folder,
        root / "dataset" / "sequences" / sequence / image_folder,
    ]
    candidates.extend(root.rglob(f"sequences/{sequence}/{image_folder}"))
    return first_existing_dir(candidates)


def first_existing_file(paths):
    seen = set()
    for path in paths:
        if path in seen:
            continue
        seen.add(path)
        if path.exists() and path.is_file():
            return path
    return None


def first_existing_dir(paths):
    seen = set()
    for path in paths:
        if path in seen:
            continue
        seen.add(path)
        if path.exists() and path.is_dir():
            return path
    return None


def count_pngs(folder):
    if folder is None:
        return 0
    return sum(1 for path in folder.iterdir() if path.is_file() and path.suffix.lower() == ".png")


def main():
    args = parse_args()
    source_root = Path(args.downloaded_kitti_folder).expanduser()
    target_root = Path(args.target).expanduser()

    print(f"Downloaded KITTI folder inspected: {source_root}")
    print(f"DeepVO target folder: {target_root}")
    print()
    print_target_layout(target_root, args.sequences, args.image_folder)

    if not source_root.exists() or not source_root.is_dir():
        print(f"[MISSING] Downloaded folder does not exist or is not a directory: {source_root}")
        return

    print("Inspection results")
    complete_sequences = 0
    for sequence in args.sequences:
        pose_file = find_pose_file(source_root, sequence)
        image_folder_path = find_image_folder(source_root, sequence, args.image_folder)
        image_count = count_pngs(image_folder_path)

        target_pose = target_root / "poses" / f"{sequence}.txt"
        target_images = target_root / "sequences" / sequence / args.image_folder

        pose_ok = pose_file is not None
        images_ok = image_folder_path is not None and image_count > 0
        if pose_ok and images_ok:
            complete_sequences += 1

        print(f"Sequence {sequence}")
        if pose_ok:
            print(f"  [FOUND] pose file: {pose_file}")
            if pose_file != target_pose:
                print(f"          target should be: {target_pose}")
        else:
            print(f"  [MISSING] pose file for target: {target_pose}")

        if images_ok:
            print(f"  [FOUND] {args.image_folder} folder: {image_folder_path}")
            print(f"          png frames found: {image_count}")
            if image_folder_path != target_images:
                print(f"          target should be: {target_images}")
        else:
            print(f"  [MISSING] {args.image_folder} folder for target: {target_images}")
        print()

    print("Summary")
    print(f"Sequences inspected: {len(args.sequences)}")
    print(f"Sequences with both poses and {args.image_folder} frames: {complete_sequences}")
    print()
    print("This script only inspects and reports. It does not download, move, or rename files.")
    print("After arranging files, run:")
    print("  python scripts/preprocessing/check_kitti_layout.py")


if __name__ == "__main__":
    main()
