# This is an automatically generated file, please do not change
# gen by protobuf_to_pydantic[v0.3.3.1](https://github.com/so1n/protobuf_to_pydantic)
# Protobuf Version: 6.32.1 
# Pydantic Version: 2.11.10 
from .frame_p2p import Twist
from enum import IntEnum
from google.protobuf.message import Message  # type: ignore
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
import typing

class JogResultCode(IntEnum):
    JOG_RESULT_CODE_UNSPECIFIED = 0
    JOG_RESULT_CODE_OK = 1
    JOG_RESULT_CODE_ERROR = 2

class JogJointRequest(BaseModel):
    id: str = Field(default="")
    joint_velocity: typing.List[float] = Field(default_factory=list)

class JogJointResponse(BaseModel):
    model_config = ConfigDict(validate_default=True)
    result_code: JogResultCode = Field(default=0)

class JogCartesianRequest(BaseModel):
    id: str = Field(default="")
    velocity: Twist = Field(default_factory=Twist)

class JogCartesianResponse(BaseModel):
    model_config = ConfigDict(validate_default=True)
    result_code: JogResultCode = Field(default=0)
