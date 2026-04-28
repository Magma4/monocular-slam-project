#!/usr/bin/env python3
"""Plot a 2D top-down trajectory from an ORB-SLAM3 TUM trajectory file."""

import argparse
import os
from pathlib import Path
import sys
import tempfile


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "plots" / "orb_slam3"

# ORB-SLAM3 TUM format: timestamp tx ty tz qx qy qz qw
TUM_COLUMNS = ("timestamp", "tx", "ty", "tz", "qx", "qy", "qz", "qw")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Plot a top-down 2D path from an ORB-SLAM3 TUM trajectory file."
    )
    parser.add_argument("trajectory_txt", help="Input ORB-SLAM3 TUM trajectory file.")
    parser.add_argument(
        "--output",
        help=(
            "Output PNG path. Defaults to "
            "outputs/plots/orb_slam3/<sequence>_trajectory.png."
        ),
    )
    parser.add_argument(
        "--title",
        help="Optional plot title. Defaults to the sequence folder name.",
    )
    return parser.parse_args()


def read_tum_trajectory(path):
    if not path.exists():
        raise FileNotFoundError(f"Trajectory file does not exist: {path}")
    if not path.is_file():
        raise ValueError(f"Trajectory path is not a file: {path}")

    rows = []
    with path.open("r", encoding="utf-8") as trajectory_file:
        for line_number, line in enumerate(trajectory_file, start=1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split()
            if len(parts) != len(TUM_COLUMNS):
                raise ValueError(
                    f"Invalid TUM row at line {line_number}: expected 8 values, got {len(parts)}."
                )

            try:
                rows.append(tuple(float(value) for value in parts))
            except ValueError as error:
                raise ValueError(
                    f"Invalid numeric value in trajectory at line {line_number}."
                ) from error

    if not rows:
        raise ValueError(f"Trajectory file has no valid poses: {path}")

    return rows


def default_output_path(trajectory_path):
    sequence_name = trajectory_path.parent.name
    return DEFAULT_OUTPUT_ROOT / f"{sequence_name}_trajectory.png"


def plot_trajectory(trajectory_path, output_path, title):
    try:
        cache_root = Path(tempfile.gettempdir()) / "monocular_slam_matplotlib"
        os.environ.setdefault(
            "MPLCONFIGDIR", str(cache_root / "config")
        )
        os.environ.setdefault("XDG_CACHE_HOME", str(cache_root / "cache"))
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print(
            "Error: matplotlib is not installed. Run `python -m pip install -r requirements.txt`.",
            file=sys.stderr,
        )
        sys.exit(1)

    rows = read_tum_trajectory(trajectory_path)
    tx_index = TUM_COLUMNS.index("tx")
    tz_index = TUM_COLUMNS.index("tz")
    x_values = [row[tx_index] for row in rows]
    z_values = [row[tz_index] for row in rows]

    output_path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(8, 6))
    plt.plot(x_values, z_values, linewidth=1.8, color="#1f77b4")
    plt.scatter(x_values[0], z_values[0], label="start", s=40, color="#2ca02c")
    plt.scatter(x_values[-1], z_values[-1], label="end", s=40, color="#d62728")
    plt.xlabel("x translation")
    plt.ylabel("z translation")
    plt.title(title or trajectory_path.parent.name)
    plt.axis("equal")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()

    return len(rows)


def main():
    args = parse_args()
    trajectory_path = Path(args.trajectory_txt).expanduser().resolve()
    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else default_output_path(trajectory_path).resolve()
    )

    try:
        point_count = plot_trajectory(trajectory_path, output_path, args.title)
    except (FileNotFoundError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)

    print(f"Read trajectory: {trajectory_path}")
    print("Parsed format: TUM (timestamp tx ty tz qx qy qz qw)")
    print(f"Trajectory points plotted: {point_count}")
    print(f"Saved plot: {output_path}")


if __name__ == "__main__":
    main()
