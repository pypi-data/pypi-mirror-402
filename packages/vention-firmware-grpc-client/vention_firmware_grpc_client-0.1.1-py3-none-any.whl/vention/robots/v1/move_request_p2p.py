# This is an automatically generated file, please do not change
# gen by protobuf_to_pydantic[v0.3.3.1](https://github.com/so1n/protobuf_to_pydantic)
# Protobuf Version: 6.32.1 
# Pydantic Version: 2.11.10 
from .move_p2p import MoveSegment
from .plan_request_p2p import PlanResultCode
from enum import IntEnum
from google.protobuf.message import Message  # type: ignore
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
import typing

class MoveResultCode(IntEnum):
    MOVE_RESULT_CODE_UNSPECIFIED = 0
    MOVE_RESULT_CODE_SUCCESS = 1
    MOVE_RESULT_CODE_FAILURE = 2
    MOVE_RESULT_CODE_CANCELLED_BY_USER = 3
    MOVE_RESULT_CODE_NETWORK_ERROR = 4
    MOVE_RESULT_CODE_COLLAB_VIOLATION = 5
    MOVE_RESULT_CODE_SAFETY_TRANSITION = 6
    MOVE_RESULT_CODE_MODE_TRANSITION = 7
    MOVE_RESULT_CODE_ROBOT_NOT_FOUND = 8
    MOVE_RESULT_CODE_START_POSITION_MISMATCH = 9

class MoveRequest(BaseModel):
    id: str = Field(default="")
    segments: typing.List[MoveSegment] = Field(default_factory=list)

class MoveResponse(BaseModel):
    model_config = ConfigDict(validate_default=True)
    result_code: PlanResultCode = Field(default=0)
    duration: float = Field(default=0.0)# Duration of the move in seconds
    error_segment: typing.Optional[int] = Field(default=0)# Segment id in which failure occurred (if any)

class WaitForMoveCompletionRequest(BaseModel):
    id: str = Field(default="")

class WaitForMoveCompletionResponse(BaseModel):
    model_config = ConfigDict(validate_default=True)
    result_code: MoveResultCode = Field(default=0)
    error_segment: int = Field(default=0)# Segment id in which failure occurred (if any)
