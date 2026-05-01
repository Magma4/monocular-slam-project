# DeepVO Results Notes

This note summarizes the organized DeepVO outputs used for the semester project report.

## Random Custom Results

Folder:

```text
outputs/trajectories/deepvo/custom_random/
```

These runs used random model weights. They are useful only as pipeline sanity checks for preprocessing, inference, CSV export, and plotting.

Sequences:

```text
outputs/trajectories/deepvo/custom_random/indoor_loop/
outputs/trajectories/deepvo/custom_random/outdoor_loop/
```

Plots:

```text
outputs/plots/deepvo/custom_random/deepvo_custom_random_indoor_loop_trajectory.png
outputs/plots/deepvo/custom_random/deepvo_custom_random_outdoor_loop_trajectory.png
```

## Trained Custom Results

Folder:

```text
outputs/trajectories/deepvo/custom_trained/
```

These runs used the trained KITTI checkpoint:

```text
outputs/checkpoints/deepvo_kitti/checkpoint_1.pth
```

Sequences:

```text
outputs/trajectories/deepvo/custom_trained/indoor_loop/
outputs/trajectories/deepvo/custom_trained/outdoor_loop/
outputs/trajectories/deepvo/custom_trained/outdoor_loop2/
```

Plots:

```text
outputs/plots/deepvo/custom_trained/deepvo_custom_trained_indoor_loop_trajectory.png
outputs/plots/deepvo/custom_trained/deepvo_custom_trained_outdoor_loop_trajectory.png
outputs/plots/deepvo/custom_trained/deepvo_custom_trained_outdoor_loop2_trajectory.png
```

## KITTI Benchmark Results

Folder:

```text
outputs/trajectories/deepvo/kitti_benchmark/
```

Sequences:

```text
outputs/trajectories/deepvo/kitti_benchmark/04/
outputs/trajectories/deepvo/kitti_benchmark/06/
```

Plots:

```text
outputs/plots/deepvo/kitti_benchmark/deepvo_kitti_04_trajectory.png
outputs/plots/deepvo/kitti_benchmark/deepvo_kitti_06_trajectory.png
```

## Interpretation Notes

- Random custom runs should not be used as meaningful localization results.
- Trained custom runs used `checkpoint_1.pth`, trained on KITTI, so they are better for demonstration but can still drift on custom videos.
- KITTI benchmark runs are the clearest report comparison because KITTI provides ground-truth poses.
- `outdoor_loop2` is useful as a long custom-video stress test, but it differs significantly from KITTI and should be discussed qualitatively.
- DeepVO estimates visual odometry, so drift can accumulate over time because there is no loop closure or global map correction.
