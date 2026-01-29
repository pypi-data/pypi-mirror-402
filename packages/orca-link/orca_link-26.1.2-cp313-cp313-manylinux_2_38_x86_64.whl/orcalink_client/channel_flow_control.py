"""
OrcaLink 通道流控管理
与 C++ ChannelFlowControl 对等的 Python 实现
"""

from dataclasses import dataclass, field


@dataclass
class ChannelFlowControlStats:
    """通道流控统计"""
    send_count: int = 0
    recv_count: int = 0
    send_ahead: int = 0
    is_paused: bool = False
    total_pauses: int = 0
    last_log_frame: int = 0
    remote_acked_sequence: int = 0  # 对方已确认的序列号（NEW）
    paused_acked_baseline: int = 0  # 暂停时的 ACK 基准（NEW）


class ChannelFlowControl:
    """通道级流控管理"""
    
    def __init__(self, channel_id: int, is_publisher: bool, is_subscriber: bool):
        """
        初始化通道流控
        
        Args:
            channel_id: 频道ID
            is_publisher: 是否为发布端
            is_subscriber: 是否为订阅端
        """
        self.channel_id = channel_id
        self.is_publisher = is_publisher
        self.is_subscriber = is_subscriber
        self.is_bidirectional = is_publisher and is_subscriber
        self.stats = ChannelFlowControlStats()
    
    def record_send(self) -> None:
        """记录发送一条消息"""
        self.stats.send_count += 1
        self._update_send_ahead()
    
    def record_recv(self, count: int = 1) -> None:
        """
        记录接收消息
        
        Args:
            count: 接收的消息数（默认1）
        """
        self.stats.recv_count += count
        self._update_send_ahead()
    
    def should_pause(self, max_ahead: int) -> bool:
        """
        检查是否应该暂停
        
        Args:
            max_ahead: 最大超前帧数
            
        Returns:
            如果应该暂停则返回 True
        """
        # 仅对双向通道启用流控
        if not self.is_bidirectional:
            return False
        
        return self.stats.send_ahead > max_ahead
    
    def can_resume(self, min_ahead: int) -> bool:
        """
        检查是否可以恢复
        
        Args:
            min_ahead: 最小超前帧数阈值
            
        Returns:
            如果可以恢复则返回 True
        """
        return self.stats.send_ahead <= min_ahead
    
    def set_paused(self, paused: bool) -> None:
        """
        设置暂停状态
        
        Args:
            paused: 是否暂停
        """
        if paused and not self.stats.is_paused:
            self.stats.total_pauses += 1
        self.stats.is_paused = paused
    
    def get_stats(self) -> ChannelFlowControlStats:
        """获取统计信息"""
        return self.stats
    
    def set_remote_acked_sequence(self, sequence: int) -> None:
        """设置对方已确认的序列号（NEW）"""
        self.stats.remote_acked_sequence = sequence
        self._update_send_ahead()
    
    def get_remote_acked_sequence(self) -> int:
        """获取对方已确认的序列号（NEW）"""
        return self.stats.remote_acked_sequence
    
    def set_paused_acked_baseline(self, baseline: int) -> None:
        """设置暂停时的 ACK 基准（NEW）"""
        self.stats.paused_acked_baseline = baseline
    
    def get_paused_acked_baseline(self) -> int:
        """获取暂停时的 ACK 基准（NEW）"""
        return self.stats.paused_acked_baseline
    
    def _update_send_ahead(self) -> None:
        """更新超前数"""
        # Use remote_acked_sequence for bounded async flow control
        # Falls back to recv_count if remote_acked_sequence is 0 (old server)
        baseline = self.stats.remote_acked_sequence if self.stats.remote_acked_sequence > 0 else self.stats.recv_count
        self.stats.send_ahead = self.stats.send_count - baseline

