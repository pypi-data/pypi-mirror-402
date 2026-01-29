# This is an automatically generated file, please do not change
# gen by protobuf_to_pydantic[v0.3.3.1](https://github.com/so1n/protobuf_to_pydantic)
# Protobuf Version: 6.32.1 
# Pydantic Version: 2.11.10 
from enum import IntEnum
from google.protobuf.message import Message  # type: ignore
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

class StopResultCode(IntEnum):
    STOP_RESULT_CODE_SUCCESS = 0
    STOP_RESULT_CODE_FAILURE = 1
    STOP_RESULT_CODE_ROBOT_NOT_FOUND = 2

class StopResponse(BaseModel):
    model_config = ConfigDict(validate_default=True)
    result_code: StopResultCode = Field(default=0)
