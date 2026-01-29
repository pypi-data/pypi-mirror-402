# This is an automatically generated file, please do not change
# gen by protobuf_to_pydantic[v0.3.3.1](https://github.com/so1n/protobuf_to_pydantic)
# Protobuf Version: 6.32.1 
# Pydantic Version: 2.11.10 
from google.protobuf.message import Message  # type: ignore
from pydantic import BaseModel
from pydantic import Field


class EthercatCreateLogRequest(BaseModel):
    delay_seconds: float = Field(default=0.0)

class EthercatLogResponse(BaseModel):
    success: bool = Field(default=False)
    log_path: str = Field(default="")
    message: str = Field(default="")

class EthercatResetRequest(BaseModel):
    pass

class EthercatResetResponse(BaseModel):
    success: bool = Field(default=False)
    message: str = Field(default="")
