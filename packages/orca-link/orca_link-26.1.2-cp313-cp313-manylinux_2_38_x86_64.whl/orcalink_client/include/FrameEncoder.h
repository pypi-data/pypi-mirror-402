#ifndef __ORCALINK_FRAME_ENCODER_H__
#define __ORCALINK_FRAME_ENCODER_H__

#include <vector>
#include <cstdint>
#include "orcalink.pb.h"
#include "DataStructures.h"

namespace OrcaLink {

/// I/P 帧编码器
class FrameEncoder {
public:
    FrameEncoder();
    ~FrameEncoder();
    
    // ===== 配置 =====
    
    /// 设置 I 帧间隔（每 N 帧发送 I 帧）
    void SetIFrameInterval(uint32_t interval);
    
    /// 设置变化阈值
    void SetChangeThreshold(float threshold);
    
    // ===== 编码 =====
    
    /// 编码力数据帧（自动决定 I/P 帧）
    orca::DataFrame EncodeFrame(const std::vector<RigidBodyForce>& forces);
    
    /// 重置编码器（强制下一帧为 I 帧）
    void Reset();
    
    /// 获取当前帧序列号
    uint64_t GetCurrentSequence() const { return m_frameId; }

private:
    uint32_t m_frameId;                    // 当前帧 ID
    uint32_t m_iFrameInterval;             // I 帧发送间隔
    uint32_t m_framesSinceIFrame;          // 上次 I 帧以来的帧数
    float m_changeThreshold;               // 变化阈值
    
    // 参考帧数据
    std::vector<RigidBodyForce> m_referenceFrame;
    uint64_t m_referenceSequence;
    
    // 私有方法
    
    /// 决定是否应该发送 I 帧
    bool ShouldSendIFrame(const std::vector<RigidBodyForce>& current);
    
    /// 计算变化的索引（用于 P 帧）
    std::vector<uint32_t> ComputeChangedIndices(
        const std::vector<RigidBodyForce>& current);
    
    /// 计算两个力向量的差异程度
    float ComputeForceDifference(const RigidBodyForce& f1, const RigidBodyForce& f2) const;
};

} // namespace OrcaLink

#endif // __ORCALINK_FRAME_ENCODER_H__

