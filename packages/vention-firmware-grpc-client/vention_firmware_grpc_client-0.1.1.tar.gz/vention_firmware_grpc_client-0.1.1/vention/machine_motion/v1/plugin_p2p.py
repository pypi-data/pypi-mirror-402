# This is an automatically generated file, please do not change
# gen by protobuf_to_pydantic[v0.3.3.1](https://github.com/so1n/protobuf_to_pydantic)
# Protobuf Version: 6.32.1 
# Pydantic Version: 2.11.10 
from enum import IntEnum
from google.protobuf.message import Message  # type: ignore
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
import typing


class GetPluginsResponse(BaseModel):
    class Plugin(BaseModel):
        name: str = Field(example="TCP Socket API")
        service_name: str = Field(example="mmai-tcp-socket-api")
        activated: bool = Field()
        version: str = Field(example="1.0.0")

    plugins: typing.List["GetPluginsResponse.Plugin"] = Field(default_factory=list)

class ActivatePluginRequest(BaseModel):
    license_key: str = Field(example="1-12D687-A432F8E6")

class ActivatePluginErrorResponse(BaseModel):
    class ErrorCode(IntEnum):
        ERROR_CODE_UNSPECIFIED = 0
        ERROR_CODE_NO_SERIAL_NUMBER_ASSIGNED_TO_MACHINE = 1
        ERROR_CODE_LICENSE_KEY_FORMAT_IS_INVALID = 2
        ERROR_CODE_LICENSE_KEY_VALIDATION_FAILED = 3
        ERROR_CODE_PLUGIN_NOT_SUPPORTED = 4
        ERROR_CODE_UNKNOWN_ERROR = 5

    model_config = ConfigDict(validate_default=True)
    message: str = Field(description="Error code can be **1** for no serial number assigned to machine, **2** for license key format is invalid, **3** for license key validation failed, **4** for plugin not supported, and **5** for unknown error.")
    error_code: "ActivatePluginErrorResponse.ErrorCode" = Field()

class DeactivatePluginRequest(BaseModel):
    name: str = Field(example="TCP Socket API")

class DeactivatePluginErrorResponse(BaseModel):
    class ErrorCode(IntEnum):
        ERROR_CODE_UNSPECIFIED = 0
        ERROR_CODE_PLUGIN_DOES_NOT_EXIST = 1
        ERROR_CODE_PLUGIN_NOT_ACTIVATED = 2
        ERROR_CODE_FAILED_TO_DISABLE_PLUGIN = 3
        ERROR_CODE_FAILED_TO_STOP_PLUGIN = 4
        ERROR_CODE_UNKNOWN_ERROR = 5

    model_config = ConfigDict(validate_default=True)
    message: str = Field(description="Error code can be **1** for plugin does not exist, **2** for plugin not activated, **3** for failed to disable plugin, **4** for failed to stop plugin, and **5** for unknown error.")
    error_code: "DeactivatePluginErrorResponse.ErrorCode" = Field()
