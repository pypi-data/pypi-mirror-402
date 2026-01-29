# This is an automatically generated file, please do not change
# gen by protobuf_to_pydantic[v0.3.3.1](https://github.com/so1n/protobuf_to_pydantic)
# Protobuf Version: 6.32.1 
# Pydantic Version: 2.11.10 
from enum import IntEnum
from google.protobuf.message import Message  # type: ignore
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

class MotorSize(IntEnum):
    MOTOR_SIZE_UNKNOWN = 0
    MOTOR_SIZE_NEMA_34_68MM = 1
    MOTOR_SIZE_NEMA_34_100MM = 2
    MOTOR_SIZE_NEMA_34_157MM = 3


class MotorType(IntEnum):
    MOTOR_TYPE_UNKNOWN = 0
    MOTOR_TYPE_STEP_SERVO = 1
    MOTOR_TYPE_CONVEYOR_STEP_SERVO = 2

class MotorHardwareInfo(BaseModel):
    model_config = ConfigDict(validate_default=True)
    motor_type: MotorType = Field(default=0)
    motor_size: MotorSize = Field(default=0)
    serial_number: int = Field(default=0)
    firmware_version: str = Field(default="")
    hardware_version: str = Field(default="")
    brake_present: bool = Field(default=False)
    encoder_offset: int = Field(default=0)
    valid_firmware: bool = Field(default=False)
