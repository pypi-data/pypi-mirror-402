# This is an automatically generated file, please do not change
# gen by protobuf_to_pydantic[v0.3.3.1](https://github.com/so1n/protobuf_to_pydantic)
# Protobuf Version: 6.32.1 
# Pydantic Version: 2.11.10 
from .ethercat_address_p2p import EthercatAddress
from enum import IntEnum
from google.protobuf.message import Message  # type: ignore
from protobuf_to_pydantic.customer_validator import check_one_of
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import model_validator
import typing

class HomingMethod(IntEnum):
    HOMING_METHOD_UNSPECIFIED = 0
    HOMING_METHOD_SENSOR_A = 17
    HOMING_METHOD_SENSOR_B = 18


class QuickStopOptionCode(IntEnum):
    QUICK_STOP_OPTION_CODE_UNSPECIFIED = 0
    QUICK_STOP_OPTION_CODE_SLOW_DOWN_ON_QUICK_STOP = 1


class DriveDirection(IntEnum):
    DRIVE_DIRECTION_UNSPECIFIED = 0
    DRIVE_DIRECTION_CLOCKWISE = 1
    DRIVE_DIRECTION_COUNTER_CLOCKWISE = -1

class TuningParameters(BaseModel):
    kp_current: float = Field(default=0.0)
    ki_current: float = Field(default=0.0)
    kp_velocity: float = Field(default=0.0)
    ki_velocity: float = Field(default=0.0)
    imax_velocity: float = Field(default=0.0)
    kp_position: float = Field(default=0.0)
    ki_position: float = Field(default=0.0)
    kd_position: float = Field(default=0.0)
    imax_position: float = Field(default=0.0)
    velocity_feedforward: float = Field(default=0.0)
    acceleration_feedforward: float = Field(default=0.0)
    load_feedforward: float = Field(default=0.0)

class ControllerParameters(BaseModel):
    electric_angle_correction_saturation: int = Field(default=0)# SATTHETA_CT
    kp_electric_angle_correction: int = Field(default=0)# KSPDTH
    electric_angle_correction_offset: int = Field(default=0)# THETAOFF
    electric_angle_variation_limit: int = Field(default=0)# DELTA_THETAC_LIM
    kp_id_current: float = Field(default=0.0)# KP_CRTD_F
    ki_id_current: float = Field(default=0.0)# KI_CRTD_F
    kp_id_reference_motor_speed: int = Field(default=0)# IDREF_FACTOR
    auxiliar_setting_register_4: int = Field(default=0)# ASR4

class PositionProfileModeConfiguration(BaseModel):
    position_window: float = Field(default=0.0)
    position_window_time: float = Field(default=0.0)
    quick_stop_deceleration: float = Field(default=0.0)
    target_position: float = Field(default=0.0)
    profile_velocity: float = Field(default=0.0)
    profile_acceleration: float = Field(default=0.0)

class HomingModeConfiguration(BaseModel):
    model_config = ConfigDict(validate_default=True)
    home_offset: float = Field(default=0.0)
    homing_velocity_search_for_switch: float = Field(default=0.0)
    homing_velocity_search_for_zero: float = Field(default=0.0)
    homing_acceleration: float = Field(default=0.0)
    homing_method: HomingMethod = Field(default=0)

class VelocityProfileModeConfiguration(BaseModel):
    velocity_window: float = Field(default=0.0)
    velocity_window_time: float = Field(default=0.0)
    velocity_threshold: float = Field(default=0.0)
    target_velocity: float = Field(default=0.0)

class CyclicSynchronousTorqueModeConfiguration(BaseModel):
    max_motor_speed: float = Field(default=0.0)

class DriveConfiguration(BaseModel):
    model_config = ConfigDict(validate_default=True)
    tuning_parameters: TuningParameters = Field(default_factory=TuningParameters)
    controller_parameters: ControllerParameters = Field(default_factory=ControllerParameters)
    position_profile_mode_configuration: PositionProfileModeConfiguration = Field(default_factory=PositionProfileModeConfiguration)
    homing_mode_configuration: HomingModeConfiguration = Field(default_factory=HomingModeConfiguration)
    velocity_profile_mode_configuration: VelocityProfileModeConfiguration = Field(default_factory=VelocityProfileModeConfiguration)
    cyclic_synchronous_torque_mode_configuration: CyclicSynchronousTorqueModeConfiguration = Field(default_factory=CyclicSynchronousTorqueModeConfiguration)
    quick_stop_option_code: QuickStopOptionCode = Field(default=0)
    drive_direction: DriveDirection = Field(default=0)
    touch_probe_function: int = Field(default=0)
    quick_stop_deceleration: int = Field(default=0)
    mm_per_rotation: float = Field(default=0.0)
    gear_ratio: float = Field(default=0.0)

class DriveConfigurationRequest(BaseModel):
    _one_of_dict = {"DriveConfigurationRequest.identifier": {"fields": {"id", "motor_address"}}}
    one_of_validator = model_validator(mode="before")(check_one_of)
    motor_address: EthercatAddress = Field(default_factory=EthercatAddress)
    id: str = Field(default="")
    configuration: typing.Optional[DriveConfiguration] = Field(default_factory=DriveConfiguration)# Optional configuration to read

class DriveConfigurationResponse(BaseModel):
    success: bool = Field(default=False)
    message: str = Field(default="")
    configuration: typing.Optional[DriveConfiguration] = Field(default_factory=DriveConfiguration)
