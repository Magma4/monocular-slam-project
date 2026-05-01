# DeepVO Summary

## Overview

DeepVO is the learning-based visual odometry component of this monocular localization/mapping semester project. It estimates relative camera motion from consecutive monocular frames and accumulates those estimates into a predicted trajectory.

DeepVO is located at:

```text
src/models/deepvo/
```

DeepVO outputs are organized under:

```text
outputs/trajectories/deepvo/
outputs/plots/deepvo/
```

## Setup and Training

The DeepVO repository was patched for MacBook M4 / Apple Silicon by replacing CUDA-specific assumptions with device-aware PyTorch code. The code attempts to use Apple Silicon MPS when available and falls back to CPU otherwise.

KITTI odometry grayscale data was used from `image_0`. The dataset loader was adjusted so the image folder can be configured while defaulting to the grayscale setup used in this project.

A short KITTI training run produced the local checkpoint:

```text
outputs/checkpoints/deepvo_kitti/checkpoint_1.pth
```

This checkpoint is excluded from GitHub because it is a large generated model artifact.

## Custom Dataset Results

Custom videos were converted into extracted frame sequences:

```text
data/custom/extracted_frames/indoor_loop/
data/custom/extracted_frames/outdoor_loop/
data/custom/extracted_frames/outdoor_loop2/
```

The `outdoor_loop2` video was large and portrait-oriented. To keep local storage manageable, its frames were extracted with `--max-width 1280`, producing `5928` frames at `24 FPS` with saved frame size `1280x2276`.

### Random-Weight Custom Runs

Random-weight runs were created only as pipeline sanity checks. They verify frame loading, inference execution, CSV export, and plotting, but they should not be interpreted as meaningful localization results.

```text
outputs/trajectories/deepvo/custom_random/indoor_loop/
outputs/trajectories/deepvo/custom_random/outdoor_loop/
outputs/plots/deepvo/custom_random/
```

### Trained Custom Runs

Trained custom runs used:

```text
outputs/checkpoints/deepvo_kitti/checkpoint_1.pth
```

Trajectory outputs:

```text
outputs/trajectories/deepvo/custom_trained/indoor_loop/
outputs/trajectories/deepvo/custom_trained/outdoor_loop/
outputs/trajectories/deepvo/custom_trained/outdoor_loop2/
```

Report plots:

```text
outputs/plots/deepvo/custom_trained/deepvo_custom_trained_indoor_loop_trajectory.png
outputs/plots/deepvo/custom_trained/deepvo_custom_trained_outdoor_loop_trajectory.png
outputs/plots/deepvo/custom_trained/deepvo_custom_trained_outdoor_loop2_trajectory.png
```

The custom runs demonstrate the DeepVO pipeline on project video data, but results should be interpreted qualitatively because the checkpoint was trained on KITTI driving data and the custom videos differ from KITTI.

## KITTI Benchmark Results

Benchmark inference was run on KITTI odometry sequences `04` and `06` using grayscale `image_0` frames and the trained checkpoint.

Trajectory outputs:

```text
outputs/trajectories/deepvo/kitti_benchmark/04/
outputs/trajectories/deepvo/kitti_benchmark/06/
```

Each benchmark folder contains predicted relative poses, accumulated predicted trajectory, and ground-truth trajectory CSV files.

Report plots:

```text
outputs/plots/deepvo/kitti_benchmark/deepvo_kitti_04_trajectory.png
outputs/plots/deepvo/kitti_benchmark/deepvo_kitti_06_trajectory.png
```

These benchmark runs are the clearest DeepVO evaluation examples because KITTI provides ground-truth poses for comparison.

## Pseudo-Real-Time Demo

The DeepVO pseudo-real-time demo replays extracted frames and reveals the saved predicted trajectory over time. It is a visualization/replay tool, not live model inference.

Default demo:

```bash
.venv/bin/python scripts/visualization/deepvo_realtime_demo.py
```

`outdoor_loop2` demo:

```bash
.venv/bin/python scripts/visualization/deepvo_realtime_demo.py \
  --frames data/custom/extracted_frames/outdoor_loop2 \
  --trajectory outputs/trajectories/deepvo/custom_trained/outdoor_loop2/predicted_trajectory.csv \
  --fps 24
```

## Strengths

- Provides a compact learning-based visual odometry baseline.
- Supports KITTI benchmark data and custom video frame folders.
- Saves simple CSV outputs that are easy to plot and inspect.
- Runs on MacBook M4 after removing CUDA-only assumptions.
- Works well as an academic comparison point against ORB-SLAM3.

## Limitations

- DeepVO is visual odometry, not full SLAM; it does not perform loop closure or global map correction.
- Accumulated relative-pose errors can cause drift over time.
- The current checkpoint is an early KITTI-trained checkpoint, so it is suitable for experimentation but not strong accuracy claims.
- Custom videos can suffer from domain shift relative to KITTI driving data.
- Long custom sequences such as `outdoor_loop2` take time to process on CPU.
