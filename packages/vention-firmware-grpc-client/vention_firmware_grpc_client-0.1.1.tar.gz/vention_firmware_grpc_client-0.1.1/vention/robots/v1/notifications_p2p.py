# This is an automatically generated file, please do not change
# gen by protobuf_to_pydantic[v0.3.3.1](https://github.com/so1n/protobuf_to_pydantic)
# Protobuf Version: 6.32.1 
# Pydantic Version: 2.11.10 
from datetime import datetime
from enum import IntEnum
from google.protobuf.message import Message  # type: ignore
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

class NotificationType(IntEnum):
    NOTIFICATION_TYPE_UNSPECIFIED = 0
    NOTIFICATION_TYPE_MOTION = 1
    NOTIFICATION_TYPE_ROBOT = 2
    NOTIFICATION_TYPE_ACTUATOR = 3


class SeverityLevel(IntEnum):
    SEVERITY_LEVEL_UNSPECIFIED = 0
    SEVERITY_LEVEL_INFO = 1
    SEVERITY_LEVEL_WARNING = 2
    SEVERITY_LEVEL_ERROR = 3
    SEVERITY_LEVEL_CRITICAL = 4

class Notification(BaseModel):
    model_config = ConfigDict(validate_default=True)
    timestamp: datetime = Field(default_factory=datetime.now)# Time the notification was generated
    type: NotificationType = Field(default=0)# Type of notification
    message: str = Field(default="")# Human-readable message
    raw_message: str = Field(default="")# Raw message from the source system, if applicable
    code: int = Field(default=0)# Code for categorizing the notification
    severity: SeverityLevel = Field(default=0)# severity level of the notification
