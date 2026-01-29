from vention.robots.v1 import (
    frame_pb2,
    joint_position_pb2,
    joint_trajectory_point_pb2,
    mass_properties_pb2,
    move_interpolation_request_pb2,
    move_pb2,
    move_request_pb2,
    plan_request_pb2,
    robot_alarm_pb2,
    robot_configuration_pb2,
    robot_instance_pb2,
    robot_kinematics_pb2,
    robot_management_pb2,
    robot_requests_pb2,
    robot_state_pb2,
    stop_request_pb2,
)

from vrmcs.types import (
    CommandState,
    CommandStateStreamRequest,
    ForwardKinematicsRequest,
    ForwardKinematicsResponse,
    Frame,
    GetCommandStateRequest,
    GetCommandStateResponse,
    GetJointStatesRequest,
    GetJointStatesResponse,
    GetPositionStateRequest,
    GetPositionStateResponse,
    GetRobotInfoRequest,
    GetRobotStatesRequest,
    GetRobotStatesResponse,
    GetTcpRequest,
    GetTcpResponse,
    InverseKinematicsBatchRequest,
    InverseKinematicsBatchResponse,
    InverseKinematicsRequest,
    InverseKinematicsResponse,
    InverseKinematicsSolutions,
    JointPosition,
    JointStates,
    JointStatesStreamRequest,
    JointTrajectoryPoint,
    ListRobotsResponse,
    MoveInterpolationRequest,
    MoveInterpolationResponse,
    MoveRequest,
    MoveResponse,
    MoveSegment,
    MoveType,
    Notification,
    NotificationType,
    PlanRequest,
    PlanResponse,
    PositionState,
    PositionStreamRequest,
    Quaternion,
    RegisterRobotRequest,
    RegisterRobotResponse,
    RobotAlarm,
    RobotAlarmStreamRequest,
    RobotInfo,
    RobotStates,
    RobotStatesStreamRequest,
    SetPayloadRequest,
    SetPayloadResponse,
    SetTcpRequest,
    SetTcpResponse,
    SetToFreedriveRequest,
    SetToFreedriveResponse,
    SetToNormalRequest,
    SetToNormalResponse,
    SeverityLevel,
    StopRequest,
    StopResponse,
    StopResultCode,
    Tcp,
    Twist,
    UnregisterRobotRequest,
    UnregisterRobotResponse,
    Vector3d,
    WaitForMoveCompletionRequest,
    WaitForMoveCompletionResponse,
)


def register_robot_request_to_proto(
    request: RegisterRobotRequest,
) -> robot_management_pb2.RegisterRobotRequest:
    driver_params = robot_instance_pb2.DriverParam(
        params=request.robot_instance.driver_params.params
    )
    robot_instance = robot_instance_pb2.RobotInstance(
        name=request.robot_instance.name,
        id=request.robot_instance.id,
        robot_type=request.robot_instance.robot_type,
        driver=request.robot_instance.driver,
        driver_params=driver_params,
    )
    return robot_management_pb2.RegisterRobotRequest(robot_instance=robot_instance)


def register_robot_response_to_message(
    response: robot_management_pb2.RegisterRobotResponse,
) -> RegisterRobotResponse:
    return RegisterRobotResponse(
        success=response.success, error_message=response.error_message
    )


def set_to_normal_request_to_proto(
    request: SetToNormalRequest,
) -> robot_state_pb2.SetToNormalRequest:
    return robot_state_pb2.SetToNormalRequest(id=request.id)


def set_to_normal_response_to_message(
    response: robot_state_pb2.SetToNormalResponse,
) -> SetToNormalResponse:
    return SetToNormalResponse(success=response.success)


def set_to_freedrive_request_to_proto(
    request: SetToFreedriveRequest,
) -> robot_state_pb2.SetToFreedriveRequest:
    return robot_state_pb2.SetToFreedriveRequest(id=request.id, enable=request.enable)


def set_to_freedrive_response_to_message(
    response: robot_state_pb2.SetToFreedriveResponse,
) -> SetToFreedriveResponse:
    return SetToFreedriveResponse(success=response.success)


def move_segment_to_proto(segment: MoveSegment) -> move_pb2.MoveSegment:
    if segment.move_type == MoveType.MOVE_TYPE_JOINT:
        joint_goal = move_pb2.JointGoal(positions=segment.joint_goal.positions)
        joint_constraints = move_pb2.JointConstraints(
            velocities=segment.joint_constraints.velocities,
            accelerations=segment.joint_constraints.accelerations,
        )
        proto_segment = move_pb2.MoveSegment(
            move_type=move_pb2.MoveType.MOVE_TYPE_JOINT,
            joint_goal=joint_goal,
            joint_constraints=joint_constraints,
            blend_radius=segment.blend_radius,
        )
    elif segment.move_type == MoveType.MOVE_TYPE_CARTESIAN:
        pose = frame_pb2.Frame(
            position=frame_pb2.Vector3d(
                x=segment.cartesian_goal.pose.position.x,
                y=segment.cartesian_goal.pose.position.y,
                z=segment.cartesian_goal.pose.position.z,
            ),
            orientation=frame_pb2.Quaternion(
                x=segment.cartesian_goal.pose.orientation.x,
                y=segment.cartesian_goal.pose.orientation.y,
                z=segment.cartesian_goal.pose.orientation.z,
                w=segment.cartesian_goal.pose.orientation.w,
            ),
        )
        cartesian_goal = move_pb2.CartesianGoal(pose=pose)

        cartesian_constraints = move_pb2.CartesianConstraints()
        if segment.cartesian_constraints.velocity is not None:
            cartesian_constraints.velocity.linear = (
                segment.cartesian_constraints.velocity.linear
            )
            cartesian_constraints.velocity.angular = (
                segment.cartesian_constraints.velocity.angular
            )

        if segment.cartesian_constraints.acceleration is not None:
            cartesian_constraints.acceleration.linear = (
                segment.cartesian_constraints.acceleration.linear
            )
            cartesian_constraints.acceleration.angular = (
                segment.cartesian_constraints.acceleration.angular
            )

        proto_segment = move_pb2.MoveSegment(
            move_type=move_pb2.MoveType.MOVE_TYPE_CARTESIAN,
            cartesian_goal=cartesian_goal,
            cartesian_constraints=cartesian_constraints,
            blend_radius=segment.blend_radius,
        )
    else:
        raise ValueError(f"Unsupported move type: {segment.move_type}")
    return proto_segment


def move_request_to_proto(move_request: MoveRequest) -> move_request_pb2.MoveRequest:
    segments = []
    for segment in move_request.segments:
        segments.append(move_segment_to_proto(segment))
    return move_request_pb2.MoveRequest(id=move_request.id, segments=segments)


def move_response_to_message(response: move_request_pb2.MoveResponse) -> MoveResponse:
    return MoveResponse(
        result_code=response.result_code,
        duration=response.duration,
        error_segment=response.error_segment,
    )


def move_interpolation_request_to_proto(
    request: MoveInterpolationRequest,
) -> move_interpolation_request_pb2.MoveInterpolationRequest:
    points_proto = []
    for point in request.points:
        proto_point = joint_trajectory_point_pb2.JointTrajectoryPoint(
            positions=point.positions,
            velocities=point.velocities,
            accelerations=point.accelerations,
            time=point.time,
        )
        points_proto.append(proto_point)
    return move_interpolation_request_pb2.MoveInterpolationRequest(
        id=request.id, points=points_proto
    )


def move_interpolation_response_to_message(
    response: move_interpolation_request_pb2.MoveInterpolationResponse,
) -> MoveInterpolationResponse:
    return MoveInterpolationResponse(
        result_code=response.result_code,
        duration=response.duration,
        error_point=response.error_point,
    )


def plan_request_to_proto(request: PlanRequest) -> plan_request_pb2.PlanRequest:
    segments = []
    for segment in request.segments:
        segments.append(move_segment_to_proto(segment))
    return plan_request_pb2.PlanRequest(
        id=request.id,
        segments=segments,
        sampling_time=request.sampling_time,
        initial_joint_position=request.initial_joint_position,
    )


def plan_response_to_message(response: plan_request_pb2.PlanResponse) -> PlanResponse:
    joint_trajectory_points = []
    for point in response.joint_trajectory_points:
        proto_point = JointTrajectoryPoint(
            positions=point.positions,
            velocities=point.velocities,
            accelerations=point.accelerations,
            time=point.time.ToDatetime(),
        )
        joint_trajectory_points.append(proto_point)
    return PlanResponse(
        result_code=response.result_code,
        duration=response.duration,
        joint_trajectory_points=joint_trajectory_points,
        error_segment=response.error_segment,
    )


def wait_for_move_completion_request_to_proto(
    request: WaitForMoveCompletionRequest,
) -> move_request_pb2.WaitForMoveCompletionRequest:
    return move_request_pb2.WaitForMoveCompletionRequest(id=request.id)


def wait_for_move_completion_response_to_message(
    response: move_request_pb2.WaitForMoveCompletionResponse,
) -> WaitForMoveCompletionResponse:
    return WaitForMoveCompletionResponse(
        result_code=response.result_code, error_segment=response.error_segment
    )


def joint_states_stream_request_to_proto(
    request: JointStatesStreamRequest,
) -> robot_requests_pb2.JointStatesStreamRequest:
    max_frequency_hz = getattr(request, "max_frequency_hz", 0.0)
    return robot_requests_pb2.JointStatesStreamRequest(
        id=request.id, max_frequency_hz=max_frequency_hz
    )


def joint_states_to_message(
    response: robot_state_pb2.JointStates,
) -> JointStates:
    return JointStates(
        joint_position=JointPosition(positions=response.joint_position.positions),
        timestamp=response.timestamp.ToDatetime(),
    )


def robot_states_stream_request_to_proto(
    request: RobotStatesStreamRequest,
) -> robot_state_pb2.RobotStatesStreamRequest:
    return robot_state_pb2.RobotStatesStreamRequest(id=request.id)


def robot_states_to_message(states: robot_state_pb2.RobotStates) -> RobotStates:
    return RobotStates(
        operational_state=states.operational_state,
        safety_state=states.safety_state,
        connection_state=states.connection_state,
        timestamp=states.timestamp.ToDatetime(),
    )


def get_joint_states_request_to_proto(
    request: GetJointStatesRequest,
) -> robot_state_pb2.GetJointStatesRequest:
    return robot_state_pb2.GetJointStatesRequest(id=request.id)


def get_joint_states_response_to_message(
    response: robot_state_pb2.GetJointStatesResponse,
) -> GetJointStatesResponse:
    return GetJointStatesResponse(
        joint_state=joint_states_to_message(response.joint_state)
    )


def get_position_state_request_to_proto(
    request: GetPositionStateRequest,
) -> robot_state_pb2.GetPositionStateRequest:
    return robot_state_pb2.GetPositionStateRequest(id=request.id)


def get_position_state_response_to_message(
    response: robot_state_pb2.GetPositionStateResponse,
) -> GetPositionStateResponse:
    return GetPositionStateResponse(
        position_state=position_state_to_message(response.position_state)
    )


def get_robot_states_request_to_proto(
    request: GetRobotStatesRequest,
) -> robot_state_pb2.GetRobotStatesRequest:
    return robot_state_pb2.GetRobotStatesRequest(id=request.id)


def get_robot_states_response_to_message(
    response: robot_state_pb2.GetRobotStatesResponse,
) -> GetRobotStatesResponse:
    return GetRobotStatesResponse(
        robot_state=robot_states_to_message(response.robot_state)
    )


def get_command_state_request_to_proto(
    request: GetCommandStateRequest,
) -> robot_state_pb2.GetCommandStateRequest:
    return robot_state_pb2.GetCommandStateRequest(id=request.id)


def get_command_state_response_to_message(
    response: robot_state_pb2.GetCommandStateResponse,
) -> GetCommandStateResponse:
    return GetCommandStateResponse(
        command_state=command_state_to_message(response.command_state)
    )


def position_stream_request_to_proto(
    request: PositionStreamRequest,
) -> robot_requests_pb2.PositionStreamRequest:
    max_frequency_hz = getattr(request, "max_frequency_hz", 0.0)
    return robot_requests_pb2.PositionStreamRequest(
        id=request.id, max_frequency_hz=max_frequency_hz
    )


def position_state_to_message(
    response: robot_state_pb2.PositionState,
) -> PositionState:
    pose = Frame(
        position=Vector3d(
            x=response.cartesian_pose.position.x,
            y=response.cartesian_pose.position.y,
            z=response.cartesian_pose.position.z,
        ),
        orientation=Quaternion(
            x=response.cartesian_pose.orientation.x,
            y=response.cartesian_pose.orientation.y,
            z=response.cartesian_pose.orientation.z,
            w=response.cartesian_pose.orientation.w,
        ),
    )
    return PositionState(
        cartesian_pose=pose,
        joint_position=JointPosition(positions=response.joint_position.positions),
        timestamp=response.timestamp.ToDatetime(),
    )


def stop_request_to_proto(stop_req: StopRequest) -> robot_requests_pb2.StopRequest:
    return robot_requests_pb2.StopRequest(id=stop_req.id)


def stop_response_to_message(
    stop_res_proto: stop_request_pb2.StopResponse,
) -> StopResponse:
    return StopResponse(result_code=StopResultCode(stop_res_proto.result_code))


def list_robots_response_to_message(
    response: robot_management_pb2.ListRobotsResponse,
) -> ListRobotsResponse:
    robots = []
    for robot in response.robots:
        driver_params = robot_instance_pb2.DriverParam(
            params=robot.driver_params.params
        )
        robot_instance = RobotInfo(
            id=robot.id,
            name=robot.name,
            robot_type=robot.robot_type,
            joint_names=list(robot.joint_names),
            driver=robot.driver,
            driver_params=driver_params,
        )
        robots.append(robot_instance)
    return ListRobotsResponse(robots=robots)


def set_payload_request_to_proto(
    set_payload_req: SetPayloadRequest,
) -> robot_configuration_pb2.SetPayloadRequest:
    mass_props = mass_properties_pb2.MassProperties(
        mass=set_payload_req.mass_properties.mass,
        center_of_mass=frame_pb2.Vector3d(
            x=set_payload_req.mass_properties.center_of_mass.x,
            y=set_payload_req.mass_properties.center_of_mass.y,
            z=set_payload_req.mass_properties.center_of_mass.z,
        ),
        inertia_tensor=mass_properties_pb2.Inertia(
            ixx=set_payload_req.mass_properties.inertia_tensor.ixx,
            ixy=set_payload_req.mass_properties.inertia_tensor.ixy,
            ixz=set_payload_req.mass_properties.inertia_tensor.ixz,
            iyy=set_payload_req.mass_properties.inertia_tensor.iyy,
            iyz=set_payload_req.mass_properties.inertia_tensor.iyz,
            izz=set_payload_req.mass_properties.inertia_tensor.izz,
        ),
    )
    return robot_configuration_pb2.SetPayloadRequest(
        id=set_payload_req.id, mass_properties=mass_props
    )


def set_payload_response_to_message(
    set_payload_res_proto: robot_configuration_pb2.SetPayloadResponse,
) -> SetPayloadResponse:
    return SetPayloadResponse(result_code=set_payload_res_proto.result_code)


def unregister_robot_request_to_proto(
    request: UnregisterRobotRequest,
) -> robot_requests_pb2.UnregisterRobotRequest:
    return robot_requests_pb2.UnregisterRobotRequest(id=request.id)


def unregister_robot_response_to_message(
    response: robot_management_pb2.UnregisterRobotResponse,
) -> UnregisterRobotResponse:
    return UnregisterRobotResponse(
        success=response.success, error_message=response.error_message
    )


def get_robot_info_request_to_proto(
    request: GetRobotInfoRequest,
) -> robot_requests_pb2.GetRobotInfoRequest:
    return robot_requests_pb2.GetRobotInfoRequest(id=request.id)


def get_robot_info_response_to_message(
    response: robot_management_pb2.RobotInfo,
) -> RobotInfo:
    driver_params = robot_instance_pb2.DriverParam(params=response.driver_params.params)
    return RobotInfo(
        id=response.id,
        name=response.name,
        robot_type=response.robot_type,
        joint_names=list(response.joint_names),
        driver=response.driver,
        driver_params=driver_params,
    )


def command_state_stream_request_to_proto(
    request: CommandStateStreamRequest,
) -> robot_state_pb2.CommandStateStreamRequest:
    max_frequency_hz = getattr(request, "max_frequency_hz", 0.0)
    return robot_state_pb2.CommandStateStreamRequest(
        id=request.id, max_frequency_hz=max_frequency_hz
    )


def command_state_to_message(response: robot_state_pb2.CommandState) -> CommandState:
    return CommandState(
        timestamp_eval=response.timestamp_eval.ToDatetime(),
        timestamp_actual=response.timestamp_actual.ToDatetime(),
        joint_position=list(response.joint_position),
        joint_velocity=list(response.joint_velocity),
        joint_acceleration=list(response.joint_acceleration),
        cartesian_pose=Frame(
            position=Vector3d(
                x=response.cartesian_pose.position.x,
                y=response.cartesian_pose.position.y,
                z=response.cartesian_pose.position.z,
            ),
            orientation=Quaternion(
                x=response.cartesian_pose.orientation.x,
                y=response.cartesian_pose.orientation.y,
                z=response.cartesian_pose.orientation.z,
                w=response.cartesian_pose.orientation.w,
            ),
        ),
        cartesian_velocity=Twist(
            linear=Vector3d(
                x=response.cartesian_velocity.linear.x,
                y=response.cartesian_velocity.linear.y,
                z=response.cartesian_velocity.linear.z,
            ),
            angular=Vector3d(
                x=response.cartesian_velocity.angular.x,
                y=response.cartesian_velocity.angular.y,
                z=response.cartesian_velocity.angular.z,
            ),
        ),
        cartesian_acceleration=Twist(
            linear=Vector3d(
                x=response.cartesian_acceleration.linear.x,
                y=response.cartesian_acceleration.linear.y,
                z=response.cartesian_acceleration.linear.z,
            ),
            angular=Vector3d(
                x=response.cartesian_acceleration.angular.x,
                y=response.cartesian_acceleration.angular.y,
                z=response.cartesian_acceleration.angular.z,
            ),
        ),
    )


def inverse_kinematics_request_to_proto(
    request: InverseKinematicsRequest,
) -> robot_kinematics_pb2.InverseKinematicsRequest:
    joint_constraints = []
    if hasattr(request, "joint_constraints") and request.joint_constraints:
        for constraint in request.joint_constraints:
            joint_constraints.append(
                robot_kinematics_pb2.JointRangeConstraints(
                    joint_index=constraint.joint_index,
                    min_position=constraint.min_position,
                    max_position=constraint.max_position,
                )
            )

    return robot_kinematics_pb2.InverseKinematicsRequest(
        id=request.id,
        seed_joint_position=joint_position_pb2.JointPosition(
            positions=request.seed_joint_position.positions
        ),
        target_pose=frame_pb2.Frame(
            position=frame_pb2.Vector3d(
                x=request.target_pose.position.x,
                y=request.target_pose.position.y,
                z=request.target_pose.position.z,
            ),
            orientation=frame_pb2.Quaternion(
                x=request.target_pose.orientation.x,
                y=request.target_pose.orientation.y,
                z=request.target_pose.orientation.z,
                w=request.target_pose.orientation.w,
            ),
        ),
        joint_constraints=joint_constraints,
    )


def inverse_kinematics_solutions_to_message(
    solution: robot_kinematics_pb2.InverseKinematicsSolutions,
) -> InverseKinematicsSolutions:
    return InverseKinematicsSolutions(
        joint_positions=[
            JointPosition(positions=pos.positions) for pos in solution.joint_positions
        ]
    )


def inverse_kinematics_response_to_message(
    response: robot_kinematics_pb2.InverseKinematicsResponse,
) -> InverseKinematicsResponse:
    return InverseKinematicsResponse(
        joint_position=JointPosition(positions=response.joint_position.positions),
        result_code=response.result_code,
        error_message=response.error_message,
    )


def inverse_kinematics_batch_request_to_proto(
    request: InverseKinematicsBatchRequest,
) -> robot_kinematics_pb2.InverseKinematicsBatchRequest:

    target_poses = []
    for pose in request.target_poses:
        target_poses.append(
            frame_pb2.Frame(
                position=frame_pb2.Vector3d(
                    x=pose.position.x,
                    y=pose.position.y,
                    z=pose.position.z,
                ),
                orientation=frame_pb2.Quaternion(
                    x=pose.orientation.x,
                    y=pose.orientation.y,
                    z=pose.orientation.z,
                    w=pose.orientation.w,
                ),
            )
        )
    return robot_kinematics_pb2.InverseKinematicsBatchRequest(
        id=request.id,
        seed_joint_position=joint_position_pb2.JointPosition(
            positions=request.seed_joint_position.positions
        ),
        target_poses=target_poses,
        ik_solver=request.ik_solver,
        tolerance=request.tolerance,
        max_iterations=request.max_iterations
    )


def inverse_kinematics_batch_response_to_message(
    response: robot_kinematics_pb2.InverseKinematicsBatchResponse,
) -> InverseKinematicsBatchResponse:
    return InverseKinematicsBatchResponse(
        responses=[
            inverse_kinematics_response_to_message(resp)
            for resp in response.responses
        ],
        solutions=[
            inverse_kinematics_solutions_to_message(soln)
            for soln in response.solutions
        ]
    )


def forward_kinematics_request_to_proto(
    request: ForwardKinematicsRequest,
) -> robot_kinematics_pb2.ForwardKinematicsRequest:
    return robot_kinematics_pb2.ForwardKinematicsRequest(
        id=request.id,
        joint_position=joint_position_pb2.JointPosition(
            positions=request.joint_position.positions
        ),
    )


def forward_kinematics_response_to_message(
    response: robot_kinematics_pb2.ForwardKinematicsResponse,
) -> ForwardKinematicsResponse:
    return ForwardKinematicsResponse(
        cartesian_pose=Frame(
            position=Vector3d(
                x=response.cartesian_pose.position.x,
                y=response.cartesian_pose.position.y,
                z=response.cartesian_pose.position.z,
            ),
            orientation=Quaternion(
                x=response.cartesian_pose.orientation.x,
                y=response.cartesian_pose.orientation.y,
                z=response.cartesian_pose.orientation.z,
                w=response.cartesian_pose.orientation.w,
            ),
        ),
        result_code=response.result_code,
        error_message=response.error_message,
    )


def set_tcp_request_to_proto(
    request: SetTcpRequest,
) -> robot_configuration_pb2.SetTcpRequest:
    tcp_frame = frame_pb2.Frame(
        position=frame_pb2.Vector3d(
            x=request.tcp.frame.position.x,
            y=request.tcp.frame.position.y,
            z=request.tcp.frame.position.z,
        ),
        orientation=frame_pb2.Quaternion(
            x=request.tcp.frame.orientation.x,
            y=request.tcp.frame.orientation.y,
            z=request.tcp.frame.orientation.z,
            w=request.tcp.frame.orientation.w,
        ),
    )
    tcp = robot_configuration_pb2.Tcp(id=request.tcp.id, frame=tcp_frame)
    return robot_configuration_pb2.SetTcpRequest(id=request.id, tcp=tcp)


def set_tcp_response_to_message(
    response: robot_configuration_pb2.SetTcpResponse,
) -> SetTcpResponse:
    return SetTcpResponse(result=response.result)


def get_tcp_request_to_proto(
    request: GetTcpRequest,
) -> robot_configuration_pb2.GetTcpRequest:
    return robot_configuration_pb2.GetTcpRequest(id=request.id)


def get_tcp_response_to_message(
    response: robot_configuration_pb2.GetTcpResponse,
) -> GetTcpResponse:
    tcp_frame = Frame(
        position=Vector3d(
            x=response.tcp.frame.position.x,
            y=response.tcp.frame.position.y,
            z=response.tcp.frame.position.z,
        ),
        orientation=Quaternion(
            x=response.tcp.frame.orientation.x,
            y=response.tcp.frame.orientation.y,
            z=response.tcp.frame.orientation.z,
            w=response.tcp.frame.orientation.w,
        ),
    )
    tcp = Tcp(id=response.tcp.id, frame=tcp_frame)
    return GetTcpResponse(tcp=tcp)


def robot_alarm_stream_request_to_proto(
    request: RobotAlarmStreamRequest,
) -> robot_alarm_pb2.RobotAlarmStreamRequest:
    return robot_alarm_pb2.RobotAlarmStreamRequest(id=request.id)


def robot_alarm_to_message(response: robot_alarm_pb2.RobotAlarm) -> RobotAlarm:
    notifications = []
    for notification in response.notifications:
        notifications.append(
            Notification(
                timestamp=notification.timestamp.ToDatetime(),
                type=NotificationType(notification.type),
                message=notification.message,
                raw_message=notification.raw_message,
                code=notification.code,
                severity=SeverityLevel(notification.severity),
            )
        )
    return RobotAlarm(notifications=notifications)
