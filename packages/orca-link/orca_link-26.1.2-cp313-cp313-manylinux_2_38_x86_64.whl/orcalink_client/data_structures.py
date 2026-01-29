"""
OrcaLink 数据结构定义
与 C++ 版本对应的数据结构
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import numpy as np


@dataclass
class RigidBodyForce:
    """刚体受力数据"""
    object_id: str
    force: np.ndarray  # [fx, fy, fz]
    torque: np.ndarray  # [tx, ty, tz]
    
    def __post_init__(self):
        """转换为 numpy 数组"""
        if not isinstance(self.force, np.ndarray):
            self.force = np.array(self.force, dtype=np.float32)
        if not isinstance(self.torque, np.ndarray):
            self.torque = np.array(self.torque, dtype=np.float32)


@dataclass
class RigidBodyPosition:
    """刚体位置数据"""
    object_id: str
    position: np.ndarray  # [x, y, z]
    rotation: np.ndarray  # [qw, qx, qy, qz] - Hamilton 约定
    
    def __post_init__(self):
        """转换为 numpy 数组"""
        if not isinstance(self.position, np.ndarray):
            self.position = np.array(self.position, dtype=np.float32)
        if not isinstance(self.rotation, np.ndarray):
            self.rotation = np.array(self.rotation, dtype=np.float32)


@dataclass
class OrcaLinkChannelConfig:
    """OrcaLink 频道配置"""
    channel_id: int
    publish: bool = False
    subscribe: bool = False


@dataclass
class FlowControlChannelPair:
    """滑动窗口流控通道对配置 (NEW)"""
    name: str = ""          # 配对名称
    send_channel_id: int = 0     # 发送通道ID
    recv_channel_id: int = 0     # 接收通道ID
    enabled: bool = True    # 是否启用此配对的流控


@dataclass
class FlowControlConfig:
    """滑动窗口流控配置"""
    enabled: bool = True
    max_send_ahead: int = 3  # 最大超前发送数
    min_send_ahead: int = 1  # 恢复正常阈值
    poll_interval_ms: float = 5.0  # 轮询间隔（毫秒）
    max_wait_time_sec: float = 0.1  # 最大等待时间（秒）
    enable_logging: bool = True
    log_interval_frames: int = 50
    channel_pairs: list = field(default_factory=list)  # NEW: 通道对列表


@dataclass
class AsyncParams:
    """异步模式参数"""
    flow_control_enabled: bool = True
    flow_control_window_size: int = 10
    speed_ratio_threshold: float = 2.0


@dataclass
class SyncParams:
    """同步模式参数"""
    sync_window_size: int = 1  # 1~3


@dataclass
class SessionConfig:
    """会话配置（支持同步/异步模式）"""
    control_mode: str = "async"  # "sync" 或 "async"
    async_params: AsyncParams = field(default_factory=AsyncParams)
    sync_params: SyncParams = field(default_factory=SyncParams)
    expected_clients: int = 2
    ready_timeout_sec: float = 30.0
    grpc_call_timeout_sec: float = 5.0
    
    # 向后兼容：保留旧字段（已废弃）
    # @deprecated 使用 async_params 替代
    flow_control_enabled: bool = True
    flow_control_window_size: int = 10
    speed_ratio_threshold: float = 2.0


@dataclass
class SpringConstraintConfig:
    """弹簧约束耦合模式配置
    
    NOTE: 启用状态由 coupling_mode 自动决定。
    当 coupling_mode='spring_constraint' 时，弹簧约束自动启用。
    """
    auto_tune: bool = True
    natural_frequency_hz: float = 2.0
    damping_ratio: float = 0.7
    k_linear: float = 1000.0
    c_linear: float = 50.0
    k_angular: float = 100.0
    c_angular: float = 5.0
    max_force: float = 5000.0
    max_torque: float = 500.0
    pos_deadzone: float = 0.0001
    rot_deadzone: float = 0.001
    estimate_remote_velocity: bool = True
    velocity_filter_alpha: float = 0.3


@dataclass
class OrcaLinkConfig:
    """OrcaLink 客户端完整配置"""
    enabled: bool = False
    server_address: str = "localhost:50351"
    session_id: int = 1
    client_name: str = "PythonClient"
    update_rate_hz: float = 30.0
    
    # 频道配置
    force_channel: OrcaLinkChannelConfig = field(
        default_factory=lambda: OrcaLinkChannelConfig(1, True, False)
    )
    position_channel: OrcaLinkChannelConfig = field(
        default_factory=lambda: OrcaLinkChannelConfig(2, False, True)
    )
    
    # 流控配置
    flow_control: FlowControlConfig = field(
        default_factory=FlowControlConfig
    )
    
    # 会话配置 (NEW)
    session: SessionConfig = field(
        default_factory=SessionConfig
    )
    
    # 耦合模式 (NEW)
    coupling_mode: str = "force_position"
    
    # 弹簧约束配置 (NEW)
    spring_constraint: SpringConstraintConfig = field(
        default_factory=SpringConstraintConfig
    )
    
    # I/P 帧编码配置
    i_frame_interval: int = 30
    change_threshold: float = 0.001
    
    # 异步处理
    async_enabled: bool = True
    
    # 调试配置
    verbose_logging: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'enabled': self.enabled,
            'server_address': self.server_address,
            'session_id': self.session_id,
            'client_name': self.client_name,
            'update_rate_hz': self.update_rate_hz,
            'force_channel': {
                'channel_id': self.force_channel.channel_id,
                'publish': self.force_channel.publish,
                'subscribe': self.force_channel.subscribe,
            },
            'position_channel': {
                'channel_id': self.position_channel.channel_id,
                'publish': self.position_channel.publish,
                'subscribe': self.position_channel.subscribe,
            },
            'flow_control': {
                'enabled': self.flow_control.enabled,
                'max_send_ahead': self.flow_control.max_send_ahead,
                'min_send_ahead': self.flow_control.min_send_ahead,
                'poll_interval_ms': self.flow_control.poll_interval_ms,
                'max_wait_time_sec': self.flow_control.max_wait_time_sec,
                'enable_logging': self.flow_control.enable_logging,
                'log_interval_frames': self.flow_control.log_interval_frames,
                'channel_pairs': [
                    {
                        'name': pair.name,
                        'send_channel_id': pair.send_channel_id,
                        'recv_channel_id': pair.recv_channel_id,
                        'enabled': pair.enabled,
                    }
                    for pair in self.flow_control.channel_pairs
                ] if self.flow_control.channel_pairs else [],
            },
            'session': {
                'flow_control_window_size': self.session.flow_control_window_size,
                'speed_ratio_threshold': self.session.speed_ratio_threshold,
                'expected_clients': self.session.expected_clients,
                'ready_timeout_sec': self.session.ready_timeout_sec,
            },
        }

