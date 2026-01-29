# This is an automatically generated file, please do not change
# gen by protobuf_to_pydantic[v0.3.3.1](https://github.com/so1n/protobuf_to_pydantic)
# Protobuf Version: 6.32.1 
# Pydantic Version: 2.11.10 
from .frame_p2p import Vector3d
from google.protobuf.message import Message  # type: ignore
from pydantic import BaseModel
from pydantic import Field


class Inertia(BaseModel):
    """
     Inertia tensor elements of a 3x3 symmetric matrix
    """

    ixx: float = Field(default=0.0)
    ixy: float = Field(default=0.0)
    ixz: float = Field(default=0.0)
    iyy: float = Field(default=0.0)
    iyz: float = Field(default=0.0)
    izz: float = Field(default=0.0)

class MassProperties(BaseModel):
    mass: float = Field(default=0.0)# Mass of the body (kg)
    center_of_mass: Vector3d = Field(default_factory=Vector3d)# Center of mass position in the parent frame (m)
    inertia_tensor: Inertia = Field(default_factory=Inertia)# Inertia tensor about the center of mass with respect to the parent frame orientation (kg m^2)
