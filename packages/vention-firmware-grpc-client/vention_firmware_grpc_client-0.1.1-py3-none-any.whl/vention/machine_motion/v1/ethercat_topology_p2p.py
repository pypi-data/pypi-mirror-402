# This is an automatically generated file, please do not change
# gen by protobuf_to_pydantic[v0.3.3.1](https://github.com/so1n/protobuf_to_pydantic)
# Protobuf Version: 6.32.1 
# Pydantic Version: 2.11.10 
from .motor_topology_p2p import MotorHardwareInfo
from datetime import datetime
from enum import IntEnum
from google.protobuf.message import Message  # type: ignore
from protobuf_to_pydantic.customer_validator import check_one_of
from pydantic import BaseModel
from pydantic import Field
from pydantic import model_validator
import typing

class EthercatDeviceType(IntEnum):
    ETHERCAT_DEVICE_TYPE_UNKNOWN = 0
    ETHERCAT_DEVICE_TYPE_SWITCH = 1
    ETHERCAT_DEVICE_TYPE_MOTOR = 2
    ETHERCAT_DEVICE_TYPE_IO_LINK_MASTER = 3

class EthercatDevice(BaseModel):
    _one_of_dict = {"EthercatDevice.device_info": {"fields": {"motor"}}}
    one_of_validator = model_validator(mode="before")(check_one_of)
    index: int = Field(default=0)
#SwitchHardwareInfo switch = 3;
    motor: MotorHardwareInfo = Field(default_factory=MotorHardwareInfo)

class EthercatTopologyStreamRequest(BaseModel):
    pass

class EthercatTopologyRequest(BaseModel):
    pass

class EthercatPortTopology(BaseModel):
    port: int = Field(default=0)
    devices: typing.List[EthercatDevice] = Field(default_factory=list)

class EthercatTopologyResponse(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    topology: typing.List[EthercatPortTopology] = Field(default_factory=list)
