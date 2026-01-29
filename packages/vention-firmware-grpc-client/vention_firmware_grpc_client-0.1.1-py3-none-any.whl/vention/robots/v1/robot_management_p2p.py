# This is an automatically generated file, please do not change
# gen by protobuf_to_pydantic[v0.3.3.1](https://github.com/so1n/protobuf_to_pydantic)
# Protobuf Version: 6.32.1 
# Pydantic Version: 2.11.10 
from .robot_instance_p2p import DriverParam
from .robot_instance_p2p import RobotInstance
from google.protobuf.message import Message  # type: ignore
from pydantic import BaseModel
from pydantic import Field
import typing


class RegisterRobotRequest(BaseModel):
    """
     Robot Management Messages
    """

    robot_instance: RobotInstance = Field(default_factory=RobotInstance)

class RegisterRobotResponse(BaseModel):
    success: bool = Field(default=False)
    error_message: str = Field(default="")

class UnregisterRobotResponse(BaseModel):
    success: bool = Field(default=False)
    error_message: str = Field(default="")

class RobotInfo(BaseModel):
    id: str = Field(default="")
    name: str = Field(default="")
    robot_type: str = Field(default="")
    joint_names: typing.List[str] = Field(default_factory=list)
    driver: str = Field(default="")
    driver_params: DriverParam = Field(default_factory=DriverParam)

class ListRobotsResponse(BaseModel):
    robots: typing.List[RobotInfo] = Field(default_factory=list)

class ConnectRobotResponse(BaseModel):
    success: bool = Field(default=False)
    error_message: str = Field(default="")
