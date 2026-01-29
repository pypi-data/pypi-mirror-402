# This is an automatically generated file, please do not change
# gen by protobuf_to_pydantic[v0.3.3.1](https://github.com/so1n/protobuf_to_pydantic)
# Protobuf Version: 6.32.1 
# Pydantic Version: 2.11.10 
from .joint_trajectory_point_p2p import JointTrajectoryPoint
from google.protobuf.message import Message  # type: ignore
from pydantic import BaseModel
from pydantic import Field
import typing


class JointTrajectory(BaseModel):
    """
     Message for joint trajectory, which can be used to control a model
 with multiple single-axis joints simultaneously.
    """

    num_joints: int = Field(default=0)
    points: typing.List[JointTrajectoryPoint] = Field(default_factory=list)
