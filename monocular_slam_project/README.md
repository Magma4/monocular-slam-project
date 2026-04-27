# Monocular SLAM / Visual Odometry Semester Project

This repository contains a semester project on monocular visual odometry and SLAM-style localization. The current implementation focuses on **DeepVO**, a learning-based monocular visual odometry model that estimates camera motion from image sequences.

The project is organized to support custom video experiments, KITTI benchmark testing, trajectory visualization, report writing, and future comparison with ORB-SLAM3.

## Objectives

- Study monocular camera motion estimation using visual odometry.
- Run DeepVO on custom videos and benchmark data.
- Compare random-weight and trained-checkpoint behavior.
- Generate trajectory CSV files and plots for analysis.
- Prepare the project structure for a later ORB-SLAM3 comparison.

## Current Implementation Status

Completed:

- DeepVO repository added under `src/models/deepvo/`.
- DeepVO patched for MacBook M4 / Apple Silicon by replacing CUDA-specific code with device-aware PyTorch logic.
- Custom videos converted into extracted frame sequences.
- KITTI odometry grayscale data used with `image_0`.
- DeepVO training completed on KITTI.
- Trained checkpoint created locally at `outputs/checkpoints/deepvo_kitti/checkpoint_1.pth`.
- Inference completed on custom indoor and outdoor videos.
- Benchmark inference completed on KITTI sequences `04` and `06`.
- Trajectory plots generated for custom and KITTI runs.
- Report summary and notebook created.

Planned:

- Add ORB-SLAM3 and compare it against the DeepVO baseline.

## Folder Structure

```text
monocular_slam_project/
├── data/
│   ├── benchmark/          # Local benchmark datasets, excluded from GitHub
│   └── custom/             # Local videos and extracted frames, excluded from GitHub
├── notebooks/
│   └── deepvo_project_demo.ipynb
├── outputs/
│   ├── checkpoints/        # Local model checkpoints, excluded from GitHub
│   ├── plots/deepvo/       # Report-ready trajectory plots
│   └── trajectories/deepvo/# Trajectory CSV outputs
├── reports/
│   └── drafts/             # Markdown summaries and project notes
├── scripts/
│   ├── preprocessing/      # Data preparation scripts
│   ├── inference/          # DeepVO inference scripts
│   └── visualization/      # Plotting scripts
└── src/
    └── models/
        └── deepvo/         # Patched DeepVO code
```

## Setup

Create and activate a Python virtual environment:

```bash
cd monocular_slam_project
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

For Apple Silicon / MacBook M4, enable PyTorch fallback for unsupported MPS operations:

```bash
export PYTORCH_ENABLE_MPS_FALLBACK=1
```

## DeepVO Workflow

### 1. Extract Custom Video Frames

```bash
python scripts/preprocessing/extract_frames.py \
  data/custom/raw_videos/indoor_loop.mov \
  data/custom/extracted_frames/indoor_loop
```

```bash
python scripts/preprocessing/extract_frames.py \
  data/custom/raw_videos/outdoor_loop.mov \
  data/custom/extracted_frames/outdoor_loop
```

### 2. Check KITTI Layout

DeepVO expects KITTI odometry data under:

```text
data/benchmark/kitti/
├── poses/
└── sequences/
    ├── 00/image_0/
    ├── 01/image_0/
    └── ...
```

Validate the layout:

```bash
python scripts/preprocessing/check_kitti_layout.py
```

### 3. Train DeepVO on KITTI

The project uses KITTI grayscale frames from `image_0`.

```bash
cd src/models/deepvo
PYTORCH_ENABLE_MPS_FALLBACK=1 python main.py \
  --mode train \
  --datapath ../../../data/benchmark/kitti \
  --checkpoint_path ../../../outputs/checkpoints/deepvo_kitti \
  --image_folder image_0 \
  --bsize 1 \
  --trajectory_length 10 \
  --train_iter 1
```

### 4. Run Inference on Custom Frames

Example for the indoor custom sequence:

```bash
cd ../../..
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/inference/run_deepvo_custom.py \
  --frames data/custom/extracted_frames/indoor_loop \
  --output outputs/trajectories/deepvo/custom_trained/indoor_loop \
  --checkpoint outputs/checkpoints/deepvo_kitti/checkpoint_1.pth
```

### 5. Run KITTI Benchmark Inference

Example for KITTI sequence `04`:

```bash
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/inference/run_deepvo_kitti.py \
  --kitti-root data/benchmark/kitti \
  --sequence 04 \
  --image-folder image_0 \
  --checkpoint outputs/checkpoints/deepvo_kitti/checkpoint_1.pth \
  --output-root outputs/trajectories/deepvo/kitti_benchmark \
  --plot-root outputs/plots/deepvo/kitti_benchmark
```

## Outputs and Results

DeepVO outputs are organized into three groups:

```text
outputs/trajectories/deepvo/custom_random/
outputs/trajectories/deepvo/custom_trained/
outputs/trajectories/deepvo/kitti_benchmark/
```

Trajectory plots are organized under:

```text
outputs/plots/deepvo/
```

Completed result categories:

- Random-weight custom runs for pipeline sanity checks.
- Trained-checkpoint custom runs for indoor and outdoor videos.
- KITTI benchmark runs on sequences `04` and `06`, including predicted and ground-truth trajectory CSV files.

Report-ready files:

```text
reports/drafts/deepvo_summary.md
reports/drafts/deepvo_results_notes.md
notebooks/deepvo_project_demo.ipynb
```

## Excluded from GitHub

Large or machine-specific files are intentionally excluded:

- KITTI dataset files
- Raw custom videos
- Extracted video frames
- Model checkpoints such as `.pth` files
- Python virtual environments
- Python cache files
- Jupyter checkpoint files
- OS/editor temporary files

This keeps the repository small, reproducible, and appropriate for GitHub.

## Notes

DeepVO is a visual odometry method, not a full SLAM system. It estimates frame-to-frame motion and accumulates the result into a trajectory. Because it does not perform loop closure or global map correction, drift can accumulate over time.

## Next Steps

- Add ORB-SLAM3 as a classical feature-based SLAM baseline.
- Run ORB-SLAM3 on the same custom videos and KITTI sequences where possible.
- Compare DeepVO and ORB-SLAM3 in terms of trajectory shape, drift, setup complexity, and qualitative behavior.
