# This is an automatically generated file, please do not change
# gen by protobuf_to_pydantic[v0.3.3.1](https://github.com/so1n/protobuf_to_pydantic)
# Protobuf Version: 6.32.1 
# Pydantic Version: 2.11.10 
from .frame_p2p import Frame
from .mass_properties_p2p import MassProperties
from enum import IntEnum
from google.protobuf.message import Message  # type: ignore
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

class SetToolResultCode(IntEnum):
    SET_TOOL_RESULT_CODE_UNSPECIFIED = 0
    SET_TOOL_RESULT_CODE_SUCCESS = 1
    SET_TOOL_RESULT_CODE_FAILURE = 2
    SET_TOOL_RESULT_CODE_INVALID_ROBOT_ID = 3
    SET_TOOL_RESULT_CODE_INVALID_PARENT_LINK = 4
    SET_TOOL_RESULT_CODE_INVALID_MASS_PROPERTIES = 5
    SET_TOOL_RESULT_CODE_INVALID_ROBOT_STATE = 6


class SetTcpResultCode(IntEnum):
    SET_TCP_RESULT_CODE_UNSPECIFIED = 0
    SET_TCP_RESULT_CODE_SUCCESS = 1
    SET_TCP_RESULT_CODE_FAILURE = 2
    SET_TCP_RESULT_CODE_INVALID_ROBOT_ID = 3
    SET_TCP_RESULT_CODE_INVALID_ROBOT_STATE = 4


class SetPayloadResultCode(IntEnum):
    """
     Payload
    """
    SET_PAYLOAD_RESULT_CODE_UNSPECIFIED = 0
    SET_PAYLOAD_RESULT_CODE_SUCCESS = 1
    SET_PAYLOAD_RESULT_CODE_FAILED = 2
    SET_PAYLOAD_RESULT_CODE_INVALID_STATE = 3

class Tcp(BaseModel):
    id: str = Field(default="")# ID of the TCP
    frame: Frame = Field(default_factory=Frame)# Frame of the TCP with respect to the tool base

class Tool(BaseModel):
    id: int = Field(default=0)# ID of the tool
    mass_props: MassProperties = Field(default_factory=MassProperties)# Mass properties of the tool
    tcp: Tcp = Field(default_factory=Tcp)# TCP of the tool

class SetToolRequest(BaseModel):
    """
     Set Tool request and response messages
    """

    id: str = Field(default="")# ID of the robot
    tool_parent_link: str = Field(default="")# Name of the tool parent link
    tool: Tool = Field(default_factory=Tool)# Tool to set

class SetToolResponse(BaseModel):
    model_config = ConfigDict(validate_default=True)
    result: SetToolResultCode = Field(default=0)# Indicates if the tool was set successfully

class SetTcpRequest(BaseModel):
    """
     Modify Tcp request and response messages
    """

    id: str = Field(default="")# ID of the robot
    tcp: Tcp = Field(default_factory=Tcp)# Tcp to set

class SetTcpResponse(BaseModel):
    model_config = ConfigDict(validate_default=True)
    result: SetTcpResultCode = Field(default=0)# Indicates if the TCP was set successfully

class GetTcpRequest(BaseModel):
    id: str = Field(default="")# ID of the robot

class GetTcpResponse(BaseModel):
    tcp: Tcp = Field(default_factory=Tcp)# Requested TCP

class TcpUpdateStreamRequest(BaseModel):
    """
     TcpUpdateStream service
    """

    id: str = Field(default="")# ID of the robot

class SetPayloadRequest(BaseModel):
    id: str = Field(default="")
    mass_properties: MassProperties = Field(default_factory=MassProperties)

class SetPayloadResponse(BaseModel):
    model_config = ConfigDict(validate_default=True)
    result_code: SetPayloadResultCode = Field(default=0)
