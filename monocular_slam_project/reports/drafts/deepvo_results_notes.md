# DeepVO Results Notes

This note summarizes the organized DeepVO outputs used for the semester project report.

## Output Categories

### Random Custom Results

Folder:

```text
outputs/trajectories/deepvo/custom_random/
```

Contains DeepVO inference results on the custom videos before loading a trained checkpoint. These runs used random model weights, so they are useful only as a pipeline sanity check.

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

### Trained Custom Results

Folder:

```text
outputs/trajectories/deepvo/custom_trained/
```

Contains DeepVO inference results on the same custom videos after loading the trained KITTI checkpoint:

```text
outputs/checkpoints/deepvo_kitti/checkpoint_1.pth
```

Sequences:

```text
outputs/trajectories/deepvo/custom_trained/indoor_loop/
outputs/trajectories/deepvo/custom_trained/outdoor_loop/
```

Plots:

```text
outputs/plots/deepvo/custom_trained/deepvo_custom_trained_indoor_loop_trajectory.png
outputs/plots/deepvo/custom_trained/deepvo_custom_trained_outdoor_loop_trajectory.png
```

### KITTI Benchmark Results

Folder:

```text
outputs/trajectories/deepvo/kitti_benchmark/
```

Contains DeepVO inference results on KITTI odometry sequences using grayscale `image_0` frames and the trained checkpoint:

```text
outputs/checkpoints/deepvo_kitti/checkpoint_1.pth
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
- Trained custom runs used `checkpoint_1.pth`, trained on KITTI, so they are better for demonstration but may still drift on custom videos.
- KITTI benchmark runs are the clearest report comparison because KITTI provides ground-truth poses.
- DeepVO estimates visual odometry, so drift can accumulate over time because there is no loop closure or global map correction.
