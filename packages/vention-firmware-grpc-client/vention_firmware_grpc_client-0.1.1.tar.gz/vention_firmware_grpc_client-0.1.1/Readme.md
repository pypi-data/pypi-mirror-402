# Vention Firmware gRPC Client

A Python gRPC client for calling Vention firmware endpoints. It is commonly referred to as Vention Robot Motion Control Stack (VRMCS)

## Features

- **Robot Management**: Register and manage robots
- **Motion Control**: Execute movements, plan trajectories, and control robot motion
- **Kinematics**: Forward and inverse kinematics operations
- **Real-time Streaming**: Stream robot states, joint states, position data, and alarms
- **Operating Modes**: Control normal and freedrive modes
- **TCP/Payload Configuration**: Set tool center point and payload properties

## Installation

Install the package using pip:

```bash
pip install vention-firmware-grpc-client
```

## Quick Start

```python
from vrmcs.client import VRMCSClient
from vrmcs.types import MoveRequest, JointPosition

# Connect to the VRMCS server
client = VRMCSClient("localhost:50550")

# List available robots
robots = client.list_robots()
for robot in robots.robots:
    print(f"Robot ID: {robot.id}")
    print(f"Name: {robot.name}")
    print(f"Type: {robot.robot_type}")

# Use types for type-safe requests
move_request = MoveRequest(
    robot_id="my_robot",
    joint_position=JointPosition(positions=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
)
response = client.move(move_request)
```

## Requirements

- Python >= 3.10

## License

Copyright © Vention
