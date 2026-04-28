# Monocular SLAM / Visual Odometry Semester Project

This repository contains a semester project on monocular visual odometry and SLAM-style localization. It compares two approaches on custom monocular video frame sequences:

- **DeepVO**: a learning-based monocular visual odometry baseline.
- **ORB-SLAM3**: a classical feature-based monocular SLAM baseline.

The project is organized for custom video preprocessing, KITTI benchmark experiments, trajectory visualization, report writing, and lightweight pseudo-real-time demos.

## Objectives

- Study monocular camera motion estimation using visual odometry and SLAM.
- Run DeepVO on custom videos and KITTI odometry data.
- Run ORB-SLAM3 on the same custom frame sequences as a classical SLAM baseline.
- Generate trajectory outputs, plots, notebooks, and report-ready summaries.
- Compare qualitative behavior, setup complexity, drift, and tracking stability.

## Real-Time-Style Demos

These demos are **pseudo-real-time visualizations**. They replay existing extracted frames and reveal saved trajectory outputs over time. They are not live model inference or live SLAM tracking.

### DeepVO Replay Demo

DeepVO replays the indoor custom frame sequence while updating the trained DeepVO predicted trajectory.

<img src="assets/demo_gifs/deepvo_realtime_demo_readme.gif" alt="DeepVO pseudo-real-time trajectory replay demo" width="640">

Run locally with:

```bash
.venv/bin/python scripts/visualization/deepvo_realtime_demo.py
```

### ORB-SLAM3 Replay Demo

ORB-SLAM3 replays the indoor custom frame sequence while updating the saved ORB-SLAM3 keyframe trajectory. The ORB-SLAM3 workflow uses headless mode on macOS because the Pangolin viewer crashes due to macOS main-thread GUI handling.

<img src="assets/demo_gifs/orbslam3_realtime_demo_readme.gif" alt="ORB-SLAM3 pseudo-real-time trajectory replay demo" width="640">

Run locally with smoother presentation playback:

```bash
.venv/bin/python scripts/visualization/orbslam3_realtime_demo.py --sync-mode even
```

## Current Implementation Status

Completed:

- DeepVO repository added under `src/models/deepvo/`.
- DeepVO patched for MacBook M4 / Apple Silicon with MPS or CPU fallback instead of hardcoded CUDA.
- Custom videos converted into extracted frame sequences.
- KITTI grayscale odometry data used with `image_0`.
- DeepVO training and inference completed.
- DeepVO benchmark inference completed on KITTI sequences `04` and `06`.
- ORB-SLAM3 added locally and built successfully on MacBook M4.
- ORB-SLAM3 monocular custom-frame workflow created using a KITTI-style adapter.
- ORB-SLAM3 headless `--no-viewer` workflow used to avoid Pangolin viewer crashes on macOS.
- Indoor and outdoor custom ORB-SLAM3 TUM trajectory outputs generated.
- Trajectory plots, summaries, notebooks, and pseudo-real-time replay demos created.

Current note:

- ORB-SLAM3 source/build files are kept local and excluded from GitHub because the full clone, vocabulary, Pangolin build, and binaries are large. The repository includes the project-level scripts, configs, summaries, plots, and small trajectory outputs needed to explain the workflow.

## Folder Structure

```text
monocular_slam_project/
├── assets/
│   └── demo_gifs/              # Optimized README demo GIFs
├── configs/                    # Project-level model/settings files
├── data/                       # Local datasets and videos, excluded from GitHub
│   ├── benchmark/
│   └── custom/
├── notebooks/                  # Report/demo notebooks
├── outputs/
│   ├── checkpoints/            # Local checkpoints, excluded from GitHub
│   ├── plots/                  # Small report-ready trajectory plots
│   └── trajectories/           # Small report-ready trajectory outputs
├── reports/
│   └── drafts/                 # Markdown project summaries
├── scripts/
│   ├── preprocessing/          # Data preparation scripts
│   ├── inference/              # DeepVO and ORB-SLAM3 runner scripts
│   └── visualization/          # Plotting and replay demo scripts
└── src/
    └── models/
        └── deepvo/             # Patched DeepVO code
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

### 4. Run DeepVO Inference on Custom Frames

```bash
cd ../../..
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/inference/run_deepvo_custom.py \
  --frames data/custom/extracted_frames/indoor_loop \
  --output outputs/trajectories/deepvo/custom_trained/indoor_loop \
  --checkpoint outputs/checkpoints/deepvo_kitti/checkpoint_1.pth
```

## ORB-SLAM3 Workflow

ORB-SLAM3 was built locally under `src/models/orb_slam3/`, but the full source/build tree is excluded from GitHub due to size. The setup notes are documented in the project report and local ORB-SLAM3 setup file.

Run ORB-SLAM3 on custom frames in headless mode:

```bash
python scripts/inference/run_orbslam3_kitti_custom.py \
  --sequence indoor_loop \
  --fps 30 \
  --no-viewer
```

Outdoor sequence:

```bash
python scripts/inference/run_orbslam3_kitti_custom.py \
  --sequence outdoor_loop \
  --fps 30 \
  --no-viewer
```

The custom ORB-SLAM3 video settings are stored at:

```text
configs/orbslam3_custom_1280x720.yaml
```

## Outputs and Results

DeepVO outputs are organized into:

```text
outputs/trajectories/deepvo/custom_random/
outputs/trajectories/deepvo/custom_trained/
outputs/trajectories/deepvo/kitti_benchmark/
outputs/plots/deepvo/
```

ORB-SLAM3 outputs are organized into:

```text
outputs/trajectories/orb_slam3/
outputs/plots/orb_slam3/
```

Report-ready files include:

```text
reports/drafts/deepvo_summary.md
reports/drafts/orbslam3_summary.md
notebooks/deepvo_project_demo.ipynb
notebooks/orbslam3_project_demo.ipynb
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
- ORB-SLAM3 local source/build tree, vocabulary, Pangolin build, and binaries
- Large root-level raw GIF/video exports
- Logs and temporary generated adapter inputs

This keeps the repository small, reproducible, and appropriate for GitHub.

## Notes

DeepVO is visual odometry, not full SLAM. It estimates frame-to-frame motion and accumulates the result into a trajectory, so drift can accumulate over time.

ORB-SLAM3 is a full SLAM system, but this project uses its monocular mode. Monocular trajectories have arbitrary scale unless external scale information or calibration constraints are provided. On macOS, the Pangolin viewer was disabled and the project used headless trajectory export.

## Next Steps

- Improve camera calibration for custom ORB-SLAM3 runs.
- Add a concise comparison table for DeepVO vs ORB-SLAM3.
- Export final report figures and PDFs from the notebooks and markdown summaries.
