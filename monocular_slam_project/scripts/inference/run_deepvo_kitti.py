#!/usr/bin/env python3
"""Run DeepVO inference on one KITTI odometry sequence."""

import argparse
import csv
import math
import sys
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torchvision import transforms

try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEEPVO_ROOT = PROJECT_ROOT / "src" / "models" / "deepvo"
sys.path.insert(0, str(DEEPVO_ROOT))

from deepvonet import DeepVONet  # noqa: E402


def get_device():
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def build_preprocess():
    normalize = transforms.Normalize(
        mean=[127.0 / 255.0, 127.0 / 255.0, 127.0 / 255.0],
        std=[1.0 / 255.0, 1.0 / 255.0, 1.0 / 255.0],
    )
    return transforms.Compose(
        [
            transforms.Resize((384, 1280)),
            transforms.CenterCrop((384, 1280)),
            transforms.ToTensor(),
            normalize,
        ]
    )


def load_model(checkpoint_path, device):
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Checkpoint does not exist: {checkpoint_path}")

    model = DeepVONet().to(device)
    checkpoint = torch.load(checkpoint_path, map_location=device)
    state_dict = checkpoint.get("state_dict", checkpoint)
    model.load_state_dict(state_dict)
    model.eval()
    return model


def load_frame_paths(kitti_root, sequence, image_folder):
    image_dir = kitti_root / "sequences" / sequence / image_folder
    if not image_dir.exists():
        raise FileNotFoundError(f"Image folder does not exist: {image_dir}")

    frame_paths = sorted(image_dir.glob("*.png"))
    if len(frame_paths) < 2:
        raise ValueError(f"Need at least two PNG frames in: {image_dir}")
    return image_dir, frame_paths


def rotation_matrix_to_euler_angles(rotation):
    sy = math.sqrt(rotation[0, 0] * rotation[0, 0] + rotation[1, 0] * rotation[1, 0])
    singular = sy < 1e-6

    if not singular:
        x = math.atan2(rotation[2, 1], rotation[2, 2])
        y = math.atan2(-rotation[2, 0], sy)
        z = math.atan2(rotation[1, 0], rotation[0, 0])
    else:
        x = math.atan2(-rotation[1, 2], rotation[1, 1])
        y = math.atan2(-rotation[2, 0], sy)
        z = 0

    return np.array([x, y, z], dtype=np.float32)


def load_ground_truth(kitti_root, sequence):
    pose_path = kitti_root / "poses" / f"{sequence}.txt"
    if not pose_path.exists():
        return None

    rows = []
    with pose_path.open() as pose_file:
        for index, line in enumerate(pose_file):
            values = np.array([float(value) for value in line.split()], dtype=np.float32)
            rotation = np.array(
                [
                    [values[0], values[1], values[2]],
                    [values[4], values[5], values[6]],
                    [values[8], values[9], values[10]],
                ],
                dtype=np.float32,
            )
            angles = rotation_matrix_to_euler_angles(rotation)
            rows.append(
                [
                    f"{index:06d}.png",
                    float(values[3]),
                    float(values[7]),
                    float(values[11]),
                    *angles.astype(float).tolist(),
                ]
            )
    return rows


def predict_pair(model, preprocess, frame_a, frame_b, device, reset_state):
    image_a = preprocess(Image.open(frame_a).convert("RGB"))
    image_b = preprocess(Image.open(frame_b).convert("RGB"))
    stacked = torch.cat([image_a, image_b], dim=0).unsqueeze(0)
    stacked = stacked.to(device, dtype=torch.float32)

    with torch.no_grad():
        model.reset_hidden_states(size=1, zero=reset_state)
        prediction = model(stacked)

    return prediction.squeeze(0).detach().cpu().numpy()


def write_csv(path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(header)
        writer.writerows(rows)


def write_outputs(output_dir, sequence, frame_paths, predictions, ground_truth_rows):
    relative_rows = []
    trajectory_rows = []
    cumulative = np.zeros(6, dtype=np.float32)

    trajectory_rows.append([frame_paths[0].name, *cumulative.astype(float).tolist()])
    for index, prediction in enumerate(predictions):
        relative_rows.append(
            [
                frame_paths[index].name,
                frame_paths[index + 1].name,
                *prediction.astype(float).tolist(),
            ]
        )
        cumulative += prediction.astype(np.float32)
        trajectory_rows.append([frame_paths[index + 1].name, *cumulative.astype(float).tolist()])

    relative_path = output_dir / "predicted_relative_poses.csv"
    trajectory_path = output_dir / "predicted_trajectory.csv"
    write_csv(relative_path, ["frame_a", "frame_b", "tx", "ty", "tz", "rx", "ry", "rz"], relative_rows)
    write_csv(trajectory_path, ["frame", "x", "y", "z", "rx", "ry", "rz"], trajectory_rows)

    ground_truth_path = None
    if ground_truth_rows:
        ground_truth_path = output_dir / "ground_truth_trajectory.csv"
        write_csv(ground_truth_path, ["frame", "x", "y", "z", "rx", "ry", "rz"], ground_truth_rows)

    return relative_path, trajectory_path, ground_truth_path


def plot_trajectory(plot_path, sequence, trajectory_rows, ground_truth_rows):
    if plt is None:
        print("Warning: matplotlib is not installed; skipping plot.")
        return None

    plot_path.parent.mkdir(parents=True, exist_ok=True)

    pred = np.array([[row[1], row[3]] for row in trajectory_rows], dtype=np.float32)
    plt.figure(figsize=(8, 6))
    plt.plot(pred[:, 0], pred[:, 1], label="DeepVO prediction", linewidth=1.8)
    plt.scatter(pred[0, 0], pred[0, 1], label="start", s=35)
    plt.scatter(pred[-1, 0], pred[-1, 1], label="end", s=35)

    if ground_truth_rows:
        truth = np.array([[row[1], row[3]] for row in ground_truth_rows], dtype=np.float32)
        plt.plot(truth[:, 0], truth[:, 1], label="KITTI ground truth", linewidth=1.2, alpha=0.8)

    plt.xlabel("x")
    plt.ylabel("z")
    plt.title(f"DeepVO KITTI sequence {sequence}")
    plt.axis("equal")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(plot_path, dpi=200)
    plt.close()
    return plot_path


def parse_args():
    parser = argparse.ArgumentParser(description="Run DeepVO inference on one KITTI sequence.")
    parser.add_argument("--kitti-root", default="data/benchmark/kitti", help="KITTI odometry root.")
    parser.add_argument("--sequence", required=True, help="KITTI sequence ID, e.g. 04.")
    parser.add_argument("--checkpoint", required=True, help="DeepVO checkpoint path.")
    parser.add_argument("--image-folder", default="image_0", help="KITTI camera folder. Default: image_0")
    parser.add_argument(
        "--output-root",
        default="outputs/trajectories/deepvo_kitti",
        help="Root folder for trajectory CSV outputs.",
    )
    parser.add_argument(
        "--plot-root",
        default="outputs/plots",
        help="Folder for trajectory plot PNG outputs.",
    )
    parser.add_argument(
        "--max-pairs",
        type=int,
        default=None,
        help="Optional limit for quick smoke tests.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    kitti_root = Path(args.kitti_root).expanduser()
    checkpoint_path = Path(args.checkpoint).expanduser()
    output_dir = Path(args.output_root).expanduser() / args.sequence
    plot_path = Path(args.plot_root).expanduser() / f"deepvo_kitti_{args.sequence}_trajectory.png"

    try:
        image_dir, frame_paths = load_frame_paths(kitti_root, args.sequence, args.image_folder)
        if args.max_pairs is not None:
            frame_paths = frame_paths[: args.max_pairs + 1]
        device = get_device()
        preprocess = build_preprocess()
        model = load_model(checkpoint_path, device)
        ground_truth_rows = load_ground_truth(kitti_root, args.sequence)
    except (FileNotFoundError, ValueError, RuntimeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)

    print(f"Using device: {device}")
    print(f"KITTI image folder: {image_dir}")
    print(f"Sequence: {args.sequence}")
    print(f"Frames used: {len(frame_paths)}")
    print(f"Checkpoint: {checkpoint_path}")

    predictions = []
    for index in range(len(frame_paths) - 1):
        predictions.append(
            predict_pair(
                model,
                preprocess,
                frame_paths[index],
                frame_paths[index + 1],
                device,
                reset_state=index == 0,
            )
        )

    relative_path, trajectory_path, ground_truth_path = write_outputs(
        output_dir, args.sequence, frame_paths, predictions, ground_truth_rows
    )
    trajectory_rows = []
    with trajectory_path.open(newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            trajectory_rows.append(
                [
                    row["frame"],
                    float(row["x"]),
                    float(row["y"]),
                    float(row["z"]),
                    float(row["rx"]),
                    float(row["ry"]),
                    float(row["rz"]),
                ]
            )

    saved_plot = plot_trajectory(plot_path, args.sequence, trajectory_rows, ground_truth_rows)

    print(f"Saved relative poses: {relative_path}")
    print(f"Saved predicted trajectory: {trajectory_path}")
    if ground_truth_path:
        print(f"Saved ground truth trajectory: {ground_truth_path}")
    if saved_plot:
        print(f"Saved plot: {saved_plot}")
    print(f"Predicted frame pairs: {len(predictions)}")


if __name__ == "__main__":
    main()
