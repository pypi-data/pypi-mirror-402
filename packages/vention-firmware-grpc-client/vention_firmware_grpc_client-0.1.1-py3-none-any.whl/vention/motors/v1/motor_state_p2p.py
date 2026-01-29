# This is an automatically generated file, please do not change
# gen by protobuf_to_pydantic[v0.3.3.1](https://github.com/so1n/protobuf_to_pydantic)
# Protobuf Version: 6.32.1 
# Pydantic Version: 2.11.10 
from .ethercat_address_p2p import EthercatAddress
from enum import IntEnum
from google.protobuf.message import Message  # type: ignore
from protobuf_to_pydantic.customer_validator import check_one_of
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import model_validator

class StreamMode(IntEnum):
    """
     The enum values come from the CiA402 modes of operation
    """
    STREAM_MODE_UNSPECIFIED = 0
    STREAM_POSITION = 8
    STREAM_VELOCITY = 9
    STREAM_TORQUE = 10

class SetToNormalRequest(BaseModel):
    _one_of_dict = {"SetToNormalRequest.identifier": {"fields": {"id", "motor_address"}}}
    one_of_validator = model_validator(mode="before")(check_one_of)
    motor_address: EthercatAddress = Field(default_factory=EthercatAddress)
    id: str = Field(default="")

class SetToNormalResponse(BaseModel):
    success: bool = Field(default=False)
    message: str = Field(default="")

class StartMotionStreamRequest(BaseModel):
    _one_of_dict = {"StartMotionStreamRequest.identifier": {"fields": {"id", "motor_address"}}}
    one_of_validator = model_validator(mode="before")(check_one_of)
    model_config = ConfigDict(validate_default=True)
    motor_address: EthercatAddress = Field(default_factory=EthercatAddress)
    id: str = Field(default="")
    mode: StreamMode = Field(default=0)

class StartMotionStreamResponse(BaseModel):
    success: bool = Field(default=False)
    message: str = Field(default="")

class StopMotionStreamRequest(BaseModel):
    _one_of_dict = {"StopMotionStreamRequest.identifier": {"fields": {"id", "motor_address"}}}
    one_of_validator = model_validator(mode="before")(check_one_of)
    motor_address: EthercatAddress = Field(default_factory=EthercatAddress)
    id: str = Field(default="")

class StopMotionStreamResponse(BaseModel):
    success: bool = Field(default=False)
    message: str = Field(default="")
