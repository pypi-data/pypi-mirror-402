# This is an automatically generated file, please do not change
# gen by protobuf_to_pydantic[v0.3.3.1](https://github.com/so1n/protobuf_to_pydantic)
# Protobuf Version: 6.32.1 
# Pydantic Version: 2.11.10 
from .ethercat_address_p2p import EthercatAddress
from google.protobuf.message import Message  # type: ignore
from protobuf_to_pydantic.customer_validator import check_one_of
from pydantic import BaseModel
from pydantic import Field
from pydantic import model_validator


class EthercatReadSdoRequest(BaseModel):
    _one_of_dict = {"EthercatReadSdoRequest.identifier": {"fields": {"address", "id"}}}
    one_of_validator = model_validator(mode="before")(check_one_of)
    address: EthercatAddress = Field(default_factory=EthercatAddress)
    id: str = Field(default="")
    index: int = Field(default=0)
    subindex: int = Field(default=0)
    size: int = Field(default=0)

class EthercatReadSdoResponse(BaseModel):
    value: bytes = Field(default=b"")

class EthercatWriteSdoRequest(BaseModel):
    _one_of_dict = {"EthercatWriteSdoRequest.identifier": {"fields": {"address", "id"}}}
    one_of_validator = model_validator(mode="before")(check_one_of)
    address: EthercatAddress = Field(default_factory=EthercatAddress)
    id: str = Field(default="")
    index: int = Field(default=0)
    subindex: int = Field(default=0)
    data: bytes = Field(default=b"")

class EthercatWriteSdoResponse(BaseModel):
    pass

class EthercatWriteFoeRequest(BaseModel):
    _one_of_dict = {"EthercatWriteFoeRequest.identifier": {"fields": {"address", "id"}}}
    one_of_validator = model_validator(mode="before")(check_one_of)
    address: EthercatAddress = Field(default_factory=EthercatAddress)
    id: str = Field(default="")
    filename: str = Field(default="")
    password: int = Field(default=0)
    data: bytes = Field(default=b"")

class EthercatFoeResponse(BaseModel):
    pass

class EthercatReadEscRegisterRequest(BaseModel):
    _one_of_dict = {"EthercatReadEscRegisterRequest.identifier": {"fields": {"address", "id"}}}
    one_of_validator = model_validator(mode="before")(check_one_of)
    address: EthercatAddress = Field(default_factory=EthercatAddress)
    id: str = Field(default="")
    index: int = Field(default=0)
    size: int = Field(default=0)

class EthercatReadEscRegisterResponse(BaseModel):
    value: bytes = Field(default=b"")
