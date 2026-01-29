#ifndef __ORCALINK_DATA_STRUCTURES_H__
#define __ORCALINK_DATA_STRUCTURES_H__

#include <string>
#include <vector>
#include <cstdint>
#include <Eigen/Dense>

namespace OrcaLink {

// Type aliases from SPlisHSPlasH
using Real = float;
using Vector3r = Eigen::Matrix<Real, 3, 1, Eigen::DontAlign>;
using Quaternionr = Eigen::Quaternion<Real, Eigen::DontAlign>;

// ============================================================
// 刚体数据结构
// ============================================================

/// 刚体受力数据
struct RigidBodyForce {
    std::string objectId;      // 对象标识符
    Vector3r force;       // 力 (N)
    Vector3r torque;      // 扭矩 (N·m)
    
    RigidBodyForce() 
        : force(Vector3r::Zero()), torque(Vector3r::Zero()) {}
    
    RigidBodyForce(const std::string& id, 
                   const Vector3r& f, 
                   const Vector3r& t)
        : objectId(id), force(f), torque(t) {}
};

/// 刚体位置数据
/// 注意：四元数顺序遵循 MuJoCo/Hamilton 约定 [w, x, y, z]
///       Eigen Quaternionr 内部存储为 [x, y, z, w]，但构造函数接受 (w, x, y, z)
struct RigidBodyPosition {
    std::string objectId;      // 对象标识符
    Vector3r position;    // 位置 (m)
    Quaternionr rotation; // 旋转（四元数，Eigen 格式）
    
    RigidBodyPosition()
        : position(Vector3r::Zero()), 
          rotation(Quaternionr::Identity()) {}
    
    RigidBodyPosition(const std::string& id,
                      const Vector3r& pos,
                      const Quaternionr& rot)
        : objectId(id), position(pos), rotation(rot) {}
};

// ============================================================
// 配置结构
// ============================================================

/// OrcaLink 频道配置
struct OrcaLinkChannelConfig {
    uint32_t channelId = 0;
    bool publish = false;
    bool subscribe = false;
    
    OrcaLinkChannelConfig() = default;
    OrcaLinkChannelConfig(uint32_t id, bool pub, bool sub) 
        : channelId(id), publish(pub), subscribe(sub) {}
};

/// 滑动窗口流控通道对配置
struct FlowControlChannelPair {
    std::string name;           // 配对名称
    uint32_t sendChannelId;     // 发送通道ID
    uint32_t recvChannelId;     // 接收通道ID
    bool enabled = true;        // 是否启用此配对的流控
    
    FlowControlChannelPair() = default;
    FlowControlChannelPair(const std::string& n, uint32_t sendId, uint32_t recvId, bool en = true)
        : name(n), sendChannelId(sendId), recvChannelId(recvId), enabled(en) {}
};

/// 滑动窗口流控配置
struct FlowControlConfig {
    bool enabled = true;               // 是否启用流控
    uint32_t maxSendAhead = 3;         // 最大超前发送数
    uint32_t minSendAhead = 1;         // 恢复正常阈值
    float pollIntervalMs = 5.0f;       // 轮询间隔（毫秒）
    float maxWaitTimeSec = 0.1f;       // 最大等待时间（秒）
    bool enableLogging = true;         // 启用日志
    uint32_t logIntervalFrames = 50;   // 日志间隔（帧数）
    std::vector<FlowControlChannelPair> channelPairs;  // 通道对列表
};

/// OrcaLink 客户端配置
struct OrcaLinkConfig {
    bool enabled = false;
    std::string serverAddress = "localhost:50351";
    uint32_t sessionId = 1;
    std::string clientName = "SPlisHSPlasH";
    float updateRateHz = 30.0f;        // 数据交换频率 (Hz)
    
    OrcaLinkChannelConfig forceChannel = {1, true, false};
    OrcaLinkChannelConfig positionChannel = {2, false, true};
    
    // I/P 帧编码配置
    uint32_t iFrameInterval = 30;      // 每 N 帧发送 I 帧
    float changeThreshold = 0.001f;    // 变化阈值
    
    // 异步处理
    bool asyncEnabled = true;
    
    // 会话配置（NEW: 支持同步/异步模式）
    struct SessionConfig {
        std::string controlMode = "async";  // "sync" 或 "async"
        
        struct AsyncParams {
            bool flowControlEnabled = true;
            uint32_t flowControlWindowSize = 10;
            float speedRatioThreshold = 2.0f;
        };
        AsyncParams asyncParams;
        
        struct SyncParams {
            uint32_t syncWindowSize = 1;  // 1~3
        };
        SyncParams syncParams;
        
        uint32_t expectedClients = 2;
        float readyTimeoutSec = 30.0f;
        float grpcCallTimeoutSec = 5.0f;
    };
    SessionConfig sessionConfig;
    
    // 向后兼容：保留旧字段（已废弃，使用 sessionConfig 替代）
    // @deprecated 使用 sessionConfig.asyncParams 替代
    bool flowControlEnabled = true;
    uint32_t flowControlWindowSize = 10;
    float speedRatioThreshold = 2.0f;
    uint32_t expectedClients = 2;
    float readyTimeoutSec = 30.0f;
    float grpcCallTimeoutSec = 5.0f;
    
    // NEW: 耦合模式（用于握手一致性检查）
    std::string couplingMode = "force_position";  // "force_position" 或 "spring_constraint"
};

} // namespace OrcaLink

#endif // __ORCALINK_DATA_STRUCTURES_H__