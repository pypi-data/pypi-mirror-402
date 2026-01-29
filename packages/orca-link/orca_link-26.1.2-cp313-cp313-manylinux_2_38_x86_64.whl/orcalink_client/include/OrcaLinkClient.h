#ifndef __ORCALINK_CLIENT_H__
#define __ORCALINK_CLIENT_H__

#include <memory>
#include <string>
#include <vector>
#include <thread>
#include <atomic>
#include <mutex>

#include "DataStructures.h"
#include "ITransport.h"

namespace OrcaLink {

/// OrcaLink 客户端主类（无 gRPC 依赖）
/// 
/// 负责业务逻辑：时间控制、序列号管理、数据缓存等
/// 具体通信由注入的 ITransport 实现
class OrcaLinkClient {
public:
    /// 构造函数：依赖注入传输层
    /// @param transport 传输层实例（由调用者创建）
    explicit OrcaLinkClient(std::unique_ptr<ITransport> transport);
    
    ~OrcaLinkClient();
    
    // 禁用拷贝
    OrcaLinkClient(const OrcaLinkClient&) = delete;
    OrcaLinkClient& operator=(const OrcaLinkClient&) = delete;
    
    // ===== 生命周期管理 =====
    
    /// 初始化并连接服务器
    bool Initialize(const OrcaLinkConfig& config);
    
    /// 关闭连接
    void Shutdown();
    
    /// 重置状态（仿真重启时调用）
    /// @return 重置成功返回 true
    bool Reset();
    
    // ===== 会话管理 =====
    
    /// 加入/创建会话
    bool JoinSession(uint32_t sessionId, const std::string& clientName);
    
    // ===== 数据发布 =====
    
    /// 发布刚体受力数据（每帧调用，同步）
    bool PublishForces(const std::vector<RigidBodyForce>& forces);
    
    /// 异步发布刚体受力数据（非阻塞）
    bool PublishForcesAsync(const std::vector<RigidBodyForce>& forces);
    
    /// 发布刚体位置数据（用于春约束耦合模式）
    bool PublishPositions(const std::vector<RigidBodyPosition>& positions);
    
    // ===== 数据订阅 =====
    
    /// 获取刚体位置数据（每帧调用）
    bool SubscribePositions(std::vector<RigidBodyPosition>& positions);
    
    // ===== 时间控制 =====
    
    /// 获取数据交换频率（Hz）
    float GetUpdateRateHz() const;
    
    /// 检查是否应该执行数据交换
    /// @param currentTime 当前仿真时间
    /// @return 如果到达更新时间返回 true
    bool ShouldUpdate(Real currentTime) const;
    
    /// 推进到下一个更新时间
    void AdvanceUpdateTime();
    
    /// 设置下一个更新时间
    /// @param time 下一个更新的仿真时间
    void SetNextUpdateTime(Real time);
    
    // ===== 状态查询 =====
    
    /// 检查是否已连接
    bool IsConnected() const;
    
    /// 检查会话是否活跃
    bool IsSessionActive() const;
    
    /// 获取会话 ID
    uint32_t GetSessionId() const { return m_sessionId; }
    
    /// 获取客户端名称
    const std::string& GetClientName() const { return m_clientName; }
    
    /// 获取发布的帧序列号
    uint64_t GetPublishSequence() const { return m_publishSequence; }
    
    // ===== 中央流控管理 =====
    
    /// 检查是否应该暂停本周期的数据发送
    /// @return true 表示应该暂停，false 表示继续
    bool ShouldPauseThisCycle();
    
    /// 获取会话就绪状态
    bool IsSessionReady() const { return m_sessionReady; }
    
    /// 等待远端追上（用于流控）
    bool WaitForRemote(uint32_t channelId, uint32_t maxWaitMs = 100);

private:
    std::unique_ptr<ITransport> m_transport;  // 注入的传输层
    
    // 会话状态
    uint32_t m_sessionId;
    std::string m_clientName;
    bool m_sessionActive;
    
    // 频道 ID
    uint32_t m_forceChannelId;     // 发布 FORCE 的频道
    uint32_t m_positionChannelId;  // 订阅 POSITION 的频道
    
    // 配置
    OrcaLinkConfig m_config;
    
    // 序列号管理
    uint64_t m_publishSequence;
    uint64_t m_subscribeSequence;
    
    // 时间控制
    float m_updateRateHz = 30.0f;
    Real m_nextUpdateTime = 0.0;
    
    // 中央流控管理（服务端控制）
    uint32_t m_pendingPauseCycles = 0;  // 待执行的暂停周期数
    bool m_sessionReady = false;        // 会话是否就绪
    float m_speedRatioThreshold = 1.0f; // 速度比阈值（从服务端同步）
    
    // 同步模式窗口管理（客户端本地控制）
    int32_t m_currentSyncWindow = 0;    // 当前同步窗口计数
    
    // 异步处理
    std::thread m_workerThread;
    std::atomic<bool> m_running;
    std::atomic<bool> m_hasPendingRequest;
    std::mutex m_requestMutex;
    std::vector<RigidBodyForce> m_pendingForces;
    
    // 私有方法
    
    /// 工作线程函数
    void WorkerThreadFunction();
    
    /// 内部发布函数
    bool PublishForcesInternal(const std::vector<RigidBodyForce>& forces);
    
    /// 内部位置发布函数
    bool PublishPositionsInternal(const std::vector<RigidBodyPosition>& positions);
    
    /// 内部订阅函数
    bool SubscribePositionsInternal(std::vector<RigidBodyPosition>& positions);
};

} // namespace OrcaLink

#endif // __ORCALINK_CLIENT_H__

