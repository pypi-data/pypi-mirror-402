"""
耦合模式策略 - 封装不同耦合模式的业务逻辑

使用策略模式（Strategy Pattern）将两种耦合模式的不同行为封装在独立的策略类中：
- ForcePositionStrategy: 力-位置模式（SPH发送力，客户端发送位置）
- SpringConstraintStrategy: 弹簧约束模式（双向位置交换+弹簧力计算）

这样可以消除主循环中的 if-else 分支混乱，提升代码可维护性。
"""

import asyncio
import logging
import time
import numpy as np
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from orcalink_client import OrcaLinkClient
    from test.rigid_body_physics import RigidBodyManager
    from test.sph_receiver import DataStatistics

logger = logging.getLogger(__name__)


class CouplingStrategy(ABC):
    """耦合模式策略基类"""
    
    @abstractmethod
    async def execute_network_cycle(self) -> None:
        """
        执行网络同步周期的模式特定逻辑
        
        在这个周期内执行：
        1. 接收远端数据（无条件接收，即使被暂停）
        2. 处理数据（计算、更新等）
        3. 准备待发送数据（但不发送，由主循环决定是否发送）
        """
        pass
    
    @abstractmethod
    def should_send_in_cycle(self) -> bool:
        """
        判断是否需要在当前周期发送数据
        
        Returns:
            True: 需要发送；False: 不需要发送
            
        说明：
        - ForcePositionStrategy: 检查流控后决定是否需要主循环调用 _publish_positions()
        - SpringConstraintStrategy: 已在 execute_network_cycle() 中完成发送，返回 False
        """
        pass
    
    @abstractmethod
    def get_mode_name(self) -> str:
        """获取模式名称"""
        pass


class ForcePositionStrategy(CouplingStrategy):
    """
    力-位置耦合模式策略
    
    工作流：
    1. 接收 SPH 发送的刚体受力 (FORCE 频道)
    2. 使用受力进行物理模拟 (运动学积分)
    3. 将计算结果 (位置) 发送回 SPH (POSITION 频道)
    """
    
    def __init__(self, client: 'OrcaLinkClient', rigid_bodies: 'RigidBodyManager'):
        """
        初始化力-位置策略
        
        Args:
            client: OrcaLink 客户端
            rigid_bodies: 刚体管理器
        """
        self.client = client
        self.rigid_bodies = rigid_bodies
    
    async def execute_network_cycle(self) -> None:
        """
        执行力-位置模式的网络周期
        
        步骤：
        1. 无条件接收力数据（即使被流控暂停也要接收）
        2. 更新刚体受力状态
        3. 数据已准备，由主循环根据流控决定是否发送
        """
        # 1. 无条件接收力数据（即使被暂停也接收，因为接收会更新 recv_count）
        forces = await self.client.subscribe_forces()
        
        if forces:
            logger.info(f"📥 Received {len(forces)} force updates")
            # 从 FORCE 频道接收来自 SPH 的刚体受力数据
            for force_data in forces:
                # 构造完整的 6D 向量 [fx, fy, fz, tx, ty, tz]
                force_torque_data = np.concatenate([force_data.force, force_data.torque])
                self.rigid_bodies.update_force(force_data.object_id, force_torque_data)
    
    def should_send_in_cycle(self) -> bool:
        """
        在力-位置模式中，位置发送由流控决定
        
        但这里返回 True，表示"有数据需要发送"，
        主循环会检查流控后决定是否真正发送
        """
        return True
    
    def get_mode_name(self) -> str:
        """返回模式名称"""
        return "force_position"


class SpringConstraintStrategy(CouplingStrategy):
    """
    弹簧约束耦合模式策略
    
    工作流：
    1. 发送本地刚体位姿到 OrcaLink
    2. 接收远端刚体位姿
    3. 基于位姿差异计算弹簧约束力
    4. 应用弹簧力进行物理积分
    """
    
    def __init__(self, client: 'OrcaLinkClient', rigid_bodies: 'RigidBodyManager', 
                 statistics: Optional['DataStatistics'] = None):
        """
        初始化弹簧约束策略
        
        Args:
            client: OrcaLink 客户端
            rigid_bodies: 刚体管理器
            statistics: 统计管理器（可选，用于记录力数据）
        """
        self.client = client
        self.rigid_bodies = rigid_bodies
        self.statistics = statistics
    
    async def execute_network_cycle(self) -> None:
        """
        执行弹簧约束模式的网络周期
        
        步骤：
        1. 收集本地刚体位姿
        2. 发送本地位姿到服务器
        3. 接收远端位姿
        4. 计算弹簧约束力
        5. 应用弹簧力到刚体
        
        说明：春约束模式在此步骤内完成发送和接收的完整循环
        """
        # 1. 收集本地刚体位姿
        local_positions = self.rigid_bodies.get_positions_snapshot()
        
        # 2. 发送本地位姿到服务器
        if local_positions:
            for pos in local_positions:
                logger.debug(f"  📤 [Sent to Remote] {pos.object_id}: pos=({pos.position[0]:.4f}, {pos.position[1]:.4f}, {pos.position[2]:.4f})")
            await self.client.publish_positions(local_positions)
        
        # 3. 接收远端位姿
        remote_positions = await self.client.subscribe_positions(max_count=100, enable_sync_window=True)
        # logger.info(f"[DEBUG] subscribe_positions_for_spring returned {len(remote_positions) if remote_positions else 0} positions")
        
        if remote_positions:
            logger.debug(f"[✅ Received] {len(remote_positions)} remote positions from SPH")
            for pos in remote_positions:
                logger.debug(f"  📥 [Received from Remote] {pos.object_id}: pos=({pos.position[0]:.4f}, {pos.position[1]:.4f}, {pos.position[2]:.4f})")
        for pos in remote_positions:
            self.client.remote_states[pos.object_id] = {
                'position': pos.position,
                'rotation': pos.rotation,
                'timestamp': time.time()
            }
        
        # 4. 获取本地速度
        local_velocities = self.rigid_bodies.get_velocities_dict()
        
        # 5. 计算弹簧约束力
        spring_forces = self.client.compute_spring_forces(
            local_positions, 
            local_velocities
        )
        
        # 6. 应用弹簧力到刚体
        if spring_forces:
            logger.debug(f"[OrcaLink-Python-Spring] Computed {len(spring_forces)} spring forces")
            self.rigid_bodies.apply_spring_forces(spring_forces)
            
            # 记录统计数据（如果统计管理器可用）
            if self.statistics:
                for sf in spring_forces:
                    self.statistics.add_force_value(
                        sf.object_id,
                        np.concatenate([sf.force, sf.torque])
                    )
    
    def should_send_in_cycle(self) -> bool:
        """
        在弹簧约束模式中，发送已在 execute_network_cycle() 完成
        
        Returns:
            False: 主循环无需额外发送数据
        """
        return False
    
    def get_mode_name(self) -> str:
        """返回模式名称"""
        return "spring_constraint"

