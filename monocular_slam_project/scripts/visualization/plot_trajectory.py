#!/usr/bin/env python3
"""Plot a 2D top-down trajectory from a DeepVO trajectory CSV."""

import argparse
import csv
import sys
from pathlib import Path

try:
    import matplotlib.pyplot as plt
except ImportError:
    print(
        "Error: matplotlib is not installed. Run `python -m pip install -r requirements.txt`.",
        file=sys.stderr,
    )
    sys.exit(1)


COORDINATE_PAIRS = [
    ("x", "z"),
    ("tx", "tz"),
    ("x", "y"),
    ("tx", "ty"),
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Plot a top-down 2D trajectory from a CSV file."
    )
    parser.add_argument("trajectory_csv", help="Input trajectory CSV file.")
    parser.add_argument("output_png", help="Output PNG file.")
    parser.add_argument(
        "--title",
        default=None,
        help="Optional plot title. Defaults to the CSV filename.",
    )
    return parser.parse_args()


def read_rows(csv_path):
    if not csv_path.exists():
        raise FileNotFoundError(f"Trajectory CSV does not exist: {csv_path}")
    if not csv_path.is_file():
        raise ValueError(f"Trajectory path is not a file: {csv_path}")

    with csv_path.open(newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames is None:
            raise ValueError(f"CSV has no header row: {csv_path}")
        rows = list(reader)

    if not rows:
        raise ValueError(f"CSV has no trajectory rows: {csv_path}")

    return reader.fieldnames, rows


def choose_coordinate_columns(fieldnames):
    normalized = {name.strip().lower(): name for name in fieldnames}
    for x_name, y_name in COORDINATE_PAIRS:
        if x_name in normalized and y_name in normalized:
            return normalized[x_name], normalized[y_name]

    raise ValueError(
        "Could not find coordinate columns. Expected one of: "
        + ", ".join(f"{x}/{y}" for x, y in COORDINATE_PAIRS)
    )


def column_values(rows, column_name):
    values = []
    for index, row in enumerate(rows, start=1):
        try:
            values.append(float(row[column_name]))
        except (TypeError, ValueError) as error:
            raise ValueError(
                f"Invalid numeric value in column '{column_name}' at row {index}."
            ) from error
    return values


def plot_trajectory(csv_path, output_path, title):
    fieldnames, rows = read_rows(csv_path)
    x_column, y_column = choose_coordinate_columns(fieldnames)
    x_values = column_values(rows, x_column)
    y_values = column_values(rows, y_column)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(8, 6))
    plt.plot(x_values, y_values, linewidth=1.8)
    plt.scatter(x_values[0], y_values[0], label="start", s=35)
    plt.scatter(x_values[-1], y_values[-1], label="end", s=35)
    plt.xlabel(x_column)
    plt.ylabel(y_column)
    plt.title(title or csv_path.stem)
    plt.axis("equal")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()

    return x_column, y_column, len(rows)


def main():
    args = parse_args()
    csv_path = Path(args.trajectory_csv).expanduser()
    output_path = Path(args.output_png).expanduser()

    try:
        x_column, y_column, row_count = plot_trajectory(csv_path, output_path, args.title)
    except (FileNotFoundError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)

    print(f"Read trajectory: {csv_path}")
    print(f"Detected top-down columns: {x_column}, {y_column}")
    print(f"Trajectory points plotted: {row_count}")
    print(f"Saved plot: {output_path}")


if __name__ == "__main__":
    main()
