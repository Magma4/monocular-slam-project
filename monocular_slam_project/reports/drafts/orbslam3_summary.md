# ORB-SLAM3 Summary

## Overview

ORB-SLAM3 is the classical feature-based monocular SLAM baseline for this semester project. It is used to compare a traditional SLAM pipeline against the DeepVO learning-based visual odometry workflow.

For custom experiments, ORB-SLAM3 was run on existing extracted frame sequences:

```text
data/custom/extracted_frames/indoor_loop/
data/custom/extracted_frames/outdoor_loop/
data/custom/extracted_frames/outdoor_loop2/
```

ORB-SLAM3 outputs are saved in TUM trajectory format:

```text
timestamp tx ty tz qx qy qz qw
```

## macOS Setup and Headless Workaround

ORB-SLAM3 was built locally on a MacBook M4 after minimal macOS / Apple Silicon compatibility work. Pangolin required special handling because the Homebrew package named `pangolin` was not the C++ Pangolin dependency expected by ORB-SLAM3.

The Pangolin viewer crashed on macOS with a main-thread GUI error:

```text
nextEventMatchingMask should only be called from the Main Thread!
```

The crash occurred inside the viewer path, not in the frame-input path. To keep monocular tracking usable, the project uses a headless workflow:

```bash
--no-viewer
```

Headless mode disables the Pangolin viewer but still allows ORB-SLAM3 to track and save trajectory files.

## Indoor Custom Sequence Result

| Item | Path / Value |
| --- | --- |
| Input frames | `data/custom/extracted_frames/indoor_loop/` |
| Trajectory | `outputs/trajectories/orb_slam3/indoor_loop/keyframe_trajectory_tum.txt` |
| Plot | `outputs/plots/orb_slam3/indoor_loop_trajectory.png` |
| Keyframe poses saved | 523 |
| Log | `outputs/logs/orb_slam3/indoor_loop_mono_kitti_old.log` |

The indoor result is the strongest custom ORB-SLAM3 result. It produced the most keyframe poses and a usable trajectory plot.

## Outdoor Custom Sequence Result

| Item | Path / Value |
| --- | --- |
| Input frames | `data/custom/extracted_frames/outdoor_loop/` |
| Settings | `configs/orbslam3_custom_1280x720.yaml` |
| Trajectory | `outputs/trajectories/orb_slam3/outdoor_loop/keyframe_trajectory_tum.txt` |
| Plot | `outputs/plots/orb_slam3/outdoor_loop_trajectory.png` |
| Keyframe poses saved | 182 |
| Log | `outputs/logs/orb_slam3/outdoor_loop_mono_kitti_old.log` |

The outdoor result is shorter and less stable than the indoor result. It is useful for discussing tracking sensitivity under more difficult custom-video conditions.

## Outdoor Loop 2 Result

| Item | Path / Value |
| --- | --- |
| Input frames | `data/custom/extracted_frames/outdoor_loop2/` |
| Settings | `configs/orbslam3_custom_outdoor_loop2_1280x2276.yaml` |
| Trajectory | `outputs/trajectories/orb_slam3/outdoor_loop2/keyframe_trajectory_tum.txt` |
| Plot | `outputs/plots/orb_slam3/outdoor_loop2_trajectory.png` |
| Keyframe poses saved | 451 |
| Log | `outputs/logs/orb_slam3/outdoor_loop2_mono_kitti_old.log` |

`outdoor_loop2` is a large portrait-oriented sequence. ORB-SLAM3 saved a valid trajectory, but the log shows many tracking failures and map resets. This makes it a useful robustness example rather than a clean tracking result.

## Observed Strengths

- ORB-SLAM3 provides a classical monocular SLAM baseline for comparison against DeepVO.
- It saves standard TUM trajectory files that are easy to parse and plot.
- Headless mode allows the workflow to run reliably on macOS despite Pangolin viewer issues.
- The indoor sequence produced a usable and relatively dense keyframe trajectory.
- The method can recover usable outputs on harder outdoor sequences, though with reduced stability.

## Observed Limitations

- Pangolin viewer mode is unreliable on macOS because of Cocoa main-thread GUI handling.
- Custom settings use approximate intrinsics rather than calibrated camera parameters.
- Monocular SLAM trajectory scale is arbitrary without external scale information.
- Outdoor custom videos are more sensitive to blur, lighting, texture, rotation, and camera calibration mismatch.
- `outdoor_loop2` produced repeated local-map tracking failures and map resets, showing reduced robustness on difficult custom footage.

## Output Organization

```text
outputs/
├── logs/
│   └── orb_slam3/
├── plots/
│   └── orb_slam3/
│       ├── indoor_loop_trajectory.png
│       ├── outdoor_loop_trajectory.png
│       └── outdoor_loop2_trajectory.png
└── trajectories/
    └── orb_slam3/
        ├── indoor_loop/keyframe_trajectory_tum.txt
        ├── outdoor_loop/keyframe_trajectory_tum.txt
        └── outdoor_loop2/keyframe_trajectory_tum.txt
```

## Project Role

ORB-SLAM3 serves as the monocular SLAM baseline. DeepVO represents learning-based visual odometry, while ORB-SLAM3 represents feature-based SLAM with mapping and relocalization behavior, although this project primarily evaluates exported trajectories qualitatively.
