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

class MotorDirection(IntEnum):
    MOTOR_DIRECTION_UNSPECIFIED = 0
    MOTOR_DIRECTION_CLOCKWISE = 1
    MOTOR_DIRECTION_COUNTER_CLOCKWISE = 2


class ActuatorType(IntEnum):
    ACTUATOR_TYPE_UNSPECIFIED = 0
    ACTUATOR_TYPE_CUSTOM = 1
    ACTUATOR_TYPE_TIMING_BELT = 2
    ACTUATOR_TYPE_ENCLOSED_TIMING_BELT = 3
    ACTUATOR_TYPE_RACK_AND_PINION_V2 = 4
    ACTUATOR_TYPE_BALL_SCREW = 5
    ACTUATOR_TYPE_ENCLOSED_BALL_SCREW = 6
    ACTUATOR_TYPE_LEAD_SCREW = 7
    ACTUATOR_TYPE_INDEXER_V2 = 8
    ACTUATOR_TYPE_INDEXER_V2_HEAVY_DUTY = 9
    ACTUATOR_TYPE_BELT_CONVEYOR = 10
    ACTUATOR_TYPE_ROLLER_CONVEYOR = 11
    ACTUATOR_TYPE_BELT_RACK = 12
    ACTUATOR_TYPE_HEAVY_DUTY_ROLLER_CONVEYOR = 13
    ACTUATOR_TYPE_TIMING_BELT_CONVEYOR = 14
    ACTUATOR_TYPE_TIMING_BELT_CONVEYOR_V2 = 15
    ACTUATOR_TYPE_TELESCOPIC_COLUMN = 16
    ACTUATOR_TYPE_O_RING_ROLLER_CONVEYOR = 17


class TuningProfileType(IntEnum):
    TUNING_PROFILE_TYPE_UNSPECIFIED = 0
    TUNING_PROFILE_TYPE_DEFAULT = 1
    TUNING_PROFILE_TYPE_POSITION = 2
    TUNING_PROFILE_TYPE_VELOCITY = 3
    TUNING_PROFILE_TYPE_TORQUE = 4

class PidTuningParameters(BaseModel):
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

class VoltageTuningParameters(BaseModel):
    kval_hold: float = Field(default=0.0)
    kval_run: float = Field(default=0.0)
    kval_acc: float = Field(default=0.0)
    kval_dec: float = Field(default=0.0)

class TuningParameters(BaseModel):
    _one_of_dict = {"TuningParameters.type": {"fields": {"pid_parameters", "voltage_parameters"}}}
    one_of_validator = model_validator(mode="before")(check_one_of)
    pid_parameters: PidTuningParameters = Field(default_factory=PidTuningParameters)
    voltage_parameters: VoltageTuningParameters = Field(default_factory=VoltageTuningParameters)

class ControllerParameters(BaseModel):
    electric_angle_correction_saturation: int = Field(default=0)# SATTHETA_CT
    kp_electric_angle_correction: int = Field(default=0)# KSPDTH
    electric_angle_correction_offset: int = Field(default=0)# THETAOFF
    electric_angle_variation_limit: int = Field(default=0)# DELTA_THETAC_LIM
    kp_id_current: float = Field(default=0.0)# KP_CRTD_F
    ki_id_current: float = Field(default=0.0)# KI_CRTD_F
    kp_id_reference_motor_speed: int = Field(default=0)# IDREF_FACTOR
    auxiliary_setting_register_4: int = Field(default=0)# ASR4

class TuningProfile(BaseModel):
    _one_of_dict = {"TuningProfile.type": {"fields": {"profile_type", "tuning_parameters"}}}
    one_of_validator = model_validator(mode="before")(check_one_of)
    model_config = ConfigDict(validate_default=True)
    profile_type: TuningProfileType = Field(default=0)
    tuning_parameters: TuningParameters = Field(default_factory=TuningParameters)
    controller_parameters: typing.Optional[ControllerParameters] = Field(default_factory=ControllerParameters)

class MotorConfiguration(BaseModel):
    model_config = ConfigDict(validate_default=True)
    motor_address: EthercatAddress = Field(default_factory=EthercatAddress)
    direction: MotorDirection = Field(default=0)
    gear_ratio: float = Field(default=0.0)
    lead_motor_address: typing.Optional[EthercatAddress] = Field(default_factory=EthercatAddress)
    tuning_profile: typing.Optional[TuningProfile] = Field(default_factory=TuningProfile)

class MechanicalLimits(BaseModel):
    max_velocity: typing.Optional[int] = Field(default=0)
    max_acceleration: typing.Optional[int] = Field(default=0)

class StallMonitor(BaseModel):
    position_threshold: float = Field(default=0.0)# mm
    torque_threshold: float = Field(default=0.0)# Amps
    window_time: float = Field(default=0.0)# sec

class VelocityMonitor(BaseModel):
    velocity_threshold: float = Field(default=0.0)# mm/sec
    window_time: float = Field(default=0.0)# sec

class ActuatorMonitors(BaseModel):
    stall_monitor: typing.Optional[StallMonitor] = Field(default_factory=StallMonitor)
    velocity_monitor: typing.Optional[VelocityMonitor] = Field(default_factory=VelocityMonitor)

class HomingProfile(BaseModel):
    velocity: int = Field(default=0)
    acceleration: int = Field(default=0)
    sensor_offset: int = Field(default=0)

class ActuatorConfiguration(BaseModel):
    _one_of_dict = {"ActuatorConfiguration.type": {"fields": {"actuator_type", "mm_per_rotation"}}}
    one_of_validator = model_validator(mode="before")(check_one_of)
    model_config = ConfigDict(validate_default=True)
    id: str = Field(default="")
    actuator_type: ActuatorType = Field(default=0)
    mm_per_rotation: float = Field(default=0.0)
    motors: typing.List[MotorConfiguration] = Field(default_factory=list)
    limits: typing.Optional[MechanicalLimits] = Field(default_factory=MechanicalLimits)
    homing_profile: typing.Optional[HomingProfile] = Field(default_factory=HomingProfile)
    monitors: typing.Optional[ActuatorMonitors] = Field(default_factory=ActuatorMonitors)

class WriteActuatorConfigurationRequest(BaseModel):
    actuator_configurations: typing.List[ActuatorConfiguration] = Field(default_factory=list)

class WriteActuatorConfigurationResponse(BaseModel):
    pass

class ReadActuatorConfigurationRequest(BaseModel):
    actuator_ids: typing.List[str] = Field(default_factory=list)

class ReadActuatorConfigurationResponse(BaseModel):
    actuator_configurations: typing.List[ActuatorConfiguration] = Field(default_factory=list)
