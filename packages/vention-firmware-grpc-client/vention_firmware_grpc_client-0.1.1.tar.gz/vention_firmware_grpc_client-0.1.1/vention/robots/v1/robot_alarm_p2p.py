# This is an automatically generated file, please do not change
# gen by protobuf_to_pydantic[v0.3.3.1](https://github.com/so1n/protobuf_to_pydantic)
# Protobuf Version: 6.32.1 
# Pydantic Version: 2.11.10 
from .notifications_p2p import Notification
from google.protobuf.message import Message  # type: ignore
from pydantic import BaseModel
from pydantic import Field
import typing


class RobotAlarmStreamRequest(BaseModel):
    id: str = Field(default="")# ID of the robot to stream notifications for

class RobotAlarm(BaseModel):
    notifications: typing.List[Notification] = Field(default_factory=list)# List of notifications
