"""
OrcaLink 配置加载器

从 JSON 文件加载配置，支持新格式（orcalink_client + orcalink_bridge）。
"""

import json
from typing import Dict, Any
from data_structures import (
    OrcaLinkConfig,
    OrcaLinkChannelConfig,
    FlowControlConfig,
    FlowControlChannelPair,
    SessionConfig,
    AsyncParams,
    SyncParams,
    SpringConstraintConfig,
)


def load_config_from_json(json_path: str) -> OrcaLinkConfig:
    """
    从 JSON 文件加载 OrcaLink 配置（新格式）
    
    支持新格式：
    - orcalink_client: 客户端配置（网络通信相关）
    - orcalink_bridge: 桥接层配置（力处理相关）
    
    Args:
        json_path: JSON 配置文件路径
        
    Returns:
        OrcaLinkConfig: 加载的配置对象
        
    Raises:
        RuntimeError: 配置文件格式错误或缺失必需字段
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 检查新格式
        client_config = data.get('orcalink_client', {})
        bridge_config = data.get('orcalink_bridge', {})
        
        if not client_config and not bridge_config:
            raise RuntimeError(
                "Configuration file must contain 'orcalink_client' and/or 'orcalink_bridge' blocks. "
                "Legacy format (single 'orcalink' block) is no longer supported."
            )
        
        # ========== 加载客户端配置 ==========
        enabled = client_config.get('enabled', False)
        server_address = client_config.get('server_address', 'localhost:50351')
        session_id = client_config.get('session_id', 1)
        client_name = client_config.get('client_name', 'PythonClient')
        update_rate_hz = client_config.get('update_rate_hz', 30.0)
        
        # 编码配置
        encoding_config = client_config.get('encoding', {})
        i_frame_interval = encoding_config.get('i_frame_interval', 30)
        change_threshold = encoding_config.get('change_threshold', 0.001)
        
        # 会话配置
        session_data = client_config.get('session', {})
        control_mode = session_data.get('control_mode', 'async')
        
        # 异步模式参数
        async_params_data = session_data.get('async_params', {})
        async_params = AsyncParams(
            flow_control_enabled=async_params_data.get('flow_control_enabled', True),
            flow_control_window_size=async_params_data.get('flow_control_window_size', 10),
            speed_ratio_threshold=async_params_data.get('speed_ratio_threshold', 2.0),
        )
        
        # 同步模式参数
        sync_params_data = session_data.get('sync_params', {})
        sync_window_size = sync_params_data.get('sync_window_size', 1)
        if sync_window_size < 1 or sync_window_size > 3:
            raise ValueError(f"sync_window_size must be between 1 and 3, got {sync_window_size}")
        sync_params = SyncParams(sync_window_size=sync_window_size)
        
        session = SessionConfig(
            control_mode=control_mode,
            async_params=async_params,
            sync_params=sync_params,
            expected_clients=session_data.get('expected_clients', 2),
            ready_timeout_sec=session_data.get('ready_timeout_sec', 30.0),
            grpc_call_timeout_sec=session_data.get('grpc_call_timeout_sec', 5.0),
            # 向后兼容字段
            flow_control_enabled=async_params.flow_control_enabled,
            flow_control_window_size=async_params.flow_control_window_size,
            speed_ratio_threshold=async_params.speed_ratio_threshold,
        )
        
        # ========== 加载桥接层配置 ==========
        coupling_mode = bridge_config.get('coupling_mode', 'force_position')
        
        # 根据耦合模式选择配置块
        if coupling_mode == 'spring_constraint':
            if 'spring_constraint' not in bridge_config:
                raise RuntimeError("spring_constraint mode selected but config block not found")
            mode_config = bridge_config['spring_constraint']
        elif coupling_mode == 'multi_point_force':
            if 'multi_point_force' not in bridge_config:
                raise RuntimeError("multi_point_force mode selected but config block not found")
            mode_config = bridge_config['multi_point_force']
        else:  # force_position
            if 'force_position' not in bridge_config:
                raise RuntimeError("force_position mode selected but config block not found")
            mode_config = bridge_config['force_position']
        
        # 从模式块中读取通道配置 - REQUIRED
        if 'channels' not in mode_config:
            raise RuntimeError(f"{coupling_mode} mode: 'channels' block is required but not found")
        channels_config = mode_config['channels']
        
        # Force channel (required for force_position and multi_point_force modes)
        if coupling_mode in ['force_position', 'multi_point_force']:
            if 'force' not in channels_config:
                raise RuntimeError(f"{coupling_mode} mode: 'force' channel is required but not found")
            force_ch = channels_config['force']
            if 'channel_id' not in force_ch:
                raise RuntimeError(f"{coupling_mode} mode: 'channel_id' is required in force channel")
            force_channel = OrcaLinkChannelConfig(
                channel_id=force_ch['channel_id'],
                publish=force_ch.get('publish', False),
                subscribe=force_ch.get('subscribe', False)
            )
        else:
            # spring_constraint mode: force channel not used
            force_channel = OrcaLinkChannelConfig(channel_id=1, publish=False, subscribe=False)
        
        # Position channel (required for all modes)
        if 'position' not in channels_config:
            raise RuntimeError(f"{coupling_mode} mode: 'position' channel is required but not found")
        position_ch = channels_config['position']
        if 'channel_id' not in position_ch:
            raise RuntimeError(f"{coupling_mode} mode: 'channel_id' is required in position channel")
        position_channel = OrcaLinkChannelConfig(
            channel_id=position_ch['channel_id'],
            publish=position_ch.get('publish', False),
            subscribe=position_ch.get('subscribe', True)
        )
        
        # 流控配置（如果存在）
        flow_ctrl_data = data.get('flow_control', {})  # 流控配置可能在顶层
        channel_pairs = []
        for pair_data in flow_ctrl_data.get('channel_pairs', []):
            pair = FlowControlChannelPair(
                name=pair_data.get('name', ''),
                send_channel_id=pair_data.get('send_channel_id', 0),
                recv_channel_id=pair_data.get('recv_channel_id', 0),
                enabled=pair_data.get('enabled', True)
            )
            channel_pairs.append(pair)
        
        flow_control = FlowControlConfig(
            enabled=flow_ctrl_data.get('enabled', True),
            max_send_ahead=flow_ctrl_data.get('max_send_ahead', 3),
            min_send_ahead=flow_ctrl_data.get('min_send_ahead', 1),
            poll_interval_ms=flow_ctrl_data.get('poll_interval_ms', 5.0),
            max_wait_time_sec=flow_ctrl_data.get('max_wait_time_sec', 0.1),
            enable_logging=flow_ctrl_data.get('enable_logging', True),
            log_interval_frames=flow_ctrl_data.get('log_interval_frames', 50),
            channel_pairs=channel_pairs,
        )
        
        # 加载弹簧约束配置（如果适用）
        spring_constraint = SpringConstraintConfig()
        
        if coupling_mode == 'spring_constraint':
            spring_data = mode_config.get('spring_parameters', {})
            spring_constraint = SpringConstraintConfig(
                auto_tune=spring_data.get('auto_tune', True),
                natural_frequency_hz=spring_data.get('natural_frequency_hz', 2.0),
                damping_ratio=spring_data.get('damping_ratio', 0.7),
                k_linear=spring_data.get('linear_spring_stiffness', 1000.0),
                c_linear=spring_data.get('linear_damping_coefficient', 50.0),
                k_angular=spring_data.get('angular_spring_stiffness', 100.0),
                c_angular=spring_data.get('angular_damping_coefficient', 5.0),
                max_force=spring_data.get('max_spring_force', 5000.0),
                max_torque=spring_data.get('max_spring_torque', 500.0),
                pos_deadzone=spring_data.get('position_deadzone', 0.0001),
                rot_deadzone=spring_data.get('rotation_deadzone', 0.001),
                estimate_remote_velocity=spring_data.get('estimate_remote_velocity', True),
                velocity_filter_alpha=spring_data.get('velocity_filter_alpha', 0.3),
            )
        
        # 调试配置
        verbose_logging = data.get('debug', {}).get('verbose_logging', False)
        
        # 异步处理（默认启用）
        async_enabled = True
        
        # 创建并返回配置对象
        return OrcaLinkConfig(
            enabled=enabled,
            server_address=server_address,
            session_id=session_id,
            client_name=client_name,
            update_rate_hz=update_rate_hz,
            force_channel=force_channel,
            position_channel=position_channel,
            flow_control=flow_control,
            session=session,
            coupling_mode=coupling_mode,
            spring_constraint=spring_constraint,
            i_frame_interval=i_frame_interval,
            change_threshold=change_threshold,
            async_enabled=async_enabled,
            verbose_logging=verbose_logging,
        )
    except FileNotFoundError:
        raise RuntimeError(f"Configuration file not found: {json_path}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON in configuration file {json_path}: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to load OrcaLink config from {json_path}: {e}")

