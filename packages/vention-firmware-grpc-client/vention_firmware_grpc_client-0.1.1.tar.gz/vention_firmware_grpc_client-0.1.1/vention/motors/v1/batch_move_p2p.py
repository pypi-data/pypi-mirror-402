# This is an automatically generated file, please do not change
# gen by protobuf_to_pydantic[v0.3.3.1](https://github.com/so1n/protobuf_to_pydantic)
# Protobuf Version: 6.32.1 
# Pydantic Version: 2.11.10 
from .ethercat_address_p2p import EthercatAddress
from enum import IntEnum
from google.protobuf.message import Message  # type: ignore
from protobuf_to_pydantic.customer_validator import check_one_of
from pydantic import BaseModel
from pydantic import Field
from pydantic import model_validator
import typing

class MoveType(IntEnum):
    MOVE_TYPE_UNSPECIFIED = 0
    MOVE_TYPE_TRAPEZOIDAL = 1
    MOVE_TYPE_CONTINUOUS = 2
    MOVE_TYPE_TORQUE = 3
    MOVE_TYPE_HOME = 4

class TrapezoidalMotionProfile(BaseModel):
    velocity: float = Field(default=0.0)
    acceleration: float = Field(default=0.0)
    deceleration: float = Field(default=0.0)
    jerk: float = Field(default=0.0)

class ContinuousMotionProfile(BaseModel):
    velocity: float = Field(default=0.0)
    acceleration: float = Field(default=0.0)

class TorqueMotionProfile(BaseModel):
    torque_percentage: int = Field(default=0)

class TrapezoidalMoveTarget(BaseModel):
    motor_address: EthercatAddress = Field(default_factory=EthercatAddress)
    position_target: float = Field(default=0.0)

class TrapezoidalMove(BaseModel):
    move_type: str = Field(default="")
    motions: typing.List[TrapezoidalMoveTarget] = Field(default_factory=list)
    use_relative_reference: bool = Field(default=False)
    motion_profile: TrapezoidalMotionProfile = Field(default_factory=TrapezoidalMotionProfile)
    ignore_synchronization: bool = Field(default=False)

class ContinuousMove(BaseModel):
    move_type: str = Field(default="")
    motor_address: EthercatAddress = Field(default_factory=EthercatAddress)
    motion_profile: ContinuousMotionProfile = Field(default_factory=ContinuousMotionProfile)

class TorqueMove(BaseModel):
    move_type: str = Field(default="")
    motor_address: EthercatAddress = Field(default_factory=EthercatAddress)
    motion_profile: TorqueMotionProfile = Field(default_factory=TorqueMotionProfile)

class HomeMove(BaseModel):
    move_type: str = Field(default="")
    motor_address: EthercatAddress = Field(default_factory=EthercatAddress)

class GenericMove(BaseModel):
    _one_of_dict = {"GenericMove.move_type": {"fields": {"continuous_moves", "home_moves", "torque_moves", "trapezoidal_move"}}}
    one_of_validator = model_validator(mode="before")(check_one_of)
    trapezoidal_move: TrapezoidalMove = Field(default_factory=TrapezoidalMove)
    continuous_moves: ContinuousMove = Field(default_factory=ContinuousMove)
    torque_moves: TorqueMove = Field(default_factory=TorqueMove)
    home_moves: HomeMove = Field(default_factory=HomeMove)

class BatchMove(BaseModel):
    moves: typing.List[GenericMove] = Field(default_factory=list)
