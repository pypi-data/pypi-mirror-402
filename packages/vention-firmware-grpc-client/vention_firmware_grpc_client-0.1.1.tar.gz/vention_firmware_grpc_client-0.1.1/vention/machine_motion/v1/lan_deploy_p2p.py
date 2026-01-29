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


class UpdateKeypairRequest(BaseModel):
    certificate: str = Field(default="")
    initialization_vector: str = Field(default="")
    encrypted_private_key: str = Field(default="")
    encrypted_aes_key: str = Field(default="")

class UpdateKeypairErrorResponse(BaseModel):
    class ErrorCode(IntEnum):
        ERROR_CODE_UNSPECIFIED = 0
        ERROR_CODE_NO_CERTIFICATE_INSTALLED = 1
        ERROR_CODE_MALFORMED_CERTIFICATE = 2
        ERROR_CODE_DECRYPTION_FAILURE = 3
        ERROR_CODE_UNTRUSTED_CERTIFICATE = 4
        ERROR_CODE_CERTIFICATE_ALREADY_EXISTS = 6
        ERROR_CODE_UNKNOWN_ERROR = 5

    model_config = ConfigDict(validate_default=True)
    message: str = Field(example="Not TLS certificate installed. Please contact Customer Success.")
    error_code: "UpdateKeypairErrorResponse.ErrorCode" = Field(description="Error code can be **1** for no certificate installed, **2** for malformed certificate, **3** for decryption failure, **4** for untrusted certificate, **6** for already existing certificate, and **5** for unknown error.")

class GetCertificateResponse(BaseModel):
    certificate: str = Field(default="")
    issue_date: datetime = Field(default_factory=datetime.now)
    expiration_date: datetime = Field(default_factory=datetime.now)

class GetCertificateErrorResponse(BaseModel):
    class ErrorCode(IntEnum):
        ERROR_CODE_UNSPECIFIED = 0
        ERROR_CODE_NO_CERTIFICATE_INSTALLED = 1
        ERROR_CODE_MALFORMED_CERTIFICATE = 2
        ERROR_CODE_UNKNOWN_ERROR = 3

    model_config = ConfigDict(validate_default=True)
    message: str = Field(example="No certificate installed.")
    error_code: "GetCertificateErrorResponse.ErrorCode" = Field(description="Error code can be **1** for no certificate installed, **2** for malformed certificate, and **3** for unknown error.")
