# This is an automatically generated file, please do not change
# gen by protobuf_to_pydantic[v0.3.3.1](https://github.com/so1n/protobuf_to_pydantic)
# Protobuf Version: 6.32.1 
# Pydantic Version: 2.11.10 
from .ethercat_address_p2p import EthercatAddress
from .joint_trajectory_point_p2p import JointTrajectoryPoint
from .plan_request_p2p import PlanResultCode
from datetime import datetime
from enum import IntEnum
from google.protobuf.message import Message  # type: ignore
from protobuf_to_pydantic.customer_validator import check_one_of
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import model_validator
import typing

class GcodeResultCode(IntEnum):
    GCODE_RESULT_CODE_UNSPECIFIED = 0
    GCODE_RESULT_CODE_SUCCESS = 1
    GCODE_RESULT_CODE_PARSER_FAILED = 2
    GCODE_RESULT_CODE_PLANNER_FAILED = 3
    GCODE_RESULT_CODE_MOTOR_CONFLICT = 4
    GCODE_RESULT_CODE_MOTOR_NOT_READY = 5
    GCODE_RESULT_CODE_INVALID_CONFIGURATION = 6
    GCODE_RESULT_CODE_ID_NOT_FOUND = 7
    GCODE_RESULT_CODE_IN_MOTION = 8


class ParserResultCode(IntEnum):
    PARSER_RESULT_CODE_UNSPECIFIED = 0
    PARSER_RESULT_CODE_SUCCESS = 1
    PARSER_RESULT_CODE_FAILED = 2
    PARSER_RESULT_CODE_FILE_ERROR = 3
    PARSER_RESULT_CODE_INTERNAL_ERROR = 4
    PARSER_RESULT_CODE_BAD_SYNTAX = 5
    PARSER_RESULT_CODE_BAD_ARGUMENT = 6
    PARSER_RESULT_CODE_UNRECOGNIZED_COMMAND = 7


class GcodeRuntimeCode(IntEnum):
    GCODE_RUNTIME_CODE_UNSPECIFIED = 0
    GCODE_RUNTIME_CODE_LIMIT_SWITCH_TRIGGERED = 1
    GCODE_RUNTIME_CODE_MACHINE_NOT_OPERATIONAL = 2
    GCODE_RUNTIME_CODE_POSITION_ERROR_ABOVE_THRESHOLD = 3


class GcodePathState(IntEnum):#  current execution state of a gcode path
    GCODE_PATH_STATE_UNSPECIFIED = 0
    GCODE_PATH_STATE_IDLE = 1
    GCODE_PATH_STATE_RUNNING = 2
    GCODE_PATH_STATE_STOPPING = 3
    GCODE_PATH_STATE_ERROR = 4

class GcodeAxisMap(BaseModel):
    x: typing.Optional[EthercatAddress] = Field(default_factory=EthercatAddress)
    y: typing.Optional[EthercatAddress] = Field(default_factory=EthercatAddress)
    z: typing.Optional[EthercatAddress] = Field(default_factory=EthercatAddress)
    a: typing.Optional[EthercatAddress] = Field(default_factory=EthercatAddress)
    b: typing.Optional[EthercatAddress] = Field(default_factory=EthercatAddress)
    c: typing.Optional[EthercatAddress] = Field(default_factory=EthercatAddress)

class GcodeMessage(BaseModel):
    _one_of_dict = {"GcodeMessage.code": {"fields": {"gcode_runtime_code", "parser_result_code", "planner_result_code"}}}
    one_of_validator = model_validator(mode="before")(check_one_of)
    model_config = ConfigDict(validate_default=True)
    timestamp: datetime = Field(default_factory=datetime.now)
    parser_result_code: ParserResultCode = Field(default=0)
    planner_result_code: PlanResultCode = Field(default=0)
    gcode_runtime_code: GcodeRuntimeCode = Field(default=0)# limit switch being hit, etc.
    line_number: int = Field(default=0)
    description: typing.Optional[str] = Field(default="")

class MoveGcodeRequest(BaseModel):
    _one_of_dict = {"MoveGcodeRequest.gcode_source": {"fields": {"gcode_bytes", "gcode_path", "gcode_string"}}, "MoveGcodeRequest.robot": {"fields": {"axis_map", "id"}}}
    one_of_validator = model_validator(mode="before")(check_one_of)
    id: str = Field(default="")
    axis_map: GcodeAxisMap = Field(default_factory=GcodeAxisMap)
    gcode_string: str = Field(default="")
    gcode_path: str = Field(default="")
    gcode_bytes: bytes = Field(default=b"")

class MoveGcodeResponse(BaseModel):
    model_config = ConfigDict(validate_default=True)
    result_code: GcodeResultCode = Field(default=0)
    messages: typing.List[GcodeMessage] = Field(default_factory=list)
    duration: float = Field(default=0.0)
    id: typing.Optional[str] = Field(default="")

class PlanGcodeRequest(BaseModel):
    _one_of_dict = {"PlanGcodeRequest.gcode_source": {"fields": {"gcode_bytes", "gcode_path", "gcode_string"}}, "PlanGcodeRequest.robot": {"fields": {"axis_map", "id"}}}
    one_of_validator = model_validator(mode="before")(check_one_of)
    id: str = Field(default="")
    axis_map: GcodeAxisMap = Field(default_factory=GcodeAxisMap)
    initial_joint_position: typing.List[float] = Field(default_factory=list)
    gcode_string: str = Field(default="")
    gcode_path: str = Field(default="")
    gcode_bytes: bytes = Field(default=b"")
    sampling_time: float = Field(default=0.0)# Time between samples in seconds

class PlanGcodeResponse(BaseModel):
    model_config = ConfigDict(validate_default=True)
    result_code: GcodeResultCode = Field(default=0)
    messages: typing.List[GcodeMessage] = Field(default_factory=list)
    duration: float = Field(default=0.0)
    joint_trajectory_points: typing.List[JointTrajectoryPoint] = Field(default_factory=list)

class GcodeStatusStreamRequest(BaseModel):
    id: str = Field(default="")

class GCodeStatus(BaseModel):
    model_config = ConfigDict(validate_default=True)
    timestamp: datetime = Field(default_factory=datetime.now)
    state: GcodePathState = Field(default=0)
    progress: float = Field(default=0.0)# Approximate completion percentage of the path, in terms of total distance travelled.
    line_number: int = Field(default=0)# Current line number from the G-code String or file being executed
    feedrate: float = Field(default=0.0)# in units/min. This is the actual feedrate, already taking into account the feedrate_multiplier.
    feedrate_multiplier: float = Field(default=0.0)
    message: typing.List[GcodeMessage] = Field(default_factory=list)
