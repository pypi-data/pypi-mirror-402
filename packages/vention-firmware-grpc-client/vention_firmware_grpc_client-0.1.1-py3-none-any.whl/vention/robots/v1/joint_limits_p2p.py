# This is an automatically generated file, please do not change
# gen by protobuf_to_pydantic[v0.3.3.1](https://github.com/so1n/protobuf_to_pydantic)
# Protobuf Version: 6.32.1 
# Pydantic Version: 2.11.10 
from google.protobuf.message import Message  # type: ignore
from pydantic import BaseModel
from pydantic import Field
import typing


class JointLimits(BaseModel):
    lower: typing.Optional[float] = Field(default=0.0)
    upper: typing.Optional[float] = Field(default=0.0)
    velocity: typing.Optional[float] = Field(default=0.0)
    acceleration: typing.Optional[float] = Field(default=0.0)
    jerk: typing.Optional[float] = Field(default=0.0)
    effort: typing.Optional[float] = Field(default=0.0)
