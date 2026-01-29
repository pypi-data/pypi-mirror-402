# This is an automatically generated file, please do not change
# gen by protobuf_to_pydantic[v0.3.3.1](https://github.com/so1n/protobuf_to_pydantic)
# Protobuf Version: 6.32.1 
# Pydantic Version: 2.11.10 
from .frame_p2p import CartesianMotion
from .frame_p2p import Frame
from enum import IntEnum
from google.protobuf.message import Message  # type: ignore
from protobuf_to_pydantic.customer_validator import check_one_of
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import model_validator
import typing

class MoveType(IntEnum):
    MOVE_TYPE_UNSPECIFIED = 0
    MOVE_TYPE_JOINT = 1
    MOVE_TYPE_CARTESIAN = 2

class CartesianConstraints(BaseModel):
    velocity: typing.Optional[CartesianMotion] = Field(default_factory=CartesianMotion)# Cartesian velocities in m/s, rad/s. Maximum limits are used if not specified.
    acceleration: typing.Optional[CartesianMotion] = Field(default_factory=CartesianMotion)# Cartesian accelerations in m/s^2, rad/s^2. Maximum limits are used if not specified.

class CartesianGoal(BaseModel):
    pose: Frame = Field(default_factory=Frame)# Target pose in the base frame

class JointConstraints(BaseModel):
    velocities: typing.List[float] = Field(default_factory=list)# Joint velocities in rad/s. Maximum limits are used if empty array is provided.
    accelerations: typing.List[float] = Field(default_factory=list)# Joint accelerations in rad/s^2. Maximum limits are used if empty array is provided.

class JointGoal(BaseModel):
    positions: typing.List[float] = Field(default_factory=list)# Joint positions in radians

class MoveSegment(BaseModel):
    _one_of_dict = {"MoveSegment.constraints": {"fields": {"cartesian_constraints", "joint_constraints"}}, "MoveSegment.goal": {"fields": {"cartesian_goal", "joint_goal"}}}
    one_of_validator = model_validator(mode="before")(check_one_of)
    model_config = ConfigDict(validate_default=True)
    move_type: MoveType = Field(default=0)# Type of move
    joint_goal: JointGoal = Field(default_factory=JointGoal)
    cartesian_goal: CartesianGoal = Field(default_factory=CartesianGoal)
    joint_constraints: JointConstraints = Field(default_factory=JointConstraints)# Used if move_type is MOVE_TYPE_JOINT
    cartesian_constraints: CartesianConstraints = Field(default_factory=CartesianConstraints)# Used if move_type is MOVE_TYPE_CARTESIAN
    blend_radius: typing.Optional[float] = Field(default=0.0)
