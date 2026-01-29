#ifndef __ORCALINK_ITRANSPORT_H__
#define __ORCALINK_ITRANSPORT_H__

#include "DataStructures.h"
#include <memory>
#include <string>
#include <vector>

namespace OrcaLink {

/**
 * @brief 抽象传输层接口
 * 
 * 定义了 OrcaLink 客户端的所有通信操作，具体实现由各项目提供
 * （例如：gRPC、ZeroMQ、共享内存等）
 */
class ITransport {
public:
    virtual ~ITransport() = default;
    
    // ===== 生命周期管理 =====
    
    /// 连接到服务器
    /// @param serverAddress 服务器地址（格式由实现决定，如 "localhost:50351"）
    /// @return 成功返回 true
    virtual bool Connect(const std::string& serverAddress) = 0;
    
    /// 断开连接
    virtual void Disconnect() = 0;
    
    /// 检查是否已连接
    virtual bool IsConnected() const = 0;
    
    // ===== 会话管理 =====
    
    /// 加入或创建会话
    /// @param sessionId 会话ID
    /// @param clientName 客户端名称
    /// @param config 会话配置
    /// @return 成功返回 true
    virtual bool JoinSession(
        uint32_t sessionId,
        const std::string& clientName,
        const OrcaLinkConfig& config) = 0;
    
    /// 离开会话
    virtual bool LeaveSession() = 0;
    
    /// 检查会话是否活跃
    virtual bool IsSessionActive() const = 0;
    
    // ===== 数据发布 =====
    
    /// 发布刚体受力数据（同步）
    /// @param forces 力数据列表
    /// @param channelId 通道ID
    /// @param sequence 序列号
    /// @return 成功返回 true
    virtual bool PublishForces(
        const std::vector<RigidBodyForce>& forces,
        uint32_t channelId,
        uint64_t sequence) = 0;
    
    /// 发布刚体位置数据（同步）
    /// @param positions 位置数据列表
    /// @param channelId 通道ID
    /// @param sequence 序列号
    /// @return 成功返回 true
    virtual bool PublishPositions(
        const std::vector<RigidBodyPosition>& positions,
        uint32_t channelId,
        uint64_t sequence) = 0;
    
    // ===== 数据订阅 =====
    
    /// 订阅刚体位置数据
    /// @param positions 输出：接收到的位置数据
    /// @param channelId 通道ID
    /// @param sequence 期望的序列号
    /// @return 成功返回 true
    virtual bool SubscribePositions(
        std::vector<RigidBodyPosition>& positions,
        uint32_t channelId,
        uint64_t sequence) = 0;
    
    // ===== 流控支持 =====
    
    /// 查询远端最新序列号（用于流控）
    /// @param channelId 通道ID
    /// @return 最新序列号，失败返回 0
    virtual uint64_t GetRemoteSequence(uint32_t channelId) = 0;
    
    /// 等待远端追上指定序列号
    /// @param channelId 通道ID
    /// @param targetSequence 目标序列号
    /// @param timeoutMs 超时时间（毫秒）
    /// @return 成功返回 true
    virtual bool WaitForRemoteSequence(
        uint32_t channelId,
        uint64_t targetSequence,
        uint32_t timeoutMs) = 0;
};

/**
 * @brief 传输层工厂接口
 * 
 * 用于创建特定类型的传输层实现
 */
class ITransportFactory {
public:
    virtual ~ITransportFactory() = default;
    
    /// 创建传输层实例
    virtual std::unique_ptr<ITransport> CreateTransport() = 0;
};

} // namespace OrcaLink

#endif // __ORCALINK_ITRANSPORT_H__

