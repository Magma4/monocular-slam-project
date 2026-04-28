# ORB-SLAM3 Summary

## Overview

ORB-SLAM3 was added as the classical monocular SLAM baseline for this semester project. The goal was to compare a feature-based SLAM pipeline against the DeepVO visual odometry workflow already implemented in the project.

For the custom video experiments, ORB-SLAM3 was run in monocular mode on existing extracted frame sequences:

- `data/custom/extracted_frames/indoor_loop/`
- `data/custom/extracted_frames/outdoor_loop/`

The runs produced keyframe trajectory outputs in TUM format:

```text
timestamp tx ty tz qx qy qz qw
```

## macOS Setup and Headless Workaround

ORB-SLAM3 was built successfully on a MacBook M4 after applying minimal Apple Silicon/macOS compatibility fixes. Pangolin was built locally because the Homebrew `pangolin` package was not the C++ Pangolin library expected by ORB-SLAM3.

The Pangolin viewer crashed on macOS with a main-thread error:

```text
nextEventMatchingMask should only be called from the Main Thread!
```

This crash occurred inside the Pangolin/ORB-SLAM3 viewer thread, not in the frame input pipeline. To keep the workflow stable, the monocular KITTI-style executable was patched with an explicit headless option:

```bash
--no-viewer
```

With `--no-viewer`, ORB-SLAM3 still performs tracking and saves trajectory files, but it does not open the Pangolin map viewer.

## Indoor Custom Sequence Result

The indoor sequence produced a usable ORB-SLAM3 keyframe trajectory.

| Item | Path / Value |
| --- | --- |
| Input frames | `data/custom/extracted_frames/indoor_loop/` |
| Trajectory | `outputs/trajectories/orb_slam3/indoor_loop/keyframe_trajectory_tum.txt` |
| Plot | `outputs/plots/orb_slam3/indoor_loop_trajectory.png` |
| Keyframe poses saved | 523 |
| Log | `outputs/logs/orb_slam3/indoor_loop_mono_kitti_old.log` |

The indoor result is the stronger of the two custom ORB-SLAM3 runs. It saved more keyframe poses and produced a clearer trajectory plot.

## Outdoor Custom Sequence Result

The outdoor sequence initially produced an empty trajectory when using the KITTI camera settings. After switching to a custom 1280x720 settings file, ORB-SLAM3 produced a usable TUM trajectory.

| Item | Path / Value |
| --- | --- |
| Input frames | `data/custom/extracted_frames/outdoor_loop/` |
| Custom settings | `configs/orbslam3_custom_1280x720.yaml` |
| Trajectory | `outputs/trajectories/orb_slam3/outdoor_loop/keyframe_trajectory_tum.txt` |
| Plot | `outputs/plots/orb_slam3/outdoor_loop_trajectory.png` |
| Keyframe poses saved | 182 |
| Log | `outputs/logs/orb_slam3/outdoor_loop_mono_kitti_old.log` |

The outdoor trajectory is shorter and less stable than the indoor result. The log shows repeated local-map tracking failures, which suggests the outdoor sequence was harder for feature-based monocular tracking. Likely causes include camera motion, changing lighting, motion blur, lower feature consistency, and approximate camera calibration.

## Observed Strengths

- ORB-SLAM3 can run as a classical monocular SLAM baseline on the same custom frame sequences used elsewhere in the project.
- The output trajectory format is standard TUM text, which is easy to parse, plot, and compare.
- Headless mode allows reliable execution on macOS without the Pangolin viewer crash.
- The indoor sequence produced a usable trajectory with 523 saved keyframe poses.
- The outdoor sequence produced a usable trajectory after using a more appropriate custom settings file.

## Observed Limitations

- Pangolin viewer mode was not reliable on macOS because of Cocoa main-thread handling, so the project used headless execution.
- The custom settings file uses approximate camera intrinsics, not a true camera calibration.
- Monocular SLAM has arbitrary scale unless external scale information is provided.
- The outdoor result is less stable and contains fewer keyframes than the indoor result.
- ORB-SLAM3 is sensitive to motion blur, low texture, rapid rotations, lighting changes, and incorrect camera parameters.

## Output Organization

ORB-SLAM3 outputs are organized as follows:

```text
outputs/
├── logs/
│   └── orb_slam3/
│       ├── indoor_loop_mono_kitti_old.log
│       └── outdoor_loop_mono_kitti_old.log
├── plots/
│   └── orb_slam3/
│       ├── indoor_loop_trajectory.png
│       └── outdoor_loop_trajectory.png
└── trajectories/
    └── orb_slam3/
        ├── indoor_loop/
        │   ├── keyframe_trajectory_tum.txt
        │   ├── kitti_input/
        │   └── run_command.txt
        └── outdoor_loop/
            ├── keyframe_trajectory_tum.txt
            ├── kitti_input/
            └── run_command.txt
```

## Project Role

This ORB-SLAM3 workflow serves as the monocular SLAM baseline for comparison against DeepVO. DeepVO represents the learning-based visual odometry side of the project, while ORB-SLAM3 represents the feature-based SLAM side.
