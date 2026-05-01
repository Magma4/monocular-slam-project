# Final Project Report Draft

## 1. Introduction

This project investigates monocular visual odometry and monocular SLAM-style localization using two representative approaches: DeepVO and ORB-SLAM3. The motivation is to estimate camera motion from a single moving camera, compare learning-based and feature-based methods, and evaluate how each behaves on benchmark and custom video data.

The project was developed on a MacBook M4. A major practical goal was to make the workflow reproducible on Apple Silicon without CUDA, while keeping the repository organized for a semester-project report.

## 2. Methods with Code and Process Explanation

### DeepVO

DeepVO is a learning-based visual odometry method. It predicts relative camera motion between consecutive monocular frames. The predicted relative poses are accumulated into a trajectory and saved as CSV files.

In this project, DeepVO was patched to avoid hardcoded CUDA calls. The code now uses device-aware PyTorch execution with MPS support when available and CPU fallback otherwise. The KITTI dataset loader was also adjusted to support grayscale KITTI `image_0` frames.

Important DeepVO scripts:

```text
scripts/preprocessing/extract_frames.py
scripts/inference/run_deepvo_custom.py
scripts/inference/run_deepvo_kitti.py
scripts/visualization/plot_trajectory.py
scripts/visualization/deepvo_realtime_demo.py
```

### ORB-SLAM3

ORB-SLAM3 is a classical feature-based SLAM system. This project uses the monocular path as a baseline for comparison with DeepVO. Custom extracted frames are adapted into a lightweight KITTI-style folder layout and passed into the ORB-SLAM3 monocular executable.

ORB-SLAM3 was run in headless mode on macOS because the Pangolin viewer crashed due to macOS main-thread GUI handling. The headless mode preserves tracking and trajectory saving while disabling the viewer window.

Important ORB-SLAM3 scripts/configs:

```text
scripts/inference/run_orbslam3_kitti_custom.py
scripts/visualization/plot_orbslam3_trajectory.py
scripts/visualization/orbslam3_realtime_demo.py
configs/orbslam3_custom_1280x720.yaml
configs/orbslam3_custom_outdoor_loop2_1280x2276.yaml
```

## 3. Benchmark Experiments and Results

DeepVO was trained and evaluated using KITTI odometry grayscale data from `image_0`. Benchmark inference was run on KITTI sequences `04` and `06` using the locally trained checkpoint.

Benchmark outputs:

```text
outputs/trajectories/deepvo/kitti_benchmark/04/
outputs/trajectories/deepvo/kitti_benchmark/06/
outputs/plots/deepvo/kitti_benchmark/deepvo_kitti_04_trajectory.png
outputs/plots/deepvo/kitti_benchmark/deepvo_kitti_06_trajectory.png
```

The KITTI results provide the clearest benchmark context because ground-truth poses are available. Since the checkpoint is an early one-epoch experimental checkpoint, the results should be interpreted as a working baseline rather than a high-accuracy model.

## 4. Experiments on Custom Datasets

Custom videos were converted into extracted PNG frame sequences and used for inference and visualization.

Custom sequences:

```text
indoor_loop
outdoor_loop
outdoor_loop2
```

DeepVO trained-checkpoint custom outputs:

```text
outputs/trajectories/deepvo/custom_trained/indoor_loop/
outputs/trajectories/deepvo/custom_trained/outdoor_loop/
outputs/trajectories/deepvo/custom_trained/outdoor_loop2/
```

ORB-SLAM3 custom outputs:

```text
outputs/trajectories/orb_slam3/indoor_loop/keyframe_trajectory_tum.txt
outputs/trajectories/orb_slam3/outdoor_loop/keyframe_trajectory_tum.txt
outputs/trajectories/orb_slam3/outdoor_loop2/keyframe_trajectory_tum.txt
```

The `outdoor_loop2` sequence was large and portrait-oriented. It was extracted using a maximum width of `1280`, producing `5928` frames at `24 FPS` with saved frame size `1280x2276`. This sequence was useful as a stress test for both pipelines.

## 5. Comparative Analysis

DeepVO and ORB-SLAM3 produce different kinds of outputs. DeepVO produces dense frame-to-frame visual odometry predictions saved as CSV files. ORB-SLAM3 produces sparse keyframe trajectories in TUM format.

Indoor custom results were generally cleaner, especially for ORB-SLAM3, which saved `523` keyframe poses on `indoor_loop`. Outdoor results were more challenging. ORB-SLAM3 saved `182` keyframe poses on `outdoor_loop` and `451` on `outdoor_loop2`, but the `outdoor_loop2` log showed repeated local-map tracking failures and map resets.

DeepVO is easier to run as a Python-based inference workflow, but it can accumulate drift because it does not perform loop closure. ORB-SLAM3 has stronger classical SLAM structure, but it is sensitive to feature quality, motion blur, lighting, and approximate camera calibration.

## 6. Deployment / Real-Time Processing

The project includes pseudo-real-time replay demos for both methods:

```text
scripts/visualization/deepvo_realtime_demo.py
scripts/visualization/orbslam3_realtime_demo.py
```

These demos show the current frame and reveal the saved trajectory over time. They are useful for presentation and explanation, but they are not live inference systems.

For ORB-SLAM3, the demo includes an `--sync-mode even` option. This is useful because ORB-SLAM3 keyframes can be sparse or delayed, especially when tracking fails and later recovers.

The main deployment issue was ORB-SLAM3's Pangolin viewer on macOS. Headless mode was required to avoid the Cocoa main-thread viewer crash while still saving trajectory output.

## 7. Conclusion

This project successfully implements and compares DeepVO and ORB-SLAM3 for monocular motion estimation on a MacBook M4. DeepVO provides a learning-based visual odometry baseline with simple CSV outputs and KITTI benchmark experiments. ORB-SLAM3 provides a classical monocular SLAM baseline with TUM trajectory outputs and useful robustness observations on custom videos.

The project is strongest as an implementation, workflow, and qualitative comparison study. Future improvements would include calibrated camera intrinsics for custom videos, stronger DeepVO training, quantitative metrics where ground truth is available, and a polished exported PDF report.
