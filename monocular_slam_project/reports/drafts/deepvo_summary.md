# DeepVO Summary

## Overview

This project uses DeepVO as the learning-based visual odometry component of a monocular localization/mapping semester project. DeepVO estimates relative camera motion from monocular image sequences, then accumulates those estimates into a trajectory for visualization.

The DeepVO repository is located at:

```text
src/models/deepvo/
```

The generated DeepVO outputs are organized under:

```text
outputs/trajectories/deepvo/
outputs/plots/deepvo/
```

## Setup and Training

DeepVO was patched for MacBook M4 by replacing CUDA-specific calls with device-aware PyTorch code. The model uses Apple Silicon MPS when available and falls back to CPU otherwise.

KITTI odometry grayscale data is stored under:

```text
data/benchmark/kitti/
```

The dataset loader was updated to use KITTI `image_0` frames by default. A one-epoch checkpoint was trained and saved at:

```text
outputs/checkpoints/deepvo_kitti/checkpoint_1.pth
```

This checkpoint is used for the trained custom-video runs and the KITTI benchmark runs.

## Custom Dataset Results

Custom videos were converted into extracted frame sequences:

```text
data/custom/extracted_frames/indoor_loop/
data/custom/extracted_frames/outdoor_loop/
```

Two groups of custom results are kept separate.

Random-weight custom runs:

```text
outputs/trajectories/deepvo/custom_random/indoor_loop/
outputs/trajectories/deepvo/custom_random/outdoor_loop/
outputs/plots/deepvo/custom_random/
```

These runs used random model weights and are only useful for verifying that preprocessing, inference, CSV export, and plotting work correctly.

Trained-checkpoint custom runs:

```text
outputs/trajectories/deepvo/custom_trained/indoor_loop/
outputs/trajectories/deepvo/custom_trained/outdoor_loop/
outputs/plots/deepvo/custom_trained/
```

These runs used:

```text
outputs/checkpoints/deepvo_kitti/checkpoint_1.pth
```

Report plots:

```text
outputs/plots/deepvo/custom_trained/deepvo_custom_trained_indoor_loop_trajectory.png
outputs/plots/deepvo/custom_trained/deepvo_custom_trained_outdoor_loop_trajectory.png
```

## KITTI Benchmark Results

Benchmark inference was run on KITTI sequences `04` and `06` using grayscale `image_0` frames and the trained checkpoint.

Trajectory outputs:

```text
outputs/trajectories/deepvo/kitti_benchmark/04/
outputs/trajectories/deepvo/kitti_benchmark/06/
```

Each benchmark folder contains:

```text
predicted_relative_poses.csv
predicted_trajectory.csv
ground_truth_trajectory.csv
```

Report plots:

```text
outputs/plots/deepvo/kitti_benchmark/deepvo_kitti_04_trajectory.png
outputs/plots/deepvo/kitti_benchmark/deepvo_kitti_06_trajectory.png
```

These KITTI runs are the clearest benchmark results because ground-truth trajectories are available for comparison.

## Strengths

- DeepVO provides a compact learning-based visual odometry baseline.
- The pipeline supports both custom videos and KITTI benchmark sequences.
- Outputs are easy to inspect because predictions are saved as CSV files and trajectory plots.
- The MacBook M4 patches make the code usable without CUDA hardware.

## Limitations

- DeepVO is visual odometry, not full SLAM. It does not perform loop closure or global map correction.
- Trajectory drift can accumulate because relative pose errors are integrated over time.
- The current checkpoint is an early one-epoch model, so it is suitable for experimentation but not final accuracy claims.
- Custom video results may be affected by domain shift because the model was trained on KITTI driving data.
