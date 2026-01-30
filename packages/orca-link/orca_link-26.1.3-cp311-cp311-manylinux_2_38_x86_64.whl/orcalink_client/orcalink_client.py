"""
OrcaLink Python 客户端
与 C++ OrcaLinkClient 功能对等的 Python 实现
"""

import grpc
import asyncio
import logging
import time
import sys
from pathlib import Path
from typing import List, Optional, Callable
import numpy as np

# 添加 Proto 目录到 sys.path 以导入生成的 pb.py 文件
sys.path.insert(0, str(Path(__file__).parent.parent / "Proto"))

try:
    import orcalink_pb2
    import orcalink_pb2_grpc
except ImportError as e:
    raise ImportError(f"Failed to import OrcaLink protobuf files: {e}")

from data_structures import (
    RigidBodyForce,
    RigidBodyPosition,
    OrcaLinkConfig,
    FlowControlConfig,
    SpringConstraintConfig,
)
from channel_flow_control import ChannelFlowControl

logger = logging.getLogger(__name__)
# 配置 logger 以确保日志输出
if not logger.handlers:
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('[OrcaLinkClient] %(levelname)s: %(message)s'))
    logger.addHandler(handler)


class OrcaLinkClient:
    """OrcaLink 客户端 - Python 实现"""
    
    def __init__(self, config: Optional[OrcaLinkConfig] = None):
        """
        初始化 OrcaLinkClient
        
        Args:
            config: 配置对象，如果为 None 则创建默认配置
        """
        self.config = config or OrcaLinkConfig()
        
        # gRPC 通道和 stub
        self.channel: Optional[grpc.aio.Channel] = None
        self.stub: Optional[orcalink_pb2_grpc.OrcaForwarderStub] = None
        
        # 会话状态
        self.session_id = self.config.session_id
        self.client_name = self.config.client_name
        self.session_active = False
        
        # 频道 ID
        self.force_channel_id = self.config.force_channel.channel_id
        self.position_channel_id = self.config.position_channel.channel_id
        
        # 序列号管理
        self.publish_sequence = 0
        self.subscribe_sequence = 0
        
        # 时间控制
        self.update_rate_hz = self.config.update_rate_hz
        self.next_update_time = 0.0
        
        # 流控管理（仅用于统计和 ACK，不再用于暂停决策）
        self.force_channel_flow_control = ChannelFlowControl(
            self.force_channel_id,
            self.config.force_channel.publish,
            self.config.force_channel.subscribe
        )
        self.position_channel_flow_control = ChannelFlowControl(
            self.position_channel_id,
            self.config.position_channel.publish,
            self.config.position_channel.subscribe
        )
        
        # NEW: 中央流控管理（服务端控制）
        self.speed_ratio_threshold = 2.0  # 速度比阈值（从服务端同步）
        self.pending_pause_cycles = 0      # 待执行的暂停周期数
        self.session_ready = False         # 会话是否就绪
        
        # NEW: 同步模式窗口管理（客户端本地控制）
        self.current_sync_window = 0
        if self.config.session.control_mode == "sync":
            self.current_sync_window = self.config.session.sync_params.sync_window_size
            logger.info(f"[SyncWindow] Initialized: window={self.current_sync_window}, "
                       f"size={self.config.session.sync_params.sync_window_size}")
        
        # NEW: 弹簧约束模式支持
        self.coupling_mode = self.config.coupling_mode
        self.spring_config = self.config.spring_constraint
        self.spring_calculators = {}  # objectId -> SpringConstraintCalculator (NEW: lazy-init per-body)
        self.velocity_estimator = None
        self.remote_states = {}  # 缓存远端刚体状态
        
        # Verbose logging flag from config
        self.verbose_logging = self.config.verbose_logging
        
        if self.is_spring_constraint_mode():
            from velocity_estimator import VelocityEstimator
            
            self.velocity_estimator = VelocityEstimator(
                self.spring_config.velocity_filter_alpha
            )
            logger.info(f"Spring constraint mode enabled (lazy-init calculators per rigid body, "
                       f"omega_n={self.spring_config.natural_frequency_hz}, "
                       f"zeta={self.spring_config.damping_ratio})")
    
    def set_verbose_logging(self, enabled: bool) -> None:
        """
        Enable or disable verbose logging for debugging
        
        Args:
            enabled: True to enable verbose logging, False to disable
        """
        self.verbose_logging = enabled
        if enabled:
            logger.info("✅ Verbose logging enabled")
        else:
            logger.info("✅ Verbose logging disabled")
    
    async def initialize(self) -> bool:
        """
        初始化并连接到 OrcaLink 服务器
        
        Returns:
            成功返回 True
        """
        if not self.config.enabled:
            logger.info("OrcaLink is disabled")
            return True
        
        try:
            # 解析服务器地址
            host, port = self._parse_server_address()
            
            # 创建 gRPC 通道
            self.channel = grpc.aio.insecure_channel(f"{host}:{port}")
            self.stub = orcalink_pb2_grpc.OrcaForwarderStub(self.channel)
            
            logger.info(f"[OrcaLinkClient] Connected to {host}:{port}")
            
            # 加入会话
            if not await self.join_session():
                return False
            
            self.session_active = True
            logger.info("[OrcaLinkClient] Initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"[OrcaLinkClient] Initialization failed: {e}")
            return False
    
    async def shutdown(self) -> None:
        """关闭连接"""
        if self.channel:
            await self.channel.close()
            logger.info("[OrcaLinkClient] Disconnected")
    
    async def reset(self) -> bool:
        """重置状态"""
        self.publish_sequence = 0
        self.subscribe_sequence = 0
        self.next_update_time = 0.0
        self.session_active = False
        self.pending_pause_cycles = 0
        
        # 重新连接
        return await self.initialize()
    
    async def join_session(self) -> bool:
        """加入 OrcaLink 会话"""
        if not self.stub:
            return False
        
        try:
            # 构建频道配置
            pub_channels = []
            sub_channels = []
            
            if self.config.force_channel.publish:
                pub_channels.append(orcalink_pb2.ChannelConfig(
                    channel_id=self.config.force_channel.channel_id,
                    channel_type=orcalink_pb2.CHANNEL_TYPE_FORCE,
                    data_type=orcalink_pb2.DATA_TYPE_FORCE
                ))
            
            if self.config.force_channel.subscribe:
                sub_channels.append(orcalink_pb2.ChannelConfig(
                    channel_id=self.config.force_channel.channel_id,
                    channel_type=orcalink_pb2.CHANNEL_TYPE_FORCE,
                    data_type=orcalink_pb2.DATA_TYPE_FORCE
                ))
            
            if self.config.position_channel.publish:
                pub_channels.append(orcalink_pb2.ChannelConfig(
                    channel_id=self.config.position_channel.channel_id,
                    channel_type=orcalink_pb2.CHANNEL_TYPE_POS,
                    data_type=orcalink_pb2.DATA_TYPE_POSITION
                ))
            
            if self.config.position_channel.subscribe:
                sub_channels.append(orcalink_pb2.ChannelConfig(
                    channel_id=self.config.position_channel.channel_id,
                    channel_type=orcalink_pb2.CHANNEL_TYPE_POS,
                    data_type=orcalink_pb2.DATA_TYPE_POSITION
                ))
            
            # 获取流控参数
            flow_control_window_size = self.config.session.async_params.flow_control_window_size
            speed_ratio_threshold = self.config.session.async_params.speed_ratio_threshold
            expected_clients = self.config.session.expected_clients
            ready_timeout_sec = self.config.session.ready_timeout_sec
            
            request = orcalink_pb2.JoinSessionRequest(
                session_id=self.session_id,
                client_name=self.client_name,
                publish_channels=pub_channels,
                subscribe_channels=sub_channels,
                # NEW: 添加中央流控参数
                update_rate_hz=self.update_rate_hz,
                flow_control_window_size=flow_control_window_size,
                speed_ratio_threshold=speed_ratio_threshold,
                expected_clients=expected_clients,
                # NEW: 添加耦合模式（用于握手一致性检查）
                coupling_mode=self.config.coupling_mode,
                # NEW: 添加控制模式和同步窗口大小
                control_mode=self.config.session.control_mode,
                sync_window_size=self.config.session.sync_params.sync_window_size if self.config.session.control_mode == "sync" else 0
            )
            
            # NEW: 轮询等待会话就绪
            import time as time_module
            start_time = time_module.time()
            
            # 每次 gRPC 调用的超时（秒）- 从配置读取
            grpc_call_timeout = self.config.session.grpc_call_timeout_sec
            
            while True:
                # 检查总超时
                elapsed = time_module.time() - start_time
                if elapsed > ready_timeout_sec:
                    logger.error(f"[OrcaLinkClient] Session ready timeout after {elapsed:.1f} seconds")
                    return False
                
                # 调用 JoinSession，带超时保护
                try:
                    response = await asyncio.wait_for(
                        self.stub.JoinSession(request),
                        timeout=grpc_call_timeout
                    )
                except asyncio.TimeoutError:
                    logger.error(f"[OrcaLinkClient] JoinSession gRPC call timed out after {grpc_call_timeout}s. "
                               f"Is the OrcaLink server running at {self.config.server_address}?")
                    return False
                except Exception as e:
                    logger.error(f"[OrcaLinkClient] JoinSession gRPC call failed: {e}")
                    return False
                
                if not response.success:
                    logger.error(f"[OrcaLinkClient] Failed to join session: {response.error}")
                    return False
                
                # 检查会话是否就绪
                if response.session_ready:
                    logger.info("[OrcaLinkClient] Session is ready!")
                    break
                
                logger.info(f"[OrcaLinkClient] Waiting for session ready ({response.connected_clients}/{expected_clients} clients)...")
                
                # 等待 1 秒后重试
                await asyncio.sleep(1.0)
            
            # 验证流控参数一致性
            if response.flow_control_window_size != flow_control_window_size:
                logger.error(f"[OrcaLinkClient] flow_control_window_size mismatch! "
                           f"Expected {flow_control_window_size}, got {response.flow_control_window_size}")
                return False
            
            # 保存会话状态和同步参数
            self.session_active = True
            self.session_ready = True  # 会话就绪标志
            self.update_rate_hz = response.update_rate_hz
            self.speed_ratio_threshold = response.speed_ratio_threshold
            
            logger.info(f"[OrcaLinkClient] Joined session (ID: {self.session_id}, "
                       f"Clients: {response.client_count}, "
                       f"UpdateRate: {self.update_rate_hz} Hz, "
                       f"FlowControlWindowSize: {response.flow_control_window_size}, "
                       f"SpeedRatioThreshold: {self.speed_ratio_threshold})")
            return True
            
        except Exception as e:
            logger.error(f"[OrcaLinkClient] Exception joining session: {e}")
            return False
    
    async def publish_forces(self, forces: List[RigidBodyForce]) -> bool:
        """
        发布刚体受力数据
        
        Args:
            forces: 受力数据列表
            
        Returns:
            成功返回 True
        """
        if not self.session_active or not self.stub:
            return False
        
        try:
            # 构建数据单元
            units = []
            for force in forces:
                force_value = orcalink_pb2.ForceValue(
                    fx=float(force.force[0]),
                    fy=float(force.force[1]),
                    fz=float(force.force[2]),
                    tx=float(force.torque[0]),
                    ty=float(force.torque[1]),
                    tz=float(force.torque[2])
                )
                
                unit = orcalink_pb2.DataUnit(
                    object_id=force.object_id,
                    data_type=orcalink_pb2.DATA_TYPE_FORCE,
                    force=force_value
                )
                units.append(unit)
            
            # 构建数据帧
            frame = orcalink_pb2.DataFrame(
                frame_type=orcalink_pb2.FRAME_TYPE_IFRAME,
                sequence=self.publish_sequence,
                update_mode=orcalink_pb2.UPDATE_MODE_FULL,
                timestamp=int(time.time() * 1e6),
                units=units
            )
            
            # 构建请求
            request = orcalink_pb2.PublishFrameRequest(
                session_id=self.session_id,
                channel_id=self.force_channel_id,
                client_name=self.client_name,
                frame=frame
            )
            
            # 发送请求
            response = await self.stub.PublishFrame(request)
            
            if not response.success:
                logger.error(f"[OrcaLinkClient] PublishFrame failed: {response.error}")
                return False
            
            self.publish_sequence = response.sequence
            
            # 提取 remote_acked_sequence（NEW - 有界异步流控）
            remote_acked = response.remote_acked_sequence
            self.force_channel_flow_control.set_remote_acked_sequence(remote_acked)
            
            # 处理流控指令（仅在启用流控时）
            if self.config.session.flow_control_enabled and response.HasField('flow_control'):
                flow_control = response.flow_control
                if flow_control.action == orcalink_pb2.FlowControlAction.PAUSE_CYCLES:
                    pause_cycles = flow_control.pause_cycles
                    self.pending_pause_cycles = pause_cycles
                    logger.info(f"[OrcaLinkClient] Received PAUSE_CYCLES instruction: {pause_cycles} cycles. Reason: {flow_control.reason}")
            
            # 记录发送（用于统计）
            self.force_channel_flow_control.record_send()
            
            return True
            
        except Exception as e:
            logger.error(f"[OrcaLinkClient] PublishForces exception: {e}")
            return False
    
    async def subscribe_positions(self, max_count: int = 0, enable_sync_window: bool = True) -> List[RigidBodyPosition]:
        """
        订阅刚体位置数据
        
        Args:
            max_count: 最大接收数量，0表示全部
            enable_sync_window: 是否启用同步窗口管理（同步模式下）
        
        Returns:
            接收到的位置数据列表
        """
        if not self.session_active or not self.stub:
            return []
        
        try:
            request = orcalink_pb2.SubscribeFrameRequest(
                session_id=self.session_id,
                channel_id=self.position_channel_id,
                client_name=self.client_name,
                max_count=max_count
            )
            
            response = await self.stub.SubscribeFrame(request)
            
            if not response.success:
                logger.info(f"[SubscribePositions] Response not successful")
                return []
            
            # 解码数据帧
            positions = []
            total_units = 0
            for frame in response.frames:
                self.subscribe_sequence = frame.sequence
                frame_units = len(frame.units)
                total_units += frame_units
                
                logger.info(f"[SubscribePositions] Frame sequence={frame.sequence}, units={frame_units}")
                
                for unit in frame.units:
                    logger.info(f"[SubscribePositions] Unit: object_id='{unit.object_id}', "
                               f"data_type={unit.data_type}, has_position={unit.HasField('position')}")
                    
                    if unit.data_type == orcalink_pb2.DATA_TYPE_POSITION and unit.HasField('position'):
                        pos = unit.position
                        position = RigidBodyPosition(
                            object_id=unit.object_id,
                            position=np.array([pos.x, pos.y, pos.z], dtype=np.float32),
                            rotation=np.array([pos.qw, pos.qx, pos.qy, pos.qz], dtype=np.float32)
                        )
                        positions.append(position)
            
            logger.info(f"[SubscribePositions] Summary: total_units={total_units}, positions={len(positions)}")
            
            # 记录接收（流控）
            if positions:
                self.position_channel_flow_control.record_recv(len(positions))
                
                # 同步模式窗口管理（仅在启用时）
                if enable_sync_window and self.config.session.control_mode == "sync":
                    is_bidirectional = (self.config.position_channel.publish and 
                                       self.config.position_channel.subscribe)
                    old_window = self.current_sync_window
                    if is_bidirectional:
                        self.current_sync_window += 1
                        if self.current_sync_window > self.config.session.sync_params.sync_window_size:
                            self.current_sync_window = self.config.session.sync_params.sync_window_size
                    logger.info(f"[SyncWindow] After recv: window changed from {old_window} "
                               f"to {self.current_sync_window}, received {len(positions)} units")
                
                # 提取 remote_acked_sequence（有界异步流控）
                remote_acked = response.remote_acked_sequence
                self.position_channel_flow_control.set_remote_acked_sequence(remote_acked)
                
                # 异步发送 ACK
                if response.frames:
                    last_sequence = response.frames[-1].sequence
                    asyncio.create_task(
                        self.send_ack(
                            self.position_channel_id,
                            last_sequence,
                            len(positions)
                        )
                    )
            
            return positions
            
        except Exception as e:
            logger.error(f"[OrcaLinkClient] SubscribePositions exception: {e}", exc_info=True)
            return []
    
    async def subscribe_forces(self) -> List[RigidBodyForce]:
        """
        订阅刚体受力数据 (NEW)
        
        Returns:
            接收到的受力数据列表
        """
        if not self.session_active or not self.stub:
            return []
        
        try:
            request = orcalink_pb2.SubscribeFrameRequest(
                session_id=self.session_id,
                channel_id=self.force_channel_id,
                client_name=self.client_name,
                max_count=0
            )
            
            response = await self.stub.SubscribeFrame(request)
            
            if not response.success:
                return []
            
            # 解码数据帧
            forces = []
            frame_list = response.frames  # This is a property, not a method!
            
            for frame_idx, frame in enumerate(frame_list):
                self.subscribe_sequence = frame.sequence
                
                for unit_idx, unit in enumerate(frame.units):
                    if unit.data_type == orcalink_pb2.DATA_TYPE_FORCE and unit.HasField('force'):
                        force = unit.force
                        force_obj = RigidBodyForce(
                            object_id=unit.object_id,
                            force=np.array([force.fx, force.fy, force.fz], dtype=np.float32),
                            torque=np.array([force.tx, force.ty, force.tz], dtype=np.float32)
                        )
                        forces.append(force_obj)
            
            # 记录接收（流控）
            if forces:
                self.force_channel_flow_control.record_recv(len(frame_list))
                
                # 提取 remote_acked_sequence（NEW - 有界异步流控）
                remote_acked = response.remote_acked_sequence
                self.force_channel_flow_control.set_remote_acked_sequence(remote_acked)
                
                # 异步发送 ACK（NEW - 有界异步流控）
                if frame_list:
                    last_sequence = frame_list[-1].sequence
                    asyncio.create_task(
                        self.send_ack(
                            self.force_channel_id,
                            last_sequence,
                            len(frame_list)
                        )
                    )
            
            return forces
            
        except Exception as e:
            logger.debug(f"[OrcaLinkClient] SubscribeForces exception: {e}")
            return []
    
    async def publish_positions(self, positions: List[RigidBodyPosition]) -> bool:
        """
        发布刚体位置数据
        
        Args:
            positions: 位置数据列表
            
        Returns:
            成功返回 True
        """
        if not self.session_active or not self.stub:
            return False
        
        try:
            # 构建数据单元
            units = []
            for position in positions:
                pos_value = orcalink_pb2.PositionValue(
                    x=float(position.position[0]),
                    y=float(position.position[1]),
                    z=float(position.position[2]),
                    qw=float(position.rotation[0]),  # [qw, qx, qy, qz]
                    qx=float(position.rotation[1]),
                    qy=float(position.rotation[2]),
                    qz=float(position.rotation[3])
                )
                
                unit = orcalink_pb2.DataUnit(
                    object_id=position.object_id,
                    data_type=orcalink_pb2.DATA_TYPE_POSITION,
                    position=pos_value
                )
                units.append(unit)
            
            # 构建数据帧
            frame = orcalink_pb2.DataFrame(
                frame_type=orcalink_pb2.FRAME_TYPE_IFRAME,
                sequence=self.publish_sequence,
                update_mode=orcalink_pb2.UPDATE_MODE_FULL,
                timestamp=int(time.time() * 1e6),
                units=units
            )
            
            # 构建请求
            request = orcalink_pb2.PublishFrameRequest(
                session_id=self.session_id,
                channel_id=self.position_channel_id,
                client_name=self.client_name,
                frame=frame
            )
            
            # 发送请求
            response = await self.stub.PublishFrame(request)
            
            if response.success:
                # 简化日志，避免过多输出
                if len(positions) > 0:
                    first_pos = positions[0]
                    logger.debug(f"[OrcaLink-Spring] Published {len(positions)} positions, first: {first_pos.object_id}")
                
                self.publish_sequence += 1
                
                # NEW: 同步模式窗口管理（仅对双向通道）
                if self.config.session.control_mode == "sync":
                    is_bidirectional = (self.config.position_channel.publish and 
                                       self.config.position_channel.subscribe)
                    logger.info(f"[SyncWindow] Before send: window={self.current_sync_window}, "
                               f"bidirectional={is_bidirectional}")
                    if is_bidirectional:
                        self.current_sync_window -= 1
                        logger.info(f"[SyncWindow] After send: window={self.current_sync_window}")
                
                # 提取 remote_acked_sequence（NEW - 有界异步流控）
                remote_acked = response.remote_acked_sequence
                self.position_channel_flow_control.set_remote_acked_sequence(remote_acked)
                
                # 处理流控指令（异步模式，仅在启用流控时）
                if self.config.session.control_mode == "async":
                    flow_control_enabled = self.config.session.async_params.flow_control_enabled
                    if not flow_control_enabled and self.config.session.flow_control_enabled:
                        flow_control_enabled = self.config.session.flow_control_enabled  # 向后兼容
                    if flow_control_enabled and response.HasField('flow_control'):
                        flow_control = response.flow_control
                        if flow_control.action == orcalink_pb2.FlowControlAction.PAUSE_CYCLES:
                            pause_cycles = flow_control.pause_cycles
                            self.pending_pause_cycles = pause_cycles
                            logger.info(f"[OrcaLinkClient] Received PAUSE_CYCLES instruction: {pause_cycles} cycles. Reason: {flow_control.reason}")
                
                self.position_channel_flow_control.record_send()
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"[OrcaLinkClient] PublishPositions exception: {e}", exc_info=True)
            return False
    
    def should_update(self, current_time: float) -> bool:
        """
        检查是否应该执行数据交换
        
        Args:
            current_time: 当前仿真时间
            
        Returns:
            到达更新时间返回 True
        """
        if self.update_rate_hz <= 0.0:
            return True
        return current_time >= self.next_update_time
    
    def advance_update_time(self) -> None:
        """推进到下一个更新时间"""
        if self.update_rate_hz > 0.0:
            self.next_update_time += 1.0 / self.update_rate_hz
    
    def set_next_update_time(self, time: float) -> None:
        """设置下一个更新时间"""
        self.next_update_time = time
    
    def set_flow_control_callback(self, callback: Callable[[bool, str], None]) -> None:
        """设置流控回调"""
        self.flow_control_callback = callback
    
    async def send_ack(self, channel_id: int, acked_sequence: int, received_count: int) -> bool:
        """
        异步发送 ACK 消息（NEW - 有界异步流控）
        
        Args:
            channel_id: 频道 ID
            acked_sequence: 已确认的序列号
            received_count: 接收的数据条数
            
        Returns:
            成功返回 True
        """
        if not self.session_active or not self.stub:
            return False
        
        try:
            ack = orcalink_pb2.AckMessage(
                session_id=self.session_id,
                channel_id=channel_id,
                client_name=self.client_name,
                acked_sequence=acked_sequence,
                received_count=received_count,
                timestamp=int(time.time() * 1e6)
            )
            request = orcalink_pb2.SendAckRequest(ack=ack)
            response = await self.stub.SendAck(request)
            return response.success
        except Exception as e:
            logger.debug(f"[OrcaLinkClient] SendAck exception: {e}")
            return False
    
    def _get_channel_flow_control(self, channel_id: int) -> 'ChannelFlowControl':
        """根据通道 ID 获取流控对象（仅用于统计）"""
        if channel_id == self.config.force_channel.channel_id:
            return self.force_channel_flow_control
        elif channel_id == self.config.position_channel.channel_id:
            return self.position_channel_flow_control
        return None
    
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self.channel is not None and self.stub is not None
    
    def is_session_active(self) -> bool:
        """检查会话是否活跃"""
        return self.session_active
    
    def get_update_rate_hz(self) -> float:
        """获取数据交换频率"""
        return self.update_rate_hz
    
    def _parse_server_address(self) -> tuple:
        """解析服务器地址"""
        parts = self.config.server_address.split(':')
        if len(parts) != 2:
            raise ValueError(f"Invalid server address format: {self.config.server_address}")
        return parts[0], int(parts[1])
    
    # NEW: 中央流控相关方法
    
    def should_pause_this_cycle(self) -> bool:
        """
        检查是否应该暂停本周期的数据发送
        
        Returns:
            True 表示应该暂停，False 表示继续
        """
        # NEW: 根据控制模式选择判定逻辑
        if self.config.session.control_mode == "sync":
            # 同步模式：检查本地窗口
            should_pause = self.current_sync_window <= 0
            if should_pause:
                logger.info(f"[SyncWindow] PAUSE: window={self.current_sync_window} <= 0")
            return should_pause
        else:
            # 异步模式：检查服务端暂停指令
            # 如果流控已禁用，则不暂停
            flow_control_enabled = self.config.session.async_params.flow_control_enabled
            if not flow_control_enabled and self.config.session.flow_control_enabled:
                flow_control_enabled = self.config.session.flow_control_enabled  # 向后兼容
            if not flow_control_enabled:
                return False
            
            if self.pending_pause_cycles > 0:
                self.pending_pause_cycles -= 1
                return True  # 暂停本周期
            return False  # 继续执行
    
    def is_session_ready_status(self) -> bool:
        """获取会话就绪状态"""
        return self.session_ready
    
    # NEW: 弹簧约束模式相关方法
    
    def is_spring_constraint_mode(self) -> bool:
        """检查是否为弹簧约束模式"""
        return self.coupling_mode == "spring_constraint"
    
    def compute_spring_forces(self, local_positions: List[RigidBodyPosition], 
                            local_velocities: Optional[dict] = None) -> List[RigidBodyForce]:
        """
        计算弹簧约束力
        
        Args:
            local_positions: 本地刚体位姿列表
            local_velocities: 本地速度字典 {object_id: (velocity, angular_velocity)}
        
        Returns:
            弹簧力列表
        """
        if not self.is_spring_constraint_mode():
            return []
        
        spring_forces = []
        
        for local_pos in local_positions:
            if local_pos.object_id not in self.remote_states:
                continue
            
            object_id = local_pos.object_id
            remote_state = self.remote_states[object_id]
            
            # === NEW: Get or create per-body spring calculator ===
            if object_id not in self.spring_calculators:
                logger.info(f"[Auto-Tune] Creating calculator for {object_id}")
                
                from spring_constraint_calculator import SpringConstraintCalculator
                
                calc = SpringConstraintCalculator(self.spring_config)
                
                if self.spring_config.auto_tune:
                    # Get mass from rigid_bodies if available
                    mass = 1.0  # default value
                    if hasattr(self, 'rigid_bodies') and self.rigid_bodies:
                        try:
                            rb_state = self.rigid_bodies.get_state(object_id)
                            if rb_state:
                                mass = rb_state.mass
                        except Exception as e:
                            logger.debug(f"Could not get mass for {object_id}: {e}")
                    
                    # Estimate moment of inertia (simplified: I = 0.01 * m)
                    inertia = 0.01 * mass
                    
                    # Calculate angular frequency
                    omega_n = 2.0 * np.pi * self.spring_config.natural_frequency_hz
                    zeta = self.spring_config.damping_ratio
                    
                    # Call auto_tune
                    calc.auto_tune(mass, inertia, omega_n, zeta)
                    
                    logger.debug(f"[Auto-Tune] {object_id}: mass={mass:.2f} kg, "
                               f"inertia={inertia:.4f} kg·m², "
                               f"f={self.spring_config.natural_frequency_hz} Hz, "
                               f"k_linear={calc.config.k_linear:.1f} N/m, "
                               f"c_linear={calc.config.c_linear:.1f} N·s/m")
                
                self.spring_calculators[object_id] = calc
            
            calculator = self.spring_calculators[object_id]
            
            # 估计远端速度
            if self.spring_config.estimate_remote_velocity:
                self.velocity_estimator.update_state(
                    object_id,
                    remote_state['position'],
                    remote_state['rotation'],
                    time.time()
                )
                remote_vel, remote_angvel = self.velocity_estimator.get_velocity(
                    object_id
                )
            else:
                remote_vel = remote_state.get('velocity', np.zeros(3))
                remote_angvel = remote_state.get('angular_velocity', np.zeros(3))
            
            # 获取本地速度
            if local_velocities and object_id in local_velocities:
                local_vel, local_angvel = local_velocities[object_id]
            else:
                local_vel = np.zeros(3)
                local_angvel = np.zeros(3)
            
            # 构建状态字典
            local_state = {
                'position': local_pos.position,
                'rotation': local_pos.rotation,
                'velocity': local_vel if local_vel is not None else np.zeros(3),
                'angular_velocity': local_angvel if local_angvel is not None else np.zeros(3)
            }
            
            remote_state_dict = {
                'position': remote_state['position'],
                'rotation': remote_state['rotation'],
                'velocity': remote_vel if remote_vel is not None else np.zeros(3),
                'angular_velocity': remote_angvel if remote_angvel is not None else np.zeros(3)
            }
            
            # === Use per-body calculator to compute spring force ===
            # 计算弹簧力
            force, torque = calculator.compute_spring_force(
                local_state, remote_state_dict
            )
            
            # 🔍 打印位置对比和力的详细信息（仅在verbose日志启用时）
            if self.verbose_logging:
                local_p = local_state['position']
                remote_p = remote_state_dict['position']
                pos_diff = remote_p - local_p
                pos_diff_norm = np.linalg.norm(pos_diff)
                force_norm = np.linalg.norm(force)
                
                logger.info(f"  🔍 [{object_id}]")
                logger.info(f"     📍 MuJoCo Local:  pos=({local_p[0]:7.4f}, {local_p[1]:7.4f}, {local_p[2]:7.4f})")
                logger.info(f"     📍 SPH Remote:    pos=({remote_p[0]:7.4f}, {remote_p[1]:7.4f}, {remote_p[2]:7.4f})")
                logger.info(f"     📏 Position Δ:    Δ=({pos_diff[0]:7.4f}, {pos_diff[1]:7.4f}, {pos_diff[2]:7.4f}), |Δ|={pos_diff_norm:.6f} m")
                logger.info(f"     ⚡ Spring Force:  F=({force[0]:7.2f}, {force[1]:7.2f}, {force[2]:7.2f}), |F|={force_norm:.2f} N")
            
            local_p = local_state['position']
            remote_p = remote_state_dict['position']
            pos_diff = remote_p - local_p
            pos_diff_norm = np.linalg.norm(pos_diff)
            force_norm = np.linalg.norm(force)
            
            spring_forces.append(RigidBodyForce(
                object_id=object_id,
                force=force,
                torque=torque
            ))
        
        return spring_forces

