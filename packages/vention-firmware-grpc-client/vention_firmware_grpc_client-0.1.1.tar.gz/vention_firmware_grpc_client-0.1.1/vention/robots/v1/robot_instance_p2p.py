# This is an automatically generated file, please do not change
# gen by protobuf_to_pydantic[v0.3.3.1](https://github.com/so1n/protobuf_to_pydantic)
# Protobuf Version: 6.32.1 
# Pydantic Version: 2.11.10 
from google.protobuf.message import Message  # type: ignore
from pydantic import BaseModel
from pydantic import Field
import typing


class DriverParam(BaseModel):
    params: "typing.Dict[str, str]" = Field(default_factory=dict)

class RobotInstance(BaseModel):
    id: str = Field(default="")
    name: str = Field(default="")
    robot_type: str = Field(default="")
    driver: str = Field(default="")
    driver_params: DriverParam = Field(default_factory=DriverParam)
    cpu_affinity: typing.Optional[int] = Field(default=0)
