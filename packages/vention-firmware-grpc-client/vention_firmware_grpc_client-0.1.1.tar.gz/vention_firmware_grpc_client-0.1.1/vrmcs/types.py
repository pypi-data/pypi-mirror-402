# Re-export all types used by the VRMCS client
# This module serves as a convenient single import point for all protobuf types

from vention.robots.v1.frame_p2p import (
    CartesianMotion,
    Frame,
    Quaternion,
    Twist,
    Vector3d,
)
from vention.robots.v1.joint_position_p2p import (
    JointPosition,
)
from vention.robots.v1.joint_trajectory_point_p2p import (
    JointTrajectoryPoint,
)
from vention.robots.v1.mass_properties_p2p import (
    Inertia,
    MassProperties,
)
from vention.robots.v1.move_interpolation_request_p2p import (
    MoveInterpolationRequest,
    MoveInterpolationResponse,
)
from vention.robots.v1.move_p2p import (
    CartesianConstraints,
    CartesianGoal,
    JointConstraints,
    JointGoal,
    MoveSegment,
    MoveType,
)
from vention.robots.v1.move_request_p2p import (
    MoveRequest,
    MoveResponse,
    MoveResultCode,
    WaitForMoveCompletionRequest,
    WaitForMoveCompletionResponse,
)
from vention.robots.v1.notifications_p2p import (
    Notification,
    NotificationType,
    SeverityLevel,
)
from vention.robots.v1.plan_request_p2p import (
    PlanRequest,
    PlanResponse,
    PlanResultCode,
)
from vention.robots.v1.robot_alarm_p2p import (
    RobotAlarm,
    RobotAlarmStreamRequest,
)
from vention.robots.v1.robot_configuration_p2p import (
    GetTcpRequest,
    GetTcpResponse,
    SetPayloadRequest,
    SetPayloadResponse,
    SetPayloadResultCode,
    SetTcpRequest,
    SetTcpResponse,
    SetTcpResultCode,
    Tcp,
)
from vention.robots.v1.robot_instance_p2p import (
    DriverParam,
    RobotInstance,
)
from vention.robots.v1.robot_kinematics_p2p import (
    ForwardKinematicsRequest,
    ForwardKinematicsResponse,
    InverseKinematicsRequest,
    InverseKinematicsResponse,
    JointRangeConstraints,
    KinResultCode,
    InverseKinematicsBatchRequest,
    InverseKinematicsBatchResponse,
    IkSolver,
    InverseKinematicsSolutions
)
from vention.robots.v1.robot_management_p2p import (
    ListRobotsResponse,
    RegisterRobotRequest,
    RegisterRobotResponse,
    RobotInfo,
    UnregisterRobotResponse,
)
from vention.robots.v1.robot_requests_p2p import (
    GetRobotInfoRequest,
    JointStatesStreamRequest,
    PositionStreamRequest,
    StopRequest,
    UnregisterRobotRequest,
)
from vention.robots.v1.robot_state_p2p import (
    CommandState,
    CommandStateStreamRequest,
    GetCommandStateRequest,
    GetCommandStateResponse,
    GetJointStatesRequest,
    GetJointStatesResponse,
    GetPositionStateRequest,
    GetPositionStateResponse,
    GetRobotStatesRequest,
    GetRobotStatesResponse,
    JointStates,
    PositionState,
    RobotConnectionState,
    RobotOperationalState,
    RobotSafetyState,
    RobotStates,
    RobotStatesStreamRequest,
    SetToFreedriveRequest,
    SetToFreedriveResponse,
    SetToNormalRequest,
    SetToNormalResponse,
)
from vention.robots.v1.stop_request_p2p import (
    StopResponse,
    StopResultCode,
)

# Explicitly define what should be re-exported to prevent auto-cleanup
__all__ = [
    # Robot Management
    "RegisterRobotRequest",
    "RegisterRobotResponse",
    "UnregisterRobotResponse",
    "UnregisterRobotRequest",
    "GetRobotInfoRequest",
    "ListRobotsResponse",
    "RobotInfo",
    # Mass Properties
    "MassProperties",
    "Inertia",
    # Configuration
    "GetTcpRequest",
    "GetTcpResponse",
    "SetPayloadResultCode",
    "SetPayloadRequest",
    "SetPayloadResponse",
    "SetTcpRequest",
    "SetTcpResponse",
    "SetTcpResultCode",
    "Tcp",
    # Robot Instance
    "DriverParam",
    "RobotInstance",
    # Robot State
    "SetToNormalRequest",
    "SetToNormalResponse",
    "SetToFreedriveRequest",
    "SetToFreedriveResponse",
    "JointStates",
    "PositionState",
    "RobotStates",
    "RobotStatesStreamRequest",
    "CommandState",
    "CommandStateStreamRequest",
    "GetJointStatesRequest",
    "GetJointStatesResponse",
    "GetPositionStateRequest",
    "GetPositionStateResponse",
    "GetRobotStatesRequest",
    "GetRobotStatesResponse",
    "GetCommandStateRequest",
    "GetCommandStateResponse",
    "RobotOperationalState",
    "RobotSafetyState",
    "RobotConnectionState",
    # Joint Position
    "JointPosition",
    # Robot Requests
    "JointStatesStreamRequest",
    "PositionStreamRequest",
    "StopRequest",
    # Move
    "MoveRequest",
    "MoveResponse",
    "WaitForMoveCompletionRequest",
    "WaitForMoveCompletionResponse",
    "MoveResultCode",
    "MoveInterpolationRequest",
    "MoveInterpolationResponse",
    # Planning
    "PlanResultCode",
    "PlanRequest",
    "PlanResponse",
    "JointTrajectoryPoint",
    # Frames and Transforms
    "Frame",
    "Vector3d",
    "Quaternion",
    "CartesianMotion",
    "Twist",
    # Stop
    "StopResponse",
    "StopResultCode",
    # Move Segments
    "MoveType",
    "MoveSegment",
    "JointConstraints",
    "JointGoal",
    "CartesianConstraints",
    "CartesianGoal",
    # Kinematics
    "ForwardKinematicsRequest",
    "ForwardKinematicsResponse",
    "InverseKinematicsRequest",
    "InverseKinematicsResponse",
    "JointRangeConstraints",
    "KinResultCode",
    "InverseKinematicsBatchRequest",
    "InverseKinematicsBatchResponse",
    "IkSolver",
    "InverseKinematicsSolutions",
    # Robot Alarms and Notifications
    "RobotAlarm",
    "RobotAlarmStreamRequest",
    "Notification",
    "NotificationType",
    "SeverityLevel",
]
