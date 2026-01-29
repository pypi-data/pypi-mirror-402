# This is an automatically generated file, please do not change
# gen by protobuf_to_pydantic[v0.3.3.1](https://github.com/so1n/protobuf_to_pydantic)
# Protobuf Version: 6.32.1 
# Pydantic Version: 2.11.10 
from google.protobuf.message import Message  # type: ignore
from pydantic import BaseModel
from pydantic import Field


class UnregisterRobotRequest(BaseModel):
    """
     Request message for UnregisterRobot service
    """

    id: str = Field(default="")

class GetRobotInfoRequest(BaseModel):
    """
     Request message for GetRobotInfo service
    """

    id: str = Field(default="")

class StopRequest(BaseModel):
    """
     Request message for Stop service
    """

    id: str = Field(default="")

class JointStatesStreamRequest(BaseModel):
    """
     Request message for JointStatesStream service
    """

    id: str = Field(default="")
    max_frequency_hz: float = Field(default=0.0)# Maximum frequency of the stream in Hz (0 = no limit)

class PositionStreamRequest(BaseModel):
    """
     Request message for PositionStream service
    """

    id: str = Field(default="")
    max_frequency_hz: float = Field(default=0.0)# Maximum frequency of the stream in Hz (0 = no limit)
