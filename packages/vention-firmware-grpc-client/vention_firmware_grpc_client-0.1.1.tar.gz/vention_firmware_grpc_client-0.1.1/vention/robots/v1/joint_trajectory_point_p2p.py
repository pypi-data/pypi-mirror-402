# This is an automatically generated file, please do not change
# gen by protobuf_to_pydantic[v0.3.3.1](https://github.com/so1n/protobuf_to_pydantic)
# Protobuf Version: 6.32.1 
# Pydantic Version: 2.11.10 
from datetime import datetime
from google.protobuf.message import Message  # type: ignore
from pydantic import BaseModel
from pydantic import Field
import typing


class JointTrajectoryPoint(BaseModel):
    positions: typing.List[float] = Field(default_factory=list)# Joint positions in radians (revolute) or meters (prismatic)
    velocities: typing.List[float] = Field(default_factory=list)# Joint velocities in rad/s (revolute) or m/s (prismatic)
    accelerations: typing.List[float] = Field(default_factory=list)# Joint accelerations in rad/s^2 (revolute) or m/s^2 (prismatic)
    time: datetime = Field(default_factory=datetime.now)# Time from start of trajectory
