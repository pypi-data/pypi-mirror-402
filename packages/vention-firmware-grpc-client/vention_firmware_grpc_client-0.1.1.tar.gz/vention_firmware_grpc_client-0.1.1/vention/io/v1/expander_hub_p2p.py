# This is an automatically generated file, please do not change
# gen by protobuf_to_pydantic[v0.3.3.1](https://github.com/so1n/protobuf_to_pydantic)
# Protobuf Version: 6.32.1 
# Pydantic Version: 2.11.10 
from datetime import datetime
from enum import IntEnum
from google.protobuf.message import Message  # type: ignore
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
import typing

class DeviceType(IntEnum):
    DEVICE_TYPE_DIGITAL_IO_MODULE = 0
    DEVICE_TYPE_PUSH_BUTTON = 1
    DEVICE_TYPE_POWER_SWITCH = 2
    DEVICE_TYPE_PUSH_BUTTON_V2 = 3
    DEVICE_TYPE_UNKNOWN = 255

class DeviceAddress(BaseModel):
    port: int = Field(default=0)# Can be either 1 or 2
    device_id: int = Field(default=0)# Can be between 1 and 16

class OutputState(BaseModel):
    """
     These fields will always be set when receiving and OutputEvent.
 They are optional when sending a SetOutputRequest, if you only want to set a subset of outputs.
    """

    output0: typing.Optional[bool] = Field(default=False)
    output1: typing.Optional[bool] = Field(default=False)
    output2: typing.Optional[bool] = Field(default=False)
    output3: typing.Optional[bool] = Field(default=False)
    led_red: typing.Optional[bool] = Field(default=False)# pin 29
    led_green: typing.Optional[bool] = Field(default=False)# pin 30
    led_blue: typing.Optional[bool] = Field(default=False)# pin 31
    led_blink: typing.Optional[bool] = Field(default=False)

class InputState(BaseModel):
    input0: bool = Field(default=False)
    input1: bool = Field(default=False)
    input2: bool = Field(default=False)
    input3: bool = Field(default=False)

class IoDeviceOutput(BaseModel):
    address: DeviceAddress = Field(default_factory=DeviceAddress)
    output: OutputState = Field(default_factory=OutputState)

class SetOutputRequest(BaseModel):
    request: typing.List[IoDeviceOutput] = Field(default_factory=list)

class IoDeviceOutputResponse(BaseModel):
    class ResponseCode(IntEnum):
        RESPONSE_CODE_SUCCESS = 0
        RESPONSE_CODE_DEVICE_DISCONNECTED = 1
        RESPONSE_CODE_UNKNOWN_ERROR = 2

    model_config = ConfigDict(validate_default=True)
    address: DeviceAddress = Field(default_factory=DeviceAddress)
    response_code: "IoDeviceOutputResponse.ResponseCode" = Field(default=0)
    error_message: str = Field(default="")

class SetOutputResponse(BaseModel):
    response: typing.List[IoDeviceOutputResponse] = Field(default_factory=list)

class IODeviceInputEvent(BaseModel):
    model_config = ConfigDict(validate_default=True)
    address: DeviceAddress = Field(default_factory=DeviceAddress)
    device_type: DeviceType = Field(default=0)
    event_time: datetime = Field(default_factory=datetime.now)
    input: InputState = Field(default_factory=InputState)

class IODeviceOutputEvent(BaseModel):
    model_config = ConfigDict(validate_default=True)
    address: DeviceAddress = Field(default_factory=DeviceAddress)
    device_type: DeviceType = Field(default=0)
    event_time: datetime = Field(default_factory=datetime.now)
    output: OutputState = Field(default_factory=OutputState)

class DeviceInfo(BaseModel):
    model_config = ConfigDict(validate_default=True)
    address: DeviceAddress = Field(default_factory=DeviceAddress)
    device_type: DeviceType = Field(default=0)
    input: InputState = Field(default_factory=InputState)
    output: OutputState = Field(default_factory=OutputState)
    hardware_revision: str = Field(default="")# This means nothing today
    firmware_version: str = Field(default="")

class GetConnectedDevicesResponse(BaseModel):
    devices: typing.List[DeviceInfo] = Field(default_factory=list)

class IoDeviceError(BaseModel):
    class ErrorCode(IntEnum):
        ERROR_CODE_UNSUPPORTED_FIRMWARE = 0
        ERROR_CODE_UNSUPPORTED_HARDWARE = 1

    model_config = ConfigDict(validate_default=True)
    address: DeviceAddress = Field(default_factory=DeviceAddress)
    error_code: "IoDeviceError.ErrorCode" = Field(default=0)
    error_message: str = Field(default="")
    time: datetime = Field(default_factory=datetime.now)

class GetIoDeviceErrorsResponse(BaseModel):
    errors: typing.List[IoDeviceError] = Field(default_factory=list)

class DefaultState(BaseModel):
    address: DeviceAddress = Field(default_factory=DeviceAddress)
    default_output: OutputState = Field(default_factory=OutputState)

class IOConfig(BaseModel):
    configs: typing.List[DefaultState] = Field(default_factory=list)
