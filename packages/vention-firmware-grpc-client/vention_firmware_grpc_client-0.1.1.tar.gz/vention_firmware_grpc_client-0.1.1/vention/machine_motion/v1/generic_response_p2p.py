# This is an automatically generated file, please do not change
# gen by protobuf_to_pydantic[v0.3.3.1](https://github.com/so1n/protobuf_to_pydantic)
# Protobuf Version: 6.32.1 
# Pydantic Version: 2.11.10 
from enum import IntEnum
from google.protobuf.message import Message  # type: ignore
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class GenericResponse(BaseModel):
    message: str = Field(example="OK")

class GenericErrorResponse(BaseModel):
    class ErrorCode(IntEnum):
        ERROR_CODE_UNSPECIFIED = 0
        ERROR_CODE_UNKNOWN_ERROR = 1
        ERROR_CODE_NOT_IMPLEMENTED = 2

    model_config = ConfigDict(validate_default=True)
    message: str = Field(example="An unknown error occurred.")
    error_code: "GenericErrorResponse.ErrorCode" = Field(description="Error code can be **1** for unknown error and **2** for not implemented.")
