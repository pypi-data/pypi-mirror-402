"""
速度估计器 - Python 版本
对应 C++ 的 VelocityEstimator 实现
从位置/旋转差分估计线性和角速度，使用 EMA 滤波
"""

import numpy as np
import logging
from typing import Optional, Tuple, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class StateHistory:
    """单个刚体的状态历史"""
    position: np.ndarray
    rotation: np.ndarray  # [qx, qy, qz, qw]
    timestamp: float
    velocity: np.ndarray = None
    angular_velocity: np.ndarray = None
    has_prev: bool = False
    
    def __post_init__(self):
        if self.velocity is None:
            self.velocity = np.zeros(3)
        if self.angular_velocity is None:
            self.angular_velocity = np.zeros(3)


class VelocityEstimator:
    """速度估计器 - 从位置/旋转变化估计速度"""
    
    def __init__(self, filter_alpha: float = 0.3):
        """
        初始化速度估计器
        
        Args:
            filter_alpha: EMA 滤波系数 [0, 1]
                         0 = 无滤波（直接使用原始速度）
                         1 = 完全低通（不更新）
                         0.3 = 推荐值（中等平滑）
        """
        self.filter_alpha = max(0.0, min(1.0, filter_alpha))
        self.history: Dict[str, StateHistory] = {}
        logger.info(f"VelocityEstimator initialized with filter_alpha={self.filter_alpha}")
    
    def update_state(self, object_id: str, position: np.ndarray, 
                     rotation: np.ndarray, timestamp: float) -> None:
        """
        更新状态并估计速度
        
        首次调用会存储状态但不估计速度
        后续调用会估计速度
        
        Args:
            object_id: 刚体标识符
            position: 位置 [x, y, z]
            rotation: 旋转 [qx, qy, qz, qw]（四元数）
            timestamp: 时间戳（秒）
        """
        position = np.array(position, dtype=np.float64)
        rotation = np.array(rotation, dtype=np.float64)
        
        if object_id not in self.history:
            # 首次调用：仅存储状态
            self.history[object_id] = StateHistory(
                position=position,
                rotation=rotation,
                timestamp=timestamp,
                has_prev=True
            )
        else:
            # 后续调用：估计速度
            hist = self.history[object_id]
            dt = timestamp - hist.timestamp
            
            if dt > 1e-10:  # 避免除零
                # 估计线性速度：v = Δx / dt
                v_raw = (position - hist.position) / dt
                
                # 估计角速度
                w_raw = self._compute_angular_velocity(
                    hist.rotation, rotation, dt
                )
                
                # 应用 EMA 滤波
                hist.velocity = self._apply_ema_filter(v_raw, hist.velocity)
                hist.angular_velocity = self._apply_ema_filter(w_raw, hist.angular_velocity)
            
            # 更新为当前状态
            hist.position = position
            hist.rotation = rotation
            hist.timestamp = timestamp
    
    def get_velocity(self, object_id: str) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        获取估计的速度
        
        Args:
            object_id: 刚体标识符
        
        Returns:
            (velocity, angular_velocity) 或 (None, None) 如果无法获取
        """
        if object_id not in self.history:
            return None, None
        
        hist = self.history[object_id]
        if not hist.has_prev:
            return None, None
        
        return hist.velocity.copy(), hist.angular_velocity.copy()
    
    def clear(self) -> None:
        """清除所有历史状态"""
        self.history.clear()
    
    def set_filter_alpha(self, alpha: float) -> None:
        """
        设置 EMA 滤波系数
        
        Args:
            alpha: 滤波系数 [0, 1]
        """
        self.filter_alpha = max(0.0, min(1.0, alpha))
    
    def _compute_angular_velocity(self, rot_old: np.ndarray, rot_new: np.ndarray, 
                                  dt: float) -> np.ndarray:
        """
        从四元数差分计算角速度
        
        ω = 2·log(q_new * q_old^-1) / dt
        其中 log(q) 得到轴角向量形式
        
        Args:
            rot_old: 前一帧旋转 [qx, qy, qz, qw]
            rot_new: 当前帧旋转 [qx, qy, qz, qw]
            dt: 时间步长
        
        Returns:
            角速度 [wx, wy, wz]
        """
        # 相对旋转：q_rel = q_new * q_old^(-1)
        q_rel = self._quaternion_multiply(
            rot_new,
            self._quaternion_inverse(rot_old)
        )
        
        # 转换为轴角表示
        # q = [qx, qy, qz, qw]
        w = np.clip(q_rel[3], -1.0, 1.0)
        theta = 2.0 * np.arccos(w)
        
        axis = np.array(q_rel[:3])
        axis_norm = np.linalg.norm(axis)
        
        if axis_norm > 1e-6:
            axis = axis / axis_norm
        else:
            return np.zeros(3)
        
        # 角速度：ω = (θ / dt) * axis
        if dt > 1e-10:
            return (theta / dt) * axis
        
        return np.zeros(3)
    
    def _apply_ema_filter(self, v_raw: np.ndarray, v_old: np.ndarray) -> np.ndarray:
        """
        应用 EMA（指数移动平均）滤波
        
        v_filtered = α·v_raw + (1-α)·v_old
        
        Args:
            v_raw: 原始速度
            v_old: 前一帧滤波后速度
        
        Returns:
            滤波后速度
        """
        return (self.filter_alpha * np.array(v_raw) + 
                (1.0 - self.filter_alpha) * np.array(v_old))
    
    @staticmethod
    def _quaternion_multiply(q1: np.ndarray, q2: np.ndarray) -> np.ndarray:
        """
        四元数乘法 q1 * q2
        
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


