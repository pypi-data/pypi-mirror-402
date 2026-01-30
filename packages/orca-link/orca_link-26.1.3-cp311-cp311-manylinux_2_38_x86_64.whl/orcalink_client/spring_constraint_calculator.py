"""
弹簧约束力计算器 - Python 版本
对应 C++ 的 SpringConstraintCalculator 实现
使用 PD 控制器计算弹簧约束力和力矩
"""

import numpy as np
import logging
from typing import Tuple
from data_structures import SpringConstraintConfig

logger = logging.getLogger(__name__)


class SpringConstraintCalculator:
    """弹簧约束力计算 - PD 控制器实现"""
    
    def __init__(self, config: SpringConstraintConfig):
        """
        初始化弹簧约束计算器
        
        Args:
            config: 弹簧约束配置
        """
        self.config = config
        logger.debug(f"SpringConstraintCalculator initialized with config: "
                   f"k_linear={config.k_linear}, c_linear={config.c_linear}")
    
    def auto_tune(self, mass: float, inertia: float, 
                  omega_n: float, zeta: float) -> None:
        """
        基于二阶系统理论自动调参
        
        ω_n: 自然频率 (rad/s)
        ζ: 阻尼比 [0, 1]
        
        k = m·ω_n²
        c = 2·ζ·m·ω_n
        """
        self.config.k_linear = mass * omega_n ** 2
        self.config.c_linear = 2.0 * zeta * mass * omega_n
        
        self.config.k_angular = inertia * omega_n ** 2
        self.config.c_angular = 2.0 * zeta * inertia * omega_n
        
        logger.debug(f"Auto-tune: mass={mass}, inertia={inertia}, "
                   f"omega_n={omega_n}, zeta={zeta}")
        logger.debug(f"Result: k_linear={self.config.k_linear}, "
                   f"c_linear={self.config.c_linear}")
    
    def compute_spring_force(self, local_state: dict, remote_state: dict) -> Tuple[np.ndarray, np.ndarray]:
        """
        计算弹簧约束力和力矩
        
        Args:
            local_state: 本地刚体状态
                {
                    'position': [x, y, z],
                    'rotation': [qx, qy, qz, qw],
                    'velocity': [vx, vy, vz],
                    'angular_velocity': [wx, wy, wz]
                }
            remote_state: 远端刚体状态（同上）
        
        Returns:
            (force, torque) - numpy 数组 [3]
        """
        # 计算线性弹簧力
        force = self._compute_linear_force(
            local_state['position'],
            remote_state['position'],
            local_state['velocity'],
            remote_state['velocity']
        )
        
        # 计算角弹簧力矩
        torque = self._compute_angular_torque(
            local_state['rotation'],
            remote_state['rotation'],
            local_state['angular_velocity'],
            remote_state['angular_velocity']
        )
        
        return force, torque
    
    def _compute_linear_force(self, pos_local: np.ndarray, pos_remote: np.ndarray,
                             vel_local: np.ndarray, vel_remote: np.ndarray) -> np.ndarray:
        """
        计算线性弹簧力
        
        F = k·Δx + c·Δv
        其中 Δx = pos_remote - pos_local，Δv = vel_remote - vel_local
        """
        # 位置误差
        pos_error = np.array(pos_remote) - np.array(pos_local)
        pos_error_norm = np.linalg.norm(pos_error)
        
        # 死区处理
        if pos_error_norm < self.config.pos_deadzone:
            return np.zeros(3)
        
        # 速度误差
        vel_error = np.array(vel_remote) - np.array(vel_local)
        
        # PD 控制：F = k·Δx + c·Δv
        force = (self.config.k_linear * pos_error + 
                self.config.c_linear * vel_error)
        
        # 限幅
        force = self._clamp_force(force, self.config.max_force)
        
        return force
    
    def _compute_angular_torque(self, rot_local: np.ndarray, rot_remote: np.ndarray,
                               angvel_local: np.ndarray, angvel_remote: np.ndarray) -> np.ndarray:
        """
        计算角弹簧力矩
        
        τ = k·Δθ + c·Δω
        其中 Δθ 从四元数差转轴角表示
        """
        # 四元数格式：[qx, qy, qz, qw]
        rot_local = np.array(rot_local, dtype=np.float64)
        rot_remote = np.array(rot_remote, dtype=np.float64)
        
        # 计算旋转误差四元数：q_error = q_remote * q_local^(-1)
        q_error = self._quaternion_multiply(
            rot_remote,
            self._quaternion_inverse(rot_local)
        )
        
        # 转换为轴角表示
        # q = [qx, qy, qz, qw]，θ = 2·acos(qw)，axis = [qx, qy, qz] / sin(θ/2)
        qw = np.clip(np.abs(q_error[3]), 0.0, 1.0)
        theta = 2.0 * np.arccos(qw)
        
        axis = np.array(q_error[:3])
        axis_norm = np.linalg.norm(axis)
        
        rotation_error = np.zeros(3)
        if axis_norm > 1e-6 and theta > self.config.rot_deadzone:
            axis = axis / axis_norm
            rotation_error = axis * theta
        
        # 角速度误差
        angvel_error = np.array(angvel_remote) - np.array(angvel_local)
        
        # PD 控制：τ = k·Δθ + c·Δω
        torque = (self.config.k_angular * rotation_error + 
                 self.config.c_angular * angvel_error)
        
        # 限幅
        torque = self._clamp_force(torque, self.config.max_torque)
        
        return torque
    
    def _clamp_force(self, force: np.ndarray, max_val: float) -> np.ndarray:
        """
        限制力/力矩的大小
        
        Args:
            force: 力向量
            max_val: 最大值
        
        Returns:
            限幅后的力
        """
        magnitude = np.linalg.norm(force)
        if magnitude > max_val and max_val > 0:
            return force * (max_val / magnitude)
        return force
    
    @staticmethod
    def _quaternion_multiply(q1: np.ndarray, q2: np.ndarray) -> np.ndarray:
        """
        四元数乘法
        q1 * q2
        
        四元数格式：[qx, qy, qz, qw]
        """
        q1 = np.array(q1, dtype=np.float64)
        q2 = np.array(q2, dtype=np.float64)
        
        x1, y1, z1, w1 = q1[0], q1[1], q1[2], q1[3]
        x2, y2, z2, w2 = q2[0], q2[1], q2[2], q2[3]
        
        x = w1*x2 + x1*w2 + y1*z2 - z1*y2
        y = w1*y2 - x1*z2 + y1*w2 + z1*x2
        z = w1*z2 + x1*y2 - y1*x2 + z1*w2
        w = w1*w2 - x1*x2 - y1*y2 - z1*z2
        
        return np.array([x, y, z, w], dtype=np.float64)
    
    @staticmethod
    def _quaternion_inverse(q: np.ndarray) -> np.ndarray:
        """
        计算四元数的逆
        对于单位四元数，逆 = 共轭
        
        四元数格式：[qx, qy, qz, qw]
        """
        q = np.array(q, dtype=np.float64)
        return np.array([-q[0], -q[1], -q[2], q[3]], dtype=np.float64)


