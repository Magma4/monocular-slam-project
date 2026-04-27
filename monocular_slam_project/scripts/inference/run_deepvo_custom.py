#!/usr/bin/env python3
"""Run DeepVO inference on a folder of extracted custom video frames."""

import argparse
import csv
import sys
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torchvision import transforms


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEEPVO_ROOT = PROJECT_ROOT / "src" / "models" / "deepvo"
sys.path.insert(0, str(DEEPVO_ROOT))

from deepvonet import DeepVONet  # noqa: E402


SUPPORTED_FRAME_EXTENSIONS = {".png", ".jpg", ".jpeg"}


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


def load_frame_paths(frames_dir):
    if not frames_dir.exists():
        raise FileNotFoundError(f"Frame folder does not exist: {frames_dir}")
    if not frames_dir.is_dir():
        raise ValueError(f"Frame path is not a folder: {frames_dir}")

    frame_paths = sorted(
        path
        for path in frames_dir.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_FRAME_EXTENSIONS
    )
    if len(frame_paths) < 2:
        raise ValueError(
            "At least two frames are required for DeepVO inference. "
            f"Found {len(frame_paths)} in {frames_dir}"
        )
    return frame_paths


def load_model(checkpoint_path, device):
    model = DeepVONet().to(device)
    model.eval()

    if checkpoint_path is None:
        print("Warning: no checkpoint provided. Predictions will use random weights.")
        return model

    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Checkpoint does not exist: {checkpoint_path}")

    checkpoint = torch.load(checkpoint_path, map_location=device)
    state_dict = checkpoint.get("state_dict", checkpoint)
    model.load_state_dict(state_dict)
    return model


def predict_pair(model, preprocess, frame_a, frame_b, device):
    image_a = preprocess(Image.open(frame_a).convert("RGB"))
    image_b = preprocess(Image.open(frame_b).convert("RGB"))
    stacked = torch.cat([image_a, image_b], dim=0)
    stacked = stacked.unsqueeze(0).to(device, dtype=torch.float32)

    with torch.no_grad():
        model.reset_hidden_states(size=1, zero=False)
        prediction = model(stacked)

    return prediction.squeeze(0).detach().cpu().numpy()


def write_predictions(output_dir, rows):
    output_dir.mkdir(parents=True, exist_ok=True)

    relative_path = output_dir / "predicted_relative_poses.csv"
    trajectory_path = output_dir / "predicted_trajectory.csv"

    with relative_path.open("w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["frame_a", "frame_b", "tx", "ty", "tz", "rx", "ry", "rz"])
        writer.writerows(rows)

    cumulative = np.zeros(6, dtype=np.float32)
    with trajectory_path.open("w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["frame", "x", "y", "z", "rx", "ry", "rz"])
        writer.writerow([rows[0][0], *cumulative.tolist()])
        for row in rows:
            cumulative += np.asarray(row[2:], dtype=np.float32)
            writer.writerow([row[1], *cumulative.tolist()])

    return relative_path, trajectory_path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run DeepVO inference on consecutive frames from a custom video."
    )
    parser.add_argument("--frames", required=True, help="Folder containing extracted frames.")
    parser.add_argument("--output", required=True, help="Output folder for trajectory CSV files.")
    parser.add_argument(
        "--checkpoint",
        default=None,
        help="Optional trained DeepVO checkpoint. If omitted, random weights are used.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    frames_dir = Path(args.frames).expanduser()
    output_dir = Path(args.output).expanduser()
    checkpoint_path = Path(args.checkpoint).expanduser() if args.checkpoint else None

    try:
        frame_paths = load_frame_paths(frames_dir)
        device = get_device()
        preprocess = build_preprocess()
        model = load_model(checkpoint_path, device)
    except (FileNotFoundError, ValueError, RuntimeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)

    print(f"Using device: {device}")
    print(f"Frames: {frames_dir}")
    print(f"Frame count: {len(frame_paths)}")

    rows = []
    for index in range(len(frame_paths) - 1):
        prediction = predict_pair(model, preprocess, frame_paths[index], frame_paths[index + 1], device)
        rows.append(
            [
                frame_paths[index].name,
                frame_paths[index + 1].name,
                *prediction.astype(float).tolist(),
            ]
        )

    relative_path, trajectory_path = write_predictions(output_dir, rows)
    print(f"Saved relative poses: {relative_path}")
    print(f"Saved trajectory: {trajectory_path}")
    print(f"Predicted frame pairs: {len(rows)}")


if __name__ == "__main__":
    main()
