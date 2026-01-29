# This is an automatically generated file, please do not change
# gen by protobuf_to_pydantic[v0.3.3.1](https://github.com/so1n/protobuf_to_pydantic)
# Protobuf Version: 6.32.1 
# Pydantic Version: 2.11.10 
from enum import IntEnum
from google.protobuf.message import Message  # type: ignore
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class ActivateServiceRequest(BaseModel):
    service_name: str = Field(example="mmai-dhcp-server")
    enable: bool = Field()
    start: bool = Field()

class ActivateServiceErrorResponse(BaseModel):
    class ErrorCode(IntEnum):
        ERROR_CODE_UNSPECIFIED = 0
        ERROR_CODE_SERVICE_DOES_NOT_EXIST = 1
        ERROR_CODE_PERMISSION_DENIED = 2
        ERROR_CODE_PLUGIN_NOT_ACTIVATED = 3
        ERROR_CODE_UNKNOWN_ERROR = 4

    model_config = ConfigDict(validate_default=True)
    message: str = Field(example="You do not have the required permissions to toggle this service.")
    error_code: "ActivateServiceErrorResponse.ErrorCode" = Field(description="Error code can be **1** for service does not exist, **2** for permission denied, and **3** for unknown error.")
