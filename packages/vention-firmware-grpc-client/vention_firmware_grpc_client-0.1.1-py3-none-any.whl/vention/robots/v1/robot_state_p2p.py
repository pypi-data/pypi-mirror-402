# This is an automatically generated file, please do not change
# gen by protobuf_to_pydantic[v0.3.3.1](https://github.com/so1n/protobuf_to_pydantic)
# Protobuf Version: 6.32.1 
# Pydantic Version: 2.11.10 
from .frame_p2p import Frame
from .frame_p2p import Twist
from .joint_position_p2p import JointPosition
from datetime import datetime
from enum import IntEnum
from google.protobuf.message import Message  # type: ignore
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
import typing

class RobotOperationalState(IntEnum):
    """
     Operational states of the robot
    """
    ROBOT_OPERATIONAL_STATE_UNSPECIFIED = 0
    ROBOT_OPERATIONAL_STATE_IDLE = 1
    ROBOT_OPERATIONAL_STATE_TRAJECTORY = 2
    ROBOT_OPERATIONAL_STATE_JOGGING = 3
    ROBOT_OPERATIONAL_STATE_FREEDRIVE = 4
    ROBOT_OPERATIONAL_STATE_STOPPING = 5
    ROBOT_OPERATIONAL_STATE_NOT_READY = 6


class RobotSafetyState(IntEnum):
    """
     Safety states of the robot
    """
    ROBOT_SAFETY_STATE_UNSPECIFIED = 0
    ROBOT_SAFETY_STATE_NORMAL = 1
    ROBOT_SAFETY_STATE_EMERGENCY_STOP = 2
    ROBOT_SAFETY_STATE_REDUCED_SPEED = 3
    ROBOT_SAFETY_STATE_RECOVERABLE_FAULT = 4


class RobotConnectionState(IntEnum):
    """
     Connection states of the robot
    """
    ROBOT_CONNECTION_STATE_UNSPECIFIED = 0
    ROBOT_CONNECTION_STATE_DISCONNECTED = 1
    ROBOT_CONNECTION_STATE_CONNECTING = 2
    ROBOT_CONNECTION_STATE_CONNECTED = 3

class JointStates(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    joint_position: JointPosition = Field(default_factory=JointPosition)

class GetJointStatesRequest(BaseModel):
    id: str = Field(default="")# ID of the robot to get joint position state from

class GetJointStatesResponse(BaseModel):
    joint_state: JointStates = Field(default_factory=JointStates)# Current joint position of the robot

class PositionState(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    joint_position: JointPosition = Field(default_factory=JointPosition)
    cartesian_pose: Frame = Field(default_factory=Frame)

class GetPositionStateRequest(BaseModel):
    id: str = Field(default="")# ID of the robot to get robot joint and Cartesian position feedback

class GetPositionStateResponse(BaseModel):
    position_state: PositionState = Field(default_factory=PositionState)# Current joint and Cartesian position feedback

class DisableControllerRequest(BaseModel):
    id: str = Field(default="")

class DisableControllerResponse(BaseModel):
    success: bool = Field(default=False)
    message: str = Field(default="")# Optional message for additional context

class StartControllerRequest(BaseModel):
    id: str = Field(default="")

class StartControllerResponse(BaseModel):
    success: bool = Field(default=False)
    message: str = Field(default="")# Optional message for additional context

class SetToNormalRequest(BaseModel):
    id: str = Field(default="")

class SetToNormalResponse(BaseModel):
    success: bool = Field(default=False)

class SetAllToNormalRequest(BaseModel):
    """
     Set all robots to normal state.
 This operation should only be called after an emergency stop is cleared and robots are
 in a safe state to resume operation.
    """

class SetAllToNormalResponse(BaseModel):
    """
     Response for SetAllToNormalRequest
    """

    id_success: typing.List[str] = Field(default_factory=list)# IDs of robots successfully set to normal
    id_failed: typing.List[str] = Field(default_factory=list)# IDs of robots that failed to set to normal

class SetToFreedriveRequest(BaseModel):
    id: str = Field(default="")
    enable: bool = Field(default=False)

class SetToFreedriveResponse(BaseModel):
    success: bool = Field(default=False)

class RobotStates(BaseModel):
    model_config = ConfigDict(validate_default=True)
    operational_state: RobotOperationalState = Field(default=0)
    safety_state: RobotSafetyState = Field(default=0)
    connection_state: RobotConnectionState = Field(default=0)
    timestamp: datetime = Field(default_factory=datetime.now)

class GetRobotStatesRequest(BaseModel):
    id: str = Field(default="")# ID of the robot to get robot state from

class GetRobotStatesResponse(BaseModel):
    robot_state: RobotStates = Field(default_factory=RobotStates)# Current state of the robot

class RobotStatesStreamRequest(BaseModel):
    id: str = Field(default="")

class CommandState(BaseModel):
    timestamp_eval: datetime = Field(default_factory=datetime.now)# Epoch time of evluated command (ideal)
    timestamp_actual: datetime = Field(default_factory=datetime.now)# Epoch time at which the command was actually prepared
    joint_position: typing.List[float] = Field(default_factory=list)# Joint positions in radians
    joint_velocity: typing.List[float] = Field(default_factory=list)# Joint velocities in radians/sec
    joint_acceleration: typing.List[float] = Field(default_factory=list)# Joint accelerations in radians/sec^2
    cartesian_pose: Frame = Field(default_factory=Frame)# TCP pose with position in meters
    cartesian_velocity: Twist = Field(default_factory=Twist)# TCP velocity in meters/sec and radians/sec
    cartesian_acceleration: Twist = Field(default_factory=Twist)# TCP acceleration in meters/sec^2 and radians/sec^2
    manipulability_index: float = Field(default=0.0)# Manipulability index, volume of the manipulability ellipsoid

class GetCommandStateRequest(BaseModel):
    id: str = Field(default="")# ID of the robot to get command state from

class GetCommandStateResponse(BaseModel):
    command_state: CommandState = Field(default_factory=CommandState)# Current command state of the robot

class CommandStateStreamRequest(BaseModel):
    id: str = Field(default="")# ID of the robot to stream command states from
    max_frequency_hz: float = Field(default=0.0)# Maximum frequency of the stream in Hz (0 = no limit)

class AllSafetyStatesStreamRequest(BaseModel):
    """
     Request message for AllSafetyStatesStream service
    """

    update_frequency_hz: float = Field(default=0.0)# Frequency at which to receive safety state updates, minimum 0.5 Hz, maximum 50 Hz

class AllSafetyStates(BaseModel):
    """
     Response message for AllSafetyStatesStream service
    """

    timestamp: datetime = Field(default_factory=datetime.now)# Timestamp of the safety states
    safety_states: "typing.Dict[str, RobotSafetyState]" = Field(default_factory=dict)# Map of robot ID to its safety state
