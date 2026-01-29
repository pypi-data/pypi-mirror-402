# This is an automatically generated file, please do not change
# gen by protobuf_to_pydantic[v0.3.3.1](https://github.com/so1n/protobuf_to_pydantic)
# Protobuf Version: 6.32.1 
# Pydantic Version: 2.11.10 
from .joint_trajectory_point_p2p import JointTrajectoryPoint
from .move_p2p import MoveSegment
from enum import IntEnum
from google.protobuf.message import Message  # type: ignore
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
import typing

class PlanResultCode(IntEnum):
    PLAN_RESULT_CODE_UNSPECIFIED = 0
    PLAN_RESULT_CODE_SUCCESS = 1
    PLAN_RESULT_CODE_FAILED = 2
    PLAN_RESULT_CODE_BAD_INPUT = 3
    PLAN_RESULT_CODE_EXCEEDS_JOINT_LIMITS = 4
    PLAN_RESULT_CODE_SINGULARITY = 5
    PLAN_RESULT_CODE_SELF_COLLISION = 6
    PLAN_RESULT_CODE_IK_NOT_FOUND = 7
    PLAN_RESULT_CODE_ROBOT_NOT_FOUND = 8
    PLAN_RESULT_CODE_BLEND_TOO_TIGHT = 9
    PLAN_RESULT_CODE_BLEND_OVERLAP = 10
    PLAN_RESULT_CODE_ROBOT_IN_MOTION = 11
    PLAN_RESULT_CODE_TYPE_CONSTRAINTS_MISMATCH = 12
    PLAN_RESULT_CODE_BLEND_ERROR = 13
    PLAN_RESULT_CODE_BLEND_ENDPOINT_NOT_STEADY = 14

class PlanRequest(BaseModel):
    id: str = Field(default="")
    initial_joint_position: typing.List[float] = Field(default_factory=list)# Initial joint positions in radians
    segments: typing.List[MoveSegment] = Field(default_factory=list)
    sampling_time: float = Field(default=0.0)# Time between samples in seconds

class PlanResponse(BaseModel):
    model_config = ConfigDict(validate_default=True)
    result_code: PlanResultCode = Field(default=0)
    duration: float = Field(default=0.0)
    joint_trajectory_points: typing.List[JointTrajectoryPoint] = Field(default_factory=list)
    error_segment: typing.Optional[int] = Field(default=0)# Segment id in which failure occurred (if any)
