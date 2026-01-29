import logging
import threading
from typing import Callable, Optional

import grpc
from google.protobuf import empty_pb2
from vention.robots.v1 import robot_service_pb2_grpc

from vrmcs.conversions import (
    command_state_stream_request_to_proto,
    command_state_to_message,
    forward_kinematics_request_to_proto,
    forward_kinematics_response_to_message,
    get_command_state_request_to_proto,
    get_command_state_response_to_message,
    get_joint_states_request_to_proto,
    get_joint_states_response_to_message,
    get_position_state_request_to_proto,
    get_position_state_response_to_message,
    get_robot_info_request_to_proto,
    get_robot_info_response_to_message,
    get_robot_states_request_to_proto,
    get_robot_states_response_to_message,
    get_tcp_request_to_proto,
    get_tcp_response_to_message,
    inverse_kinematics_batch_request_to_proto,
    inverse_kinematics_batch_response_to_message,
    inverse_kinematics_request_to_proto,
    inverse_kinematics_response_to_message,
    joint_states_stream_request_to_proto,
    joint_states_to_message,
    list_robots_response_to_message,
    move_interpolation_request_to_proto,
    move_interpolation_response_to_message,
    move_request_to_proto,
    move_response_to_message,
    plan_request_to_proto,
    plan_response_to_message,
    position_state_to_message,
    position_stream_request_to_proto,
    register_robot_request_to_proto,
    register_robot_response_to_message,
    robot_alarm_stream_request_to_proto,
    robot_alarm_to_message,
    robot_states_stream_request_to_proto,
    robot_states_to_message,
    set_payload_request_to_proto,
    set_payload_response_to_message,
    set_tcp_request_to_proto,
    set_tcp_response_to_message,
    set_to_freedrive_request_to_proto,
    set_to_freedrive_response_to_message,
    set_to_normal_request_to_proto,
    set_to_normal_response_to_message,
    stop_request_to_proto,
    stop_response_to_message,
    unregister_robot_request_to_proto,
    unregister_robot_response_to_message,
    wait_for_move_completion_request_to_proto,
    wait_for_move_completion_response_to_message,
)
from vrmcs.types import (
    CommandState,
    CommandStateStreamRequest,
    ForwardKinematicsRequest,
    ForwardKinematicsResponse,
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
    JointStates,
    JointStatesStreamRequest,
    KinResultCode,
    ListRobotsResponse,
    MoveInterpolationRequest,
    MoveInterpolationResponse,
    MoveRequest,
    MoveResponse,
    MoveResultCode,
    PlanRequest,
    PlanResponse,
    PlanResultCode,
    PositionState,
    PositionStreamRequest,
    RegisterRobotRequest,
    RegisterRobotResponse,
    RobotAlarm,
    RobotAlarmStreamRequest,
    RobotInfo,
    RobotStates,
    RobotStatesStreamRequest,
    SetPayloadRequest,
    SetPayloadResponse,
    SetPayloadResultCode,
    SetTcpRequest,
    SetTcpResponse,
    SetTcpResultCode,
    SetToFreedriveRequest,
    SetToFreedriveResponse,
    SetToNormalRequest,
    SetToNormalResponse,
    StopRequest,
    StopResponse,
    StopResultCode,
    UnregisterRobotRequest,
    UnregisterRobotResponse,
    WaitForMoveCompletionRequest,
    WaitForMoveCompletionResponse,
)

logger = logging.getLogger("vrmcs-client")
logger.addHandler(logging.NullHandler())


class VRMCSClient:
    """
    A client for interacting with the Vention Robot Motion Control System (VRMCS).

    The client communicates with the VRMCS server using gRPC and supports operations
    such as:
    - Robot registration and management
    - Movement execution and planning
    - Operating mode control (normal/freedrive)
    - Interpolated trajectory execution
    """

    def __init__(self, channel_url: str) -> None:
        """
        Initialize the VRMCS client with a gRPC channel.

        Args:
            channel_url (str): The URL of the VRMCS server (e.g., "localhost:50051").
                             This should include the host and port where the VRMCS
                             gRPC server is listening.
        """
        self.channel = grpc.insecure_channel(channel_url)
        self.stub = robot_service_pb2_grpc.RobotServiceStub(self.channel)

        self.joint_stream_thread: Optional[threading.Thread] = None

        self.position_stream_thread: Optional[threading.Thread] = None

        self.states_stream_thread: Optional[threading.Thread] = None

        self.command_state_stream_thread: Optional[threading.Thread] = None

        self.robot_alarm_stream_thread: Optional[threading.Thread] = None

    def register_robot(
        self, register_robot_req: RegisterRobotRequest
    ) -> RegisterRobotResponse:
        """
        Register a robot instance with the VRMCS server.

        This method registers a new robot with the system, making it available
        for subsequent control operations. The robot must be properly configured
        before registration.

        Args:
            register_robot_req (RegisterRobotRequest): The robot registration request
                containing robot instance details, configuration, and other metadata
                required for registration.

        Returns:
            RegisterRobotResponse: Response containing registration status and any
                error information if registration failed.

        Raises:
            grpc.RpcError: If there's a communication error with the VRMCS server.
                The error is caught and converted to a failed response.

        Note:
            Check the response.success field to determine if registration was successful.
        """
        register_robot_req_proto = register_robot_request_to_proto(register_robot_req)
        try:
            register_robot_res_proto = self.stub.RegisterRobot(register_robot_req_proto)
            register_robot_res = register_robot_response_to_message(
                register_robot_res_proto
            )
            if register_robot_res.success:
                logger.info(
                    f"Robot '{register_robot_req.robot_instance.name}' "
                    + f"with ID '{register_robot_req.robot_instance.id}' registered successfully"
                )
            else:
                logger.error(
                    f"Failed to register robot '{register_robot_req.robot_instance.name}' "
                    + f"with ID '{register_robot_req.robot_instance.id}': {register_robot_res.error_message}"
                )
        except grpc.RpcError as e:
            logger.error(f"gRPC error during RegisterRobot: {e.code()} - {e.details()}")
            register_robot_res = RegisterRobotResponse(
                success=False, error_message=str(e)
            )
        return register_robot_res

    def stop(self, stop_req: StopRequest) -> StopResponse:
        """
        Sends a stop command to the robot.
        This method instructs the robot to stop its current motion.

        Args:
            stop_req (StopRequest): The stop request containing the robot ID.
        Returns:
            StopResponse: The response from the server containing the result of the stop operation.
            This includes a result code indicating success or failure.
        Raises:
            May raise gRPC exceptions if communication with the server fails.
        """
        stop_res_proto = self.stub.Stop(stop_request_to_proto(stop_req))
        stop_res = stop_response_to_message(stop_res_proto)
        if stop_res.result_code == StopResultCode.STOP_RESULT_CODE_SUCCESS:
            logger.info(
                f"Stop command executed successfully for robot with ID '{stop_req.id}'"
            )
        else:
            logger.error(
                f"Stop command failed for robot with ID '{stop_req.id}' with result code {stop_res.result_code.name}"
            )
        return stop_res

    def set_to_normal(
        self, set_to_normal_req: SetToNormalRequest
    ) -> SetToNormalResponse:
        """
        Set a robot to normal operation state.

        This method transitions a robot from any special operating mode (such as
        freedrive or error state) back to normal operation mode, allowing it to
        execute movement commands and other standard operations.

        Args:
            set_to_normal_req (SetToNormalRequest): Request containing the robot ID
                and any additional parameters needed to set the robot to normal state.

        Returns:
            SetToNormalResponse: Response indicating whether the state change was
                successful and any error information if it failed.

        Note:
            The robot must be properly initialized and connected to transition
            to normal state successfully.
        """
        set_to_normal_req_proto = set_to_normal_request_to_proto(set_to_normal_req)
        set_to_normal_res_proto = self.stub.SetToNormal(set_to_normal_req_proto)
        set_to_normal_res = set_to_normal_response_to_message(set_to_normal_res_proto)
        if set_to_normal_res.success:
            logger.info(
                f"Robot with ID '{set_to_normal_req.id}' set to normal operation state"
            )
        else:
            logger.error(
                f"Failed to set robot with ID '{set_to_normal_req.id}' to normal operation state"
            )
        return set_to_normal_res

    def set_to_freedrive(
        self, set_to_freedrive_req: SetToFreedriveRequest
    ) -> SetToFreedriveResponse:
        """
        Enable or disable freedrive mode for a robot.

        Freedrive mode allows manual manipulation of the robot arm by disabling
        motor torques while maintaining position awareness. This is useful for
        manual teaching, positioning, or when physical interaction with the robot
        is required.

        Args:
            set_to_freedrive_req (SetToFreedriveRequest): Request containing the
                robot ID and enable flag. Set enable=True to activate freedrive
                mode, or enable=False to deactivate it.

        Returns:
            SetToFreedriveResponse: Response indicating whether the mode change was
                successful and any error information if it failed.

        Warning:
            When freedrive mode is enabled, the robot cannot execute movement
            commands. Ensure the robot is in a safe position before enabling
            freedrive mode.
        """
        set_to_freedrive_req_proto = set_to_freedrive_request_to_proto(
            set_to_freedrive_req
        )
        set_to_freedrive_res_proto = self.stub.SetToFreedrive(
            set_to_freedrive_req_proto
        )
        set_to_freedrive_res = set_to_freedrive_response_to_message(
            set_to_freedrive_res_proto
        )
        if set_to_freedrive_res.success:
            state = "enabled" if set_to_freedrive_req.enable else "disabled"
            logger.info(
                f"Freedrive mode {state} for robot with ID '{set_to_freedrive_req.id}'"
            )
        else:
            logger.error(
                f"Failed to change freedrive mode for robot with ID '{set_to_freedrive_req.id}'"
            )
        return set_to_freedrive_res

    def move(self, move_req: MoveRequest) -> MoveResponse:
        """
        Execute a robot movement command.

        This method sends a movement request to the robot, which can include
        various types of motion such as joint moves, Cartesian moves, or
        complex trajectories. The method blocks until the movement is completed
        or fails.

        Args:
            move_req (MoveRequest): The movement request containing target positions,
                motion parameters, robot ID, and other movement specifications.

        Returns:
            MoveResponse: Response containing the execution result, duration,
                and error information if the movement failed. Check result_code
                for success/failure status.

        Note:
            - The robot must be in normal operation mode to execute moves
            - Failed movements will include error_segment information indicating
              where the failure occurred in multi-segment moves
            - Duration is reported in seconds for successful moves
        """
        move_req_proto = move_request_to_proto(move_req)
        move_res_proto = self.stub.Move(move_req_proto)
        move_res = move_response_to_message(move_res_proto)
        if move_res.result_code == PlanResultCode.PLAN_RESULT_CODE_SUCCESS:
            logger.info(
                f"Move command executed successfully in {move_res.duration} seconds"
            )
        else:
            logger.error(
                f"Move command failed at segment {move_res.error_segment} with plan result code {move_res.result_code}"
            )
        return move_res

    def plan(self, plan_req: PlanRequest) -> PlanResponse:
        """
        Plan a robot trajectory without executing it.

        This method generates and validates a motion plan for the specified
        movement without actually executing the robot motion. This is useful
        for verifying that a planned movement is feasible before execution,
        or for pre-computing trajectories.

        Args:
            plan_req (PlanRequest): The planning request containing target positions,
                motion parameters, robot ID, and constraints for trajectory planning.

        Returns:
            PlanResponse: Response containing the planning result, estimated duration,
                and error information if planning failed. Check result_code for
                success/failure status.

        Note:
            - Failed plans will include error_segment information indicating
              where the failure occurred in multi-segment plans
            - Planning does not change robot state or position
            - Successful planning provides duration estimates for the planned motion
        """
        plan_req_proto = plan_request_to_proto(plan_req)
        plan_res_proto = self.stub.Plan(plan_req_proto)
        plan_res = plan_response_to_message(plan_res_proto)
        if plan_res.result_code == PlanResultCode.PLAN_RESULT_CODE_SUCCESS:
            logger.info(
                f"Plan command executed successfully in {plan_res.duration} seconds"
            )
        else:
            logger.error(
                f"Plan command failed at segment {plan_res.error_segment} with plan result code {plan_res.result_code}"
            )
        return plan_res

    def wait_for_move_completion(
        self, request: WaitForMoveCompletionRequest
    ) -> WaitForMoveCompletionResponse:
        """
        Block until the robot completes its current movement.

        This method continuously checks the robot's status and blocks execution
        until the robot has finished executing its current move command. This is
        useful for ensuring that subsequent commands are not sent until the
        robot is idle.
        Args:
            request (WaitForMoveCompletionRequest): Request containing the robot ID
                for which to wait for movement completion.
        Returns:
            WaitForMoveCompletionResponse: Response with error code indicating whether the move
             was completed successfully and any error information if it failed.
        """
        wait_req_proto = wait_for_move_completion_request_to_proto(request)
        wait_res_proto = self.stub.WaitForMoveCompletion(wait_req_proto)
        wait_res = wait_for_move_completion_response_to_message(wait_res_proto)
        if wait_res.result_code == MoveResultCode.MOVE_RESULT_CODE_SUCCESS:
            logger.info(
                f"Robot with ID '{request.id}' has completed its movement and is now idle"
            )
        else:
            logger.error(
                f"Failed while waiting for robot with ID '{request.id}' to complete movement"
            )
        return wait_res

    def _joint_stream_consume(
        self,
        stream_req: JointStatesStreamRequest,
        on_data: Callable[[JointStates], None],
    ):
        self.joint_stream_iterator = self.stub.JointStatesStream(
            joint_states_stream_request_to_proto(stream_req)
        )
        try:
            for response in self.joint_stream_iterator:
                result: JointStates = joint_states_to_message(response)
                try:
                    on_data(result)
                except Exception as e:
                    logger.error(f"Error in joint states callback: {e}")
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.CANCELLED:
                logger.info("Joint stream cancelled successfully.")
            else:
                logger.error(
                    f"gRPC error during JointStatesStream: {e.code()} - {e.details()}"
                )

    def joint_stream_subscribe(
        self,
        stream_req: JointStatesStreamRequest,
        on_data: Callable[[JointStates], None],
    ):
        """
        Subscribe to a stream of joint states.

        This method starts a background thread that consumes joint state data from the server
        and calls the provided callback function for each update.

        Args:
            stream_req (JointStatesStreamRequest): Configuration for the joint states stream.
                Includes id and optional max_frequency_hz (0 = no limit).
            on_data (Callable[[JointStates], None]): Callback function that will be called
                with each JointStates update. Any exceptions raised in the callback will be
                logged but won't stop the stream.

        Example:
            ```python
            def handle_joint_states(joint_states: JointStates):
                print(f"Joint positions: {joint_states.joint_position.positions}")

            client.joint_stream_subscribe(
                JointStatesStreamRequest(id="robot_1"),
                on_data=handle_joint_states
            )
            ```

        Note:
            This method starts a background thread. To stop the stream, call
            joint_stream_unsubscribe().
        """

        if (self.joint_stream_thread is None) or (
            not self.joint_stream_thread.is_alive()
        ):
            self.joint_stream_thread = threading.Thread(
                target=lambda: self._joint_stream_consume(stream_req, on_data),
                daemon=True,  # Daemon thread won't block program exit
            )
            self.joint_stream_thread.start()
        else:
            logger.warning(
                "Joint stream is already active. Subscription request ignored."
            )

    def joint_stream_unsubscribe(self):
        """
        Unsubscribes from the joint stream.

        This method stops the joint stream thread by cancelling the gRPC iterator,
        which causes the streaming loop to exit gracefully, then waits for the thread to terminate.

        Returns:
            None
        """
        if self.joint_stream_thread:
            if self.joint_stream_thread.is_alive() and self.joint_stream_iterator:
                self.joint_stream_iterator.cancel()
            self.joint_stream_thread.join()
            if self.joint_stream_thread.is_alive():
                logger.warning(
                    "Joint stream thread did not exit cleanly within timeout"
                )
            self.joint_stream_thread = None
            self.joint_stream_iterator = None

    def _position_stream_consume(
        self,
        stream_req: PositionStreamRequest,
        on_data: Callable[[PositionState], None],
    ):
        self.position_stream_iterator = self.stub.PositionStream(
            position_stream_request_to_proto(stream_req)
        )
        try:
            for response in self.position_stream_iterator:
                result: PositionState = position_state_to_message(response)
                try:
                    on_data(result)
                except Exception as e:
                    logger.error(f"Error in position state callback: {e}")
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.CANCELLED:
                logger.info("Position stream cancelled successfully.")
            else:
                logger.error(
                    f"gRPC error during PositionStream: {e.code()} - {e.details()}"
                )

    def position_stream_subscribe(
        self,
        stream_req: PositionStreamRequest,
        on_data: Callable[[PositionState], None],
    ):
        """
        Subscribe to a position data stream from the VRMCS server.

        This method starts a background thread that consumes position data from the server
        and calls the provided callback function for each update.

        Args:
            stream_req (PositionStreamRequest): The request parameters for the position stream.
                Includes id and optional max_frequency_hz (0 = no limit).

            on_data (Callable[[PositionState], None]): Callback function that will be called
                with each PositionState update. Any exceptions raised in the callback will be
                logged but won't stop the stream.

        Example:
            ```python
            def handle_position(position_state: PositionState):
                pose = position_state.cartesian_pose
                print(f"Position: x={pose.position.x}, y={pose.position.y}, z={pose.position.z}")

            client.position_stream_subscribe(
                PositionStreamRequest(id="robot_1"),
                on_data=handle_position
            )
            ```

        Note:
            To stop the stream, call the position_stream_unsubscribe method.
        """

        if (self.position_stream_thread is None) or (
            not self.position_stream_thread.is_alive()
        ):
            self.position_stream_thread = threading.Thread(
                target=lambda: self._position_stream_consume(stream_req, on_data),
                daemon=True,  # Daemon thread won't block program exit
            )
            self.position_stream_thread.start()
        else:
            logger.warning(
                "Position stream is already active. Subscription request ignored."
            )

    def position_stream_unsubscribe(self):
        """
        Unsubscribe from the position stream.

        This method stops the position streaming thread by cancelling the gRPC iterator,
        which causes the streaming loop to exit gracefully, then waits for the thread to terminate.

        Returns:
            None
        """
        if self.position_stream_thread:
            if self.position_stream_thread.is_alive() and self.position_stream_iterator:
                self.position_stream_iterator.cancel()
            self.position_stream_thread.join()
            if self.position_stream_thread.is_alive():
                logger.warning(
                    "Position stream thread did not exit cleanly within timeout"
                )
            self.position_stream_thread = None
            self.position_stream_iterator = None

    def _states_stream_consume(
        self,
        stream_req: RobotStatesStreamRequest,
        on_data: Callable[[RobotStates], None],
    ):
        self.states_stream_iterator = self.stub.RobotStatesStream(
            robot_states_stream_request_to_proto(stream_req)
        )
        try:
            for response in self.states_stream_iterator:
                result: RobotStates = robot_states_to_message(response)
                try:
                    on_data(result)
                except Exception as e:
                    logger.error(f"Error in robot states callback: {e}")
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.CANCELLED:
                logger.info("Robot states stream cancelled successfully.")
            else:
                logger.error(
                    f"gRPC error during RobotStatesStream: {e.code()} - {e.details()}"
                )

    def states_stream_subscribe(
        self,
        stream_req: RobotStatesStreamRequest,
        on_data: Callable[[RobotStates], None],
    ):
        """
        Subscribe to a stream of robot state changes.

        This method starts a background thread that consumes robot state data from the server
        and calls the provided callback function for each state change. Unlike position/joint
        streams which send continuous updates, this is an event-driven stream that only sends
        messages when the robot's state actually changes (connection_state, operational_state,
        or safety_state).

        Args:
            stream_req (RobotStatesStreamRequest): Configuration for the robot states stream
                including robot ID.
            on_data (Callable[[RobotStates], None]): Callback function that will be called
                with each RobotStates update. Any exceptions raised in the callback will be
                logged but won't stop the stream.

        Example:
            ```python
            def handle_state_change(states: RobotStates):
                print(f"State changed: {states.operational_state.name}")

            client.states_stream_subscribe(
                RobotStatesStreamRequest(id="robot_1"),
                on_data=handle_state_change
            )
            ```

        Note:
            To stop the stream, call states_stream_unsubscribe().
            Only one robot states stream can be active at a time per client.
        """
        if (self.states_stream_thread is None) or (
            not self.states_stream_thread.is_alive()
        ):
            self.states_stream_thread = threading.Thread(
                target=lambda: self._states_stream_consume(stream_req, on_data),
                daemon=True,  # Daemon thread won't block program exit
            )
            self.states_stream_thread.start()
        else:
            logger.warning(
                "States stream is already active. Subscription request ignored."
            )

    def states_stream_unsubscribe(self):
        """
        Unsubscribe from the robot states stream.

        This method stops the robot states streaming thread by cancelling the gRPC iterator,
        which causes the streaming loop to exit gracefully, then waits for the thread to terminate.

        Returns:
            None
        """
        if self.states_stream_thread:
            if self.states_stream_thread.is_alive() and self.states_stream_iterator:
                self.states_stream_iterator.cancel()
            self.states_stream_thread.join()
            if self.states_stream_thread.is_alive():
                logger.warning(
                    "States stream thread did not exit cleanly within timeout"
                )
            self.states_stream_thread = None
            self.states_stream_iterator = None

    def move_interpolation(
        self, move_interp_req: MoveInterpolationRequest
    ) -> MoveInterpolationResponse:
        """
        Execute an interpolated trajectory movement.

        This method executes a pre-defined trajectory consisting of multiple
        waypoints with interpolated motion between them. The robot follows
        a smooth path through all specified points, which is useful for
        complex motions and precise trajectory following.

        Args:
            move_interp_req (MoveInterpolationRequest): Request containing the
                trajectory points, interpolation parameters, timing constraints,
                robot ID, and other trajectory specifications.

        Returns:
            MoveInterpolationResponse: Response containing execution result,
                duration, and error information if the trajectory failed.
                Check result_code for success/failure status.

        Note:
            - The robot must be in normal operation mode to execute trajectories
            - Failed trajectories will include error_point information indicating
              which waypoint caused the failure
            - Duration is reported in seconds for successful trajectory planning
        """
        move_interp_req_proto = move_interpolation_request_to_proto(move_interp_req)
        move_interp_res_proto = self.stub.MoveInterpolation(move_interp_req_proto)
        move_interp_res = move_interpolation_response_to_message(move_interp_res_proto)
        if move_interp_res.result_code == PlanResultCode.PLAN_RESULT_CODE_SUCCESS:
            logger.info(
                f"Trajectory started successfully in {move_interp_res.duration} seconds"
            )
        else:
            logger.error(
                f"Trajectory plan failed at point {move_interp_res.error_point} "
                + f"with plan result code {move_interp_res.result_code}"
            )
        return move_interp_res

    def list_robots(self) -> ListRobotsResponse:
        """
        Retrieve a list of all registered robots from the VRMCS server.

        """
        list_robots_res_proto = self.stub.ListRobots(empty_pb2.Empty())
        return list_robots_response_to_message(list_robots_res_proto)

    def set_payload(self, set_payload_req: SetPayloadRequest) -> SetPayloadResponse:
        """
        Set the payload mass properties for a robot.

        This method configures the robot's payload properties, which affects dynamics
        calculations and motion planning. Proper payload configuration is essential
        for accurate motion control and safety.

        Args:
            set_payload_req (SetPayloadRequest): Request containing the robot ID
                and mass properties (mass, center of mass, inertia tensor).

        Returns:
            SetPayloadResponse: Response indicating whether the payload was set
                successfully and result code.
        """
        set_payload_req_proto = set_payload_request_to_proto(set_payload_req)
        set_payload_res_proto = self.stub.SetPayload(set_payload_req_proto)
        set_payload_res: SetPayloadResponse = set_payload_response_to_message(
            set_payload_res_proto
        )
        if (
            set_payload_res.result_code
            == SetPayloadResultCode.SET_PAYLOAD_RESULT_CODE_SUCCESS
        ):
            logger.info("Set payload command executed successfully")
        else:
            logger.error(
                f"Set payload command failed with result code {set_payload_res.result_code}"
            )
        return set_payload_res

    def unregister_robot(
        self, unregister_robot_req: UnregisterRobotRequest
    ) -> UnregisterRobotResponse:
        """
        Unregister a robot from the VRMCS server.

        This method removes a previously registered robot from the system, freeing
        up resources and making it unavailable for control operations.

        Args:
            unregister_robot_req (UnregisterRobotRequest): Request containing the
                robot ID to unregister.

        Returns:
            UnregisterRobotResponse: Response indicating success or failure with
                error message if unregistration failed.

        Raises:
            grpc.RpcError: If there's a communication error with the VRMCS server.
                The error is caught and converted to a failed response.
        """
        unregister_robot_req_proto = unregister_robot_request_to_proto(
            unregister_robot_req
        )
        try:
            unregister_robot_res_proto = self.stub.UnregisterRobot(
                unregister_robot_req_proto
            )
            unregister_robot_res = unregister_robot_response_to_message(
                unregister_robot_res_proto
            )
            if unregister_robot_res.success:
                logger.info(
                    f"Robot with ID '{unregister_robot_req.id}' unregistered successfully"
                )
            else:
                logger.error(
                    f"Failed to unregister robot with ID '{unregister_robot_req.id}': {unregister_robot_res.error_message}"
                )
        except grpc.RpcError as e:
            logger.error(
                f"gRPC error during UnregisterRobot: {e.code()} - {e.details()}"
            )
            unregister_robot_res = UnregisterRobotResponse(
                success=False, error_message=str(e)
            )
        return unregister_robot_res

    def get_robot_info(self, get_robot_info_req: GetRobotInfoRequest) -> RobotInfo:
        """
        Get detailed information about a registered robot.

        This method retrieves configuration and status information for a specific
        robot including its name, type, and joint configuration.

        Args:
            get_robot_info_req (GetRobotInfoRequest): Request containing the robot ID.

        Returns:
            RobotInfo: Information about the robot including id, name,
                robot_type, and joint_names.

        Raises:
            grpc.RpcError: If there's a communication error with the VRMCS server
                or if the robot is not found.
        """
        get_robot_info_req_proto = get_robot_info_request_to_proto(get_robot_info_req)
        get_robot_info_res_proto = self.stub.GetRobotInfo(get_robot_info_req_proto)
        robot_info = get_robot_info_response_to_message(get_robot_info_res_proto)
        logger.info(
            f"Retrieved info for robot '{robot_info.name}' (ID: '{robot_info.id}')"
        )
        return robot_info

    def _command_state_stream_consume(
        self,
        stream_req: CommandStateStreamRequest,
        on_data: Callable[[CommandState], None],
    ):
        self.command_state_stream_iterator = self.stub.CommandStateStream(
            command_state_stream_request_to_proto(stream_req)
        )
        try:
            for response in self.command_state_stream_iterator:
                result: CommandState = command_state_to_message(response)
                try:
                    on_data(result)
                except Exception as e:
                    logger.error(f"Error in command state callback: {e}")
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.CANCELLED:
                logger.info("Command state stream cancelled successfully.")
            else:
                logger.error(
                    f"gRPC error during CommandStateStream: {e.code()} - {e.details()}"
                )

    def command_state_stream_subscribe(
        self,
        stream_req: CommandStateStreamRequest,
        on_data: Callable[[CommandState], None],
    ):
        """
        Subscribe to a stream of robot command states.

        This method starts a background thread that consumes command state data from the server
        and calls the provided callback function for each update. Command states include joint
        and Cartesian positions, velocities, and accelerations being commanded to the robot.

        Args:
            stream_req (CommandStateStreamRequest): Configuration for the command
                state stream including id and optional max_frequency_hz (0 = no limit).

            on_data (Callable[[CommandState], None]): Callback function that will be called
                with each CommandState update. Any exceptions raised in the callback will be
                logged but won't stop the stream.

        Example:
            ```python
            def handle_command_state(cmd_state: CommandState):
                print(f"Command joint positions: {cmd_state.joint_position.positions}")

            client.command_state_stream_subscribe(
                CommandStateStreamRequest(id="robot_1"),
                on_data=handle_command_state
            )
            ```

        Note:
            To stop the stream, call command_state_stream_unsubscribe().
            Only one command state stream can be active at a time per client.
        """
        if (self.command_state_stream_thread is None) or (
            not self.command_state_stream_thread.is_alive()
        ):
            self.command_state_stream_thread = threading.Thread(
                target=lambda: self._command_state_stream_consume(stream_req, on_data),
                daemon=True,  # Daemon thread won't block program exit
            )
            self.command_state_stream_thread.start()
        else:
            logger.warning(
                "Command state stream is already active. Subscription request ignored."
            )

    def command_state_stream_unsubscribe(self):
        """
        Unsubscribe from the command state stream.

        This method stops the command state streaming thread by cancelling the gRPC iterator,
        which causes the streaming loop to exit gracefully, then waits for the thread to terminate.

        Returns:
            None
        """
        if self.command_state_stream_thread:
            if (
                self.command_state_stream_thread.is_alive()
                and self.command_state_stream_iterator
            ):
                self.command_state_stream_iterator.cancel()
            self.command_state_stream_thread.join()
            if self.command_state_stream_thread.is_alive():
                logger.warning(
                    "Command state stream thread did not exit cleanly within timeout"
                )
            self.command_state_stream_thread = None
            self.command_state_stream_iterator = None

    def inverse_kinematics_batch(
        self, ik_req: InverseKinematicsBatchRequest
    ) -> InverseKinematicsBatchResponse:
        """
        Calculate joint positions for a list of given Cartesian poses (Inverse Kinematics).

        A seed joint position is used as a starting point for the IK solver.
        The initial joint position is used for all target poses.

        Args:
            ik_req (InverseKinematicsBatchRequest): Request containing robot ID, seed
                joint position in radians, and a list of target Cartesian poses.

        Returns:
            InverseKinematicsBatchResponse: Response containing computed a list of joint positions,
                result code, and error message if computation failed. Each index of list corresponds
                to the target poses in the request.

        Note:
            - Multiple solutions may exist; the returned solution will be closest
              to the seed position
            - May fail if target pose is unreachable, in singularity, causes
              self-collision, or exceeds joint limits
        """
        ik_req_proto = inverse_kinematics_batch_request_to_proto(ik_req)
        ik_res_proto = self.stub.InverseKinematicsBatch(ik_req_proto)
        return inverse_kinematics_batch_response_to_message(ik_res_proto)

    def inverse_kinematics(
        self, ik_req: InverseKinematicsRequest
    ) -> InverseKinematicsResponse:
        """
        Calculate joint positions for a given Cartesian pose (Inverse Kinematics).

        This method computes the joint configuration needed to achieve a specified
        TCP pose. A seed joint position is used as a starting point for the IK solver.

        Args:
            ik_req (InverseKinematicsRequest): Request containing robot ID, seed
                joint position, target Cartesian pose, and optional joint_constraints
                (list of JointRangeConstraints to limit specific joint angles).

        Returns:
            InverseKinematicsResponse: Response containing computed joint positions,
                result code, and error message if computation failed.

        Note:
            - Multiple solutions may exist; the returned solution will be closest
              to the seed position
            - May fail if target pose is unreachable, in singularity, causes
              self-collision, or exceeds joint limits
            - Joint constraints can be specified to limit specific joints to custom ranges
        """
        ik_req_proto = inverse_kinematics_request_to_proto(ik_req)
        ik_res_proto = self.stub.InverseKinematics(ik_req_proto)
        ik_res = inverse_kinematics_response_to_message(ik_res_proto)
        if ik_res.result_code == KinResultCode.KIN_RESULT_CODE_SUCCESS:
            logger.info(
                f"Inverse kinematics computed successfully for robot '{ik_req.id}'"
            )
        else:
            logger.error(
                f"Inverse kinematics failed for robot '{ik_req.id}': {ik_res.error_message}"
            )
        return ik_res

    def forward_kinematics(
        self, fk_req: ForwardKinematicsRequest
    ) -> ForwardKinematicsResponse:
        """
        Calculate Cartesian pose for given joint positions (Forward Kinematics).

        This method computes the TCP pose that results from a specified joint
        configuration. Useful for verifying joint positions and trajectory planning.

        Args:
            fk_req (ForwardKinematicsRequest): Request containing robot ID and
                joint positions (radians).

        Returns:
            ForwardKinematicsResponse: Response containing computed Cartesian pose,
                result code, and error message if computation failed.

        Note:
            Forward kinematics has a unique solution for any valid joint configuration.
            May fail if joint positions are invalid or exceed limits.
        """
        fk_req_proto = forward_kinematics_request_to_proto(fk_req)
        fk_res_proto = self.stub.ForwardKinematics(fk_req_proto)
        fk_res = forward_kinematics_response_to_message(fk_res_proto)
        if fk_res.result_code == KinResultCode.KIN_RESULT_CODE_SUCCESS:
            logger.info(
                f"Forward kinematics computed successfully for robot '{fk_req.id}'"
            )
        else:
            logger.error(
                f"Forward kinematics failed for robot '{fk_req.id}': {fk_res.error_message}"
            )
        return fk_res

    def set_tcp(self, set_tcp_req: SetTcpRequest) -> SetTcpResponse:
        """
        Set the Tool Center Point (TCP) for a robot.

        This method configures the TCP, which defines the position and orientation
        of the tool attached to the robot's end effector. Proper TCP configuration
        is essential for accurate motion control and task execution.

        Args:
            set_tcp_req (SetTcpRequest): Request containing the robot ID and TCP frame
                relative to the tool base.
        Returns:
            SetTcpResponse: Response indicating whether the TCP was set successfully
                and result code.
        """
        set_tcp_req_proto = set_tcp_request_to_proto(set_tcp_req)
        set_tcp_res_proto = self.stub.SetTcp(set_tcp_req_proto)
        set_tcp_res: SetTcpResponse = set_tcp_response_to_message(set_tcp_res_proto)
        if set_tcp_res.result == SetTcpResultCode.SET_TCP_RESULT_CODE_SUCCESS:
            logger.info("Set TCP command executed successfully")
        else:
            logger.error(
                f"Set TCP command failed with result code {set_tcp_res.result}"
            )
        return set_tcp_res

    def get_tcp(self, get_tcp_req: GetTcpRequest) -> GetTcpResponse:
        """
        Get the Tool Center Point (TCP) configuration for a robot.

        This method retrieves the current TCP configuration, which defines the
        position and orientation of the tool attached to the robot's end effector
        relative to the tool base frame.

        Args:
            get_tcp_req (GetTcpRequest): Request containing the robot ID for which
                to retrieve the TCP configuration.

        Returns:
            GetTcpResponse: Response containing the TCP configuration including
                the TCP ID and frame (position and orientation).

        Raises:
            grpc.RpcError: If there's a communication error with the VRMCS server
                or if the robot is not found.

        Note:
            The returned frame represents the transformation from the tool base
            to the TCP (tool center point).
        """
        get_tcp_req_proto = get_tcp_request_to_proto(get_tcp_req)
        get_tcp_res_proto = self.stub.GetTcp(get_tcp_req_proto)
        get_tcp_res: GetTcpResponse = get_tcp_response_to_message(get_tcp_res_proto)
        logger.info(f"Retrieved TCP configuration for robot '{get_tcp_req.id}'")
        return get_tcp_res

    def get_joint_states(
        self, get_joint_states_req: GetJointStatesRequest
    ) -> GetJointStatesResponse:
        """
        Get the current joint states of a robot (one-time query).

        This method retrieves a single snapshot of the robot's joint positions
        at the time of the request. For continuous monitoring, use
        joint_stream_subscribe instead.

        Args:
            get_joint_states_req (GetJointStatesRequest): Request containing the
                robot ID.

        Returns:
            GetJointStatesResponse: Response containing joint states with positions
                and timestamp.

        Note:
            Use the streaming API for high-frequency monitoring.
        """
        req_proto = get_joint_states_request_to_proto(get_joint_states_req)
        res_proto = self.stub.GetJointStates(req_proto)
        res = get_joint_states_response_to_message(res_proto)
        logger.info(f"Retrieved joint states for robot '{get_joint_states_req.id}'")
        return res

    def get_position_state(
        self, get_position_state_req: GetPositionStateRequest
    ) -> GetPositionStateResponse:
        """
        Get the current position state of a robot (one-time query).

        This method retrieves a single snapshot of the robot's joint and Cartesian
        positions at the time of the request. For continuous monitoring, use
        position_stream_subscribe instead.

        Args:
            get_position_state_req (GetPositionStateRequest): Request containing
                the robot ID.

        Returns:
            GetPositionStateResponse: Response containing position state with joint
                positions, Cartesian pose, and timestamp.

        Note:
            Use the streaming API for high-frequency monitoring.
        """
        req_proto = get_position_state_request_to_proto(get_position_state_req)
        res_proto = self.stub.GetPositionState(req_proto)
        res = get_position_state_response_to_message(res_proto)
        logger.info(f"Retrieved position state for robot '{get_position_state_req.id}'")
        return res

    def get_robot_states(
        self, get_robot_states_req: GetRobotStatesRequest
    ) -> GetRobotStatesResponse:
        """
        Get the current robot states (one-time query).

        This method retrieves a single snapshot of the robot's operational,
        safety, and connection states at the time of the request. For continuous
        monitoring, use states_stream_subscribe instead.

        Args:
            get_robot_states_req (GetRobotStatesRequest): Request containing the
                robot ID.

        Returns:
            GetRobotStatesResponse: Response containing robot states including
                operational state, safety state, connection state, and timestamp.

        Note:
            Use the streaming API for high-frequency monitoring.
        """
        req_proto = get_robot_states_request_to_proto(get_robot_states_req)
        res_proto = self.stub.GetRobotStates(req_proto)
        res = get_robot_states_response_to_message(res_proto)
        logger.info(f"Retrieved robot states for robot '{get_robot_states_req.id}'")
        return res

    def get_command_state(
        self, get_command_state_req: GetCommandStateRequest
    ) -> GetCommandStateResponse:
        """
        Get the current command state of a robot (one-time query).

        This method retrieves a single snapshot of the robot's commanded joint
        and Cartesian positions, velocities, and accelerations at the time of
        the request. For continuous monitoring, use command_state_stream_subscribe
        instead.

        Args:
            get_command_state_req (GetCommandStateRequest): Request containing the
                robot ID.

        Returns:
            GetCommandStateResponse: Response containing command state with joint
                and Cartesian positions, velocities, accelerations, and timestamps.

        Note:
            Use the streaming API for high-frequency monitoring of command states.
        """
        req_proto = get_command_state_request_to_proto(get_command_state_req)
        res_proto = self.stub.GetCommandState(req_proto)
        res = get_command_state_response_to_message(res_proto)
        logger.info(f"Retrieved command state for robot '{get_command_state_req.id}'")
        return res

    def _robot_alarm_stream_consume(
        self,
        stream_req: RobotAlarmStreamRequest,
        on_data: Callable[[RobotAlarm], None],
    ):
        self.robot_alarm_stream_iterator = self.stub.RobotAlarmStream(
            robot_alarm_stream_request_to_proto(stream_req)
        )
        try:
            for response in self.robot_alarm_stream_iterator:
                result: RobotAlarm = robot_alarm_to_message(response)
                try:
                    on_data(result)
                except Exception as e:
                    logger.error(f"Error in robot alarm callback: {e}")
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.CANCELLED:
                logger.info("Robot alarm stream cancelled successfully.")
            else:
                logger.error(
                    f"gRPC error during RobotAlarmStream: {e.code()} - {e.details()}"
                )

    def robot_alarm_stream_subscribe(
        self,
        stream_req: RobotAlarmStreamRequest,
        on_data: Callable[[RobotAlarm], None],
    ):
        """
        Subscribe to a stream of robot alarms and notifications.

        This method starts a background thread that consumes robot alarm data from the server
        and calls the provided callback function for each alarm update. Alarms include
        notifications from the motion controller, robot driver, and actuator driver.

        Args:
            stream_req (RobotAlarmStreamRequest): Configuration for the robot alarm stream
                including robot ID.
            on_data (Callable[[RobotAlarm], None]): Callback function that will be called
                with each RobotAlarm update containing a list of Notification objects.
                Any exceptions raised in the callback will be logged but won't stop the stream.

        Example:
            ```python
            def handle_alarm(alarm: RobotAlarm):
                for notification in alarm.notifications:
                    print(f"[{notification.severity.name}] {notification.message}")

            client.robot_alarm_stream_subscribe(
                RobotAlarmStreamRequest(id="robot_1"),
                on_data=handle_alarm
            )
            ```

        Note:
            To stop the stream, call robot_alarm_stream_unsubscribe().
            Only one robot alarm stream can be active at a time per client.
        """
        if (self.robot_alarm_stream_thread is None) or (
            not self.robot_alarm_stream_thread.is_alive()
        ):
            self.robot_alarm_stream_thread = threading.Thread(
                target=lambda: self._robot_alarm_stream_consume(stream_req, on_data),
                daemon=True,  # Daemon thread won't block program exit
            )
            self.robot_alarm_stream_thread.start()
        else:
            logger.warning(
                "Robot alarm stream is already active. Subscription request ignored."
            )

    def robot_alarm_stream_unsubscribe(self):
        """
        Unsubscribe from the robot alarm stream.

        This method stops the robot alarm streaming thread by cancelling the gRPC iterator,
        which causes the streaming loop to exit gracefully, then waits for the thread to terminate.

        Returns:
            None
        """
        if self.robot_alarm_stream_thread:
            if (
                self.robot_alarm_stream_thread.is_alive()
                and self.robot_alarm_stream_iterator
            ):
                self.robot_alarm_stream_iterator.cancel()
            self.robot_alarm_stream_thread.join()
            if self.robot_alarm_stream_thread.is_alive():
                logger.warning(
                    "Robot alarm stream thread did not exit cleanly within timeout"
                )
            self.robot_alarm_stream_thread = None
            self.robot_alarm_stream_iterator = None
