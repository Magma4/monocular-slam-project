# DeepVO vs ORB-SLAM3 Comparison Summary

## Overview

This project compares two monocular motion-estimation approaches:

| Method | Category | Main Output | Project Role |
| --- | --- | --- | --- |
| DeepVO | Learning-based visual odometry | Predicted relative poses and accumulated CSV trajectory | Learning-based VO baseline |
| ORB-SLAM3 | Feature-based monocular SLAM | TUM-format keyframe trajectory | Classical SLAM baseline |

The comparison is qualitative for custom videos because no ground-truth trajectory is available. KITTI sequences `04` and `06` provide the clearest DeepVO benchmark context because ground-truth poses are available there.

## Benchmark Behavior

DeepVO was trained and evaluated using KITTI odometry grayscale frames from `image_0`. Benchmark inference was run on KITTI sequences `04` and `06`.

Relevant outputs:

```text
outputs/trajectories/deepvo/kitti_benchmark/04/
outputs/trajectories/deepvo/kitti_benchmark/06/
outputs/plots/deepvo/kitti_benchmark/deepvo_kitti_04_trajectory.png
outputs/plots/deepvo/kitti_benchmark/deepvo_kitti_06_trajectory.png
```

The KITTI benchmark is useful because predicted trajectories can be plotted against ground truth. The model checkpoint used here was an early training checkpoint, so the benchmark results should be presented as a working experimental baseline rather than a state-of-the-art claim.

ORB-SLAM3 was used primarily for custom-video monocular comparison in this project. A full quantitative KITTI ORB-SLAM3 evaluation was not the focus of the final workflow.

## Indoor Custom Results

The indoor sequence is the cleanest custom comparison case.

DeepVO:

```text
outputs/trajectories/deepvo/custom_trained/indoor_loop/predicted_trajectory.csv
outputs/plots/deepvo/custom_trained/deepvo_custom_trained_indoor_loop_trajectory.png
```

ORB-SLAM3:

```text
outputs/trajectories/orb_slam3/indoor_loop/keyframe_trajectory_tum.txt
outputs/plots/orb_slam3/indoor_loop_trajectory.png
```

ORB-SLAM3 saved `523` keyframe poses for the indoor run, making it the strongest ORB-SLAM3 custom result. DeepVO produced a dense frame-by-frame accumulated trajectory because it predicts motion for consecutive frame pairs.

## Outdoor Custom Results

The first outdoor sequence was harder for ORB-SLAM3 than the indoor sequence.

DeepVO:

```text
outputs/trajectories/deepvo/custom_trained/outdoor_loop/predicted_trajectory.csv
outputs/plots/deepvo/custom_trained/deepvo_custom_trained_outdoor_loop_trajectory.png
```

ORB-SLAM3:

```text
outputs/trajectories/orb_slam3/outdoor_loop/keyframe_trajectory_tum.txt
outputs/plots/orb_slam3/outdoor_loop_trajectory.png
```

ORB-SLAM3 saved `182` keyframe poses for `outdoor_loop`, fewer than the indoor result. The reduced keyframe count and earlier tracking issues suggest that lighting, motion blur, viewpoint changes, texture, or approximate camera intrinsics made the sequence more difficult.

## Outdoor Loop 2 Results

`outdoor_loop2` is a longer portrait-oriented custom video. It was extracted with resizing to keep local storage practical:

```bash
.venv/bin/python scripts/preprocessing/extract_frames.py \
  data/custom/raw_videos/outdoor_loop2.MOV \
  data/custom/extracted_frames/outdoor_loop2 \
  --max-width 1280
```

Resulting frame sequence:

```text
5928 frames, 24 FPS, saved frame size 1280x2276
```

DeepVO outputs:

```text
outputs/trajectories/deepvo/custom_trained/outdoor_loop2/predicted_trajectory.csv
outputs/plots/deepvo/custom_trained/deepvo_custom_trained_outdoor_loop2_trajectory.png
```

ORB-SLAM3 outputs:

```text
outputs/trajectories/orb_slam3/outdoor_loop2/keyframe_trajectory_tum.txt
outputs/plots/orb_slam3/outdoor_loop2_trajectory.png
outputs/logs/orb_slam3/outdoor_loop2_mono_kitti_old.log
```

ORB-SLAM3 saved `451` keyframe poses for `outdoor_loop2`, but the log contains many local-map tracking failures and map resets. This makes `outdoor_loop2` useful as a robustness/stress-test sequence rather than a clean SLAM result.

## Drift and Robustness Observations

DeepVO:

- Produces dense trajectory output because it predicts motion between consecutive frames.
- Can drift because relative-pose errors accumulate over time.
- Does not perform loop closure, relocalization, or global map correction.
- Custom-video performance is affected by domain shift from KITTI training data.

ORB-SLAM3:

- Produces sparse keyframe trajectories rather than dense frame-by-frame trajectories.
- Can be more geometrically interpretable because it uses feature matching, mapping, and keyframes.
- Can lose tracking when frames have blur, low texture, strong rotation, lighting change, or calibration mismatch.
- Monocular output has arbitrary scale without external scale constraints.

## Deployment and macOS Issues

DeepVO required PyTorch device patches to avoid CUDA-only assumptions. On the MacBook M4, it can use MPS when supported and falls back to CPU otherwise.

ORB-SLAM3 required more system-level setup. Pangolin caused a macOS viewer crash:

```text
nextEventMatchingMask should only be called from the Main Thread!
```

The project therefore uses a headless ORB-SLAM3 workflow with:

```bash
--no-viewer
```

This keeps tracking and trajectory export working without opening the Pangolin viewer.

## Pseudo-Real-Time Demo Summary

Both methods have replay-based pseudo-real-time demos under:

```text
scripts/visualization/deepvo_realtime_demo.py
scripts/visualization/orbslam3_realtime_demo.py
```

These demos display extracted frames and update the saved trajectory over time. They are useful for presentation and explanation, but they are not live inference systems.

For ORB-SLAM3, `--sync-mode even` is useful for presentation because ORB-SLAM3 keyframes may be sparse or delayed when tracking fails.

## Strengths and Limitations

| Method | Strengths | Limitations |
| --- | --- | --- |
| DeepVO | Simple CSV outputs, dense predictions, easier Python workflow, useful learning-based baseline | Drift accumulation, domain shift, no loop closure, early checkpoint |
| ORB-SLAM3 | Classical SLAM baseline, TUM trajectory format, keyframe/map behavior, strong indoor result | More difficult macOS build, Pangolin viewer issue, approximate calibration, tracking instability outdoors |

## Final Interpretation

DeepVO and ORB-SLAM3 complement each other well for a semester project. DeepVO demonstrates a learning-based visual odometry pipeline, while ORB-SLAM3 demonstrates a classical monocular SLAM baseline. The results are strongest as an implementation and qualitative comparison project rather than a final accuracy benchmark, especially because custom videos do not have ground-truth trajectories.
