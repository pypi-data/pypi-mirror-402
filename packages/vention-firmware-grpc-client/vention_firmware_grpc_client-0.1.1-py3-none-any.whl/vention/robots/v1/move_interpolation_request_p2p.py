# This is an automatically generated file, please do not change
# gen by protobuf_to_pydantic[v0.3.3.1](https://github.com/so1n/protobuf_to_pydantic)
# Protobuf Version: 6.32.1 
# Pydantic Version: 2.11.10 
from .joint_trajectory_point_p2p import JointTrajectoryPoint
from .plan_request_p2p import PlanResultCode
from google.protobuf.message import Message  # type: ignore
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
import typing


class MoveInterpolationRequest(BaseModel):
    id: str = Field(default="")
    points: typing.List[JointTrajectoryPoint] = Field(default_factory=list)

class MoveInterpolationResponse(BaseModel):
    model_config = ConfigDict(validate_default=True)
    result_code: PlanResultCode = Field(default=0)
    start_duration: float = Field(default=0.0)# Duration to reach start of trajectory
    duration: float = Field(default=0.0)# Duration of the trajectory in seconds (not including start trajectory)
    error_point: int = Field(default=0)# Point index in which failure occurred (if any)
