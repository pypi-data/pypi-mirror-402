# This is an automatically generated file, please do not change
# gen by protobuf_to_pydantic[v0.3.3.1](https://github.com/so1n/protobuf_to_pydantic)
# Protobuf Version: 6.32.1 
# Pydantic Version: 2.11.10 
from google.protobuf.message import Message  # type: ignore
from pydantic import BaseModel
from pydantic import Field


class RobotAssets(BaseModel):
    robot_type: str = Field(default="")
    path_urdf: str = Field(default="")
    path_srdf: str = Field(default="")
    path_joint_limits: str = Field(default="")
    path_cartesian_limits: str = Field(default="")
    kinematic_chain_start: str = Field(default="")
    kinematic_chain_end: str = Field(default="")
