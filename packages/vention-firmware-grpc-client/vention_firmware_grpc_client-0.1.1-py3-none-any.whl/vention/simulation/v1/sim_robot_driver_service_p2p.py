# This is an automatically generated file, please do not change
# gen by protobuf_to_pydantic[v0.3.3.1](https://github.com/so1n/protobuf_to_pydantic)
# Protobuf Version: 6.32.1 
# Pydantic Version: 2.11.10 
from .joint_trajectory_point_p2p import JointTrajectoryPoint
from .move_request_p2p import MoveResultCode
from .robot_state_p2p import RobotOperationalState
from datetime import datetime
from enum import IntEnum
from google.protobuf.message import Message  # type: ignore
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
import typing

class RobotSimulationDriverState(IntEnum):
    DRIVER_STATE_DISCONNECTED = 0
    DRIVER_STATE_ESTOP = 1
    DRIVER_STATE_RECOVERABLE_FAULT = 2
    DRIVER_STATE_NOT_READY = 3
    DRIVER_STATE_NORMAL = 4
    DRIVER_STATE_REDUCED = 5
    DRIVER_STATE_FREEDRIVE = 6

class SimRobotDriverServiceRequest(BaseModel):
    id: str = Field(default="")

class RobotSimulationControlLoopPeriod(BaseModel):
    period_ms: int = Field(default=0)# Control loop period in milliseconds

class RobotSimulationControlResponse(BaseModel):
    success: bool = Field(default=False)
    message: str = Field(default="")# Optional message for additional context

class StartTrajectoryRequest(BaseModel):
    points: typing.List[JointTrajectoryPoint] = Field(default_factory=list)
    id: str = Field(default="")

class RegisterTrajectoryCompletionCallbackResponse(BaseModel):
    model_config = ConfigDict(validate_default=True)
    result_code: MoveResultCode = Field(default=0)
    operational_state: RobotOperationalState = Field(default=0)
    timestamp: datetime = Field(default_factory=datetime.now)

class RobotSimulationDriverStateResponse(BaseModel):
    model_config = ConfigDict(validate_default=True)
    state: RobotSimulationDriverState = Field(default=0)
