# This is an automatically generated file, please do not change
# gen by protobuf_to_pydantic[v0.3.3.1](https://github.com/so1n/protobuf_to_pydantic)
# Protobuf Version: 6.32.1 
# Pydantic Version: 2.11.10 
from .ethercat_address_p2p import EthercatAddress
from google.protobuf.message import Message  # type: ignore
from pydantic import BaseModel
from pydantic import Field


class SetPosition(BaseModel):
    motor_address: EthercatAddress = Field(default_factory=EthercatAddress)
    position: float = Field(default=0.0)
