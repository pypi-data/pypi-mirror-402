# SynriaRD: Synria Robot Descriptions

English | [中文](README_CN.md)

This repository contains URDF (Unified Robot Description Format) and MJCF (MuJoCo Modeling Format) models for Synria robotic platforms.

## Repository Structure

```
├── synriard
│   ├── meshes
│   │   ├── Alicia_D_v5_5
│   │   ├── Alicia_D_v5_6
│   │   ├── Alicia_M_v1_0
│   │   ├── Alicia_M_v1_1
│   │   ├── Bessica_D_v1_0
│   │   ├── Bessica_D_v1_1
│   │   └── Bessica_M_v1_0
│   ├── mjcf
│   │   ├── Alicia_D_v5_5
│   │   ├── Alicia_D_v5_6
│   │   ├── Alicia_M_v1_1
│   │   ├── Bessica_D_v1_0
│   │   ├── Bessica_D_v1_1
│   │   └── Bessica_M_v1_0
│   └── urdf
│       ├── Alicia_D_v5_5
│       ├── Alicia_D_v5_6
│       ├── Alicia_M_v1_0
│       ├── Alicia_M_v1_1
│       ├── Bessica_D_v1_0
│       ├── Bessica_D_v1_1
│       └── Bessica_M_v1_0
```

## Naming Convention

All model files follow a unified naming format: `{name}_{version}_{variant}.{ext}`

- **name**: Robot name (e.g., `Alicia_D`, `Alicia_M`, `Bessica_D`, `Bessica_M`)
- **version**: Version number (e.g., `v5_5`, `v5_6`, `v1_0`, `v1_1`)
- **variant**: Variant identifier
  - For robots with grippers (Alicia_D, Alicia_M): `gripper_{size}` (e.g., `gripper_50mm`, `gripper_100mm`)
  - For other variants (Bessica_D): Direct variant name (e.g., `covered`, `skeleton`, `skeleton_interactive`)
- **ext**: File extension (`.urdf` or `.xml`)

### Examples

- `Alicia_D_v5_6_gripper_50mm.urdf` - Alicia_D v5.6 version with 50mm gripper
- `Alicia_D_v5_6_gripper_100mm.urdf` - Alicia_D v5.6 version with 100mm gripper
- `Alicia_M_v1_1_gripper_100mm.urdf` - Alicia_M v1.1 version with 100mm gripper
- `Bessica_D_v1_0_covered.urdf` - Bessica_D v1.0 version, covered variant
- `Bessica_D_v1_1_skeleton.urdf` - Bessica_D v1.1 version, skeleton variant
- `Bessica_D_v1_0_covered_interactive.xml` - Bessica_D v1.0 version, covered interactive variant (MJCF)

### Usage API

```python
from synriard import get_model_path, list_available_models

# Get model path
urdf_path = get_model_path("Alicia_D", version="v5_6", variant="gripper_50mm")
mjcf_path = get_model_path("Alicia_D", version="v5_6", variant="gripper_50mm", model_format="mjcf")

# List all available models
print(list_available_models(model_format="urdf"))
print(list_available_models(model_format="urdf", show_path=True))
```

## Products

### Alicia-D 
- **Description**: Agile manipulation arm
- **DOF**: 6
- **Gripper Configurations**: 50mm and 100mm
- **Versions**: v5.5, v5.6
- **Variants**: 
  - `gripper_50mm` - 50mm gripper configuration
  - `gripper_100mm` - 100mm gripper configuration
  - `leader` - Leader arm configuration (v5.6 only)
  - `vertical_50mm` - Vertical 50mm configuration (v5.6 only)
- **Locations**: 
  - [`Alicia_D_v5_5`](synriard/urdf/Alicia_D_v5_5)
  - [`Alicia_D_v5_6`](synriard/urdf/Alicia_D_v5_6)

### Alicia-M 
- **Description**: Cloud-powered robotic arm
- **DOF**: 6
- **Versions**: v1.0, v1.1
- **Gripper Configuration**: 100mm
- **Locations**: 
  - [`Alicia_M_v1_0`](synriard/urdf/Alicia_M_v1_0)
  - [`Alicia_M_v1_1`](synriard/urdf/Alicia_M_v1_1)

### Bessica-D 
- **Description**: Dual-arm humanoid robot
- **DOF**: 14 (Dual 7-DOF arms)
- **Versions**: v1.0, v1.1
- **Appearance**: Skeleton and covered versions

#### Skeleton Version
- **v1.0 URDF**: [`Bessica_D_v1_0_skeleton.urdf`](synriard/urdf/Bessica_D_v1_0/Bessica_D_v1_0_skeleton.urdf)
- **v1.0 MuJoCo XML**: [`Bessica_D_v1_0_skeleton.xml`](synriard/mjcf/Bessica_D_v1_0/Bessica_D_v1_0_skeleton.xml)
- **v1.1 URDF**: [`Bessica_D_v1_1_skeleton.urdf`](synriard/urdf/Bessica_D_v1_1/Bessica_D_v1_1_skeleton.urdf)
- **v1.1 MuJoCo XML**: [`Bessica_D_v1_1_skeleton.xml`](synriard/mjcf/Bessica_D_v1_1/Bessica_D_v1_1_skeleton.xml)
- **v1.1 MuJoCo XML (Interactive)**: [`Bessica_D_v1_1_skeleton_interactive.xml`](synriard/mjcf/Bessica_D_v1_1/Bessica_D_v1_1_skeleton_interactive.xml)

#### Covered Version (v1.0 only)
- **URDF**: [`Bessica_D_v1_0_covered.urdf`](synriard/urdf/Bessica_D_v1_0/Bessica_D_v1_0_covered.urdf)
- **MuJoCo XML**: [`Bessica_D_v1_0_covered.xml`](synriard/mjcf/Bessica_D_v1_0/Bessica_D_v1_0_covered.xml)
- **MuJoCo XML (Interactive)**: [`Bessica_D_v1_0_covered_interactive.xml`](synriard/mjcf/Bessica_D_v1_0/Bessica_D_v1_0_covered_interactive.xml)

### Bessica-M 
- **Description**: Dual-arm humanoid robot (M series)
- **DOF**: 14 (Dual 7-DOF arms)
- **Version**: v1.0
- **Location**: [`Bessica_M_v1_0`](synriard/urdf/Bessica_M_v1_0)

## Adding New Robot Models

After adding new robot models, run the automation script to automatically generate the required `__init__.py` files:

```bash
# 1. Add model files to the corresponding directory
mkdir -p synriard/mjcf/RobotName_v1_0
cp RobotName_v1_0_gripper_100mm.xml synriard/mjcf/RobotName_v1_0/

# 2. Run the automation script
python3 auto_generate_init.py

# The script will automatically:
# - Generate __init__.py for each robot directory
# - Update parent directory __init__.py to register all robots
```

Script options:
- `--format mjcf|urdf|all`: Specify the format to process (default: all)
- `--synriard-path PATH`: Specify the synriard directory path (default: auto-detect)

## Supported Simulation Environments

- ROS/ROS2 (via URDF)
- MuJoCo (via MJCF)
- Gazebo (via URDF)
- PyBullet (via URDF)
- Isaac Sim (via URDF/MJCF)
