# This is an automatically generated file, please do not change
# gen by protobuf_to_pydantic[v0.3.3.1](https://github.com/so1n/protobuf_to_pydantic)
# Protobuf Version: 6.32.1 
# Pydantic Version: 2.11.10 
from google.protobuf.message import Message  # type: ignore
from pydantic import BaseModel
from pydantic import Field


class Vector3d(BaseModel):
    x: float = Field(default=0.0)
    y: float = Field(default=0.0)
    z: float = Field(default=0.0)

class Quaternion(BaseModel):
    x: float = Field(default=0.0)
    y: float = Field(default=0.0)
    z: float = Field(default=0.0)
    w: float = Field(default=0.0)

class Frame(BaseModel):
    position: Vector3d = Field(default_factory=Vector3d)# Position in meters
    orientation: Quaternion = Field(default_factory=Quaternion)# Orientation as a unit quaternion

class CartesianMotion(BaseModel):
    linear: float = Field(default=0.0)# Linear motion magnitude
    angular: float = Field(default=0.0)# Angular motion magnitude

class Twist(BaseModel):
    linear: Vector3d = Field(default_factory=Vector3d)# Linear velocity vector m/s
    angular: Vector3d = Field(default_factory=Vector3d)# Angular velocity vector rad/s
