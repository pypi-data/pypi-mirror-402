#ifndef __ORCALINK_DATA_MAPPER_H__
#define __ORCALINK_DATA_MAPPER_H__

#include <string>
#include <vector>
#include "orcalink.pb.h"
#include "DataStructures.h"

namespace OrcaLink {

/// 数据映射器：SPlisHSPlasH <-> OrcaLink 协议
class DataMapper {
public:
    DataMapper();
    ~DataMapper();
    
    // ===== 发布侧：SPlisHSPlasH -> OrcaLink =====
    
    /// 将 RigidBodyForce 映射到 DataUnit
    static orca::DataUnit MapForceToDataUnit(const RigidBodyForce& force);
    
    /// 将力数据列表映射到 DataFrame
    static orca::DataFrame MapForcesToFrame(
        const std::vector<RigidBodyForce>& forces,
        uint64_t sequence,
        orca::FrameType frameType = orca::FRAME_TYPE_IFRAME);
    
    // ===== 订阅侧：OrcaLink -> SPlisHSPlasH =====
    
    /// 从 DataUnit 解析位置数据
    static RigidBodyPosition ParsePositionFromDataUnit(const orca::DataUnit& unit);
    
    /// 从 DataFrame 列表解析所有位置数据
    static std::vector<RigidBodyPosition> ParsePositionsFromFrames(
        const std::vector<orca::DataFrame>& frames);
    
    // ===== 坐标系转换 =====
    // 参考 ParticleRender 的已验证实现
    // SPlisHSPlasH: X=right, Y=up, Z=forward
    // MuJoCo/Orca:  X=forward, Y=left, Z=up
    
    /// SPlisHSPlasH (Y-up) -> OrcaLink/MuJoCo (Z-up)
    /// [x, y, z]_sph -> [x, -z, y]_orca
    /// 适用于：位置、力、扭矩、速度等所有向量类型
    static void ConvertToOrcaCoordinates(Vector3r& v);
    
    /// OrcaLink/MuJoCo (Z-up) -> SPlisHSPlasH (Y-up)
    /// [x, y, z]_orca -> [x, z, -y]_sph
    /// 适用于：位置、力、扭矩、速度等所有向量类型
    static void ConvertFromOrcaCoordinates(Vector3r& v);
    
    /// 四元数坐标系转换：SPlisHSPlasH (Y-up) -> OrcaLink/MuJoCo (Z-up)
    /// 通过旋转矩阵变换实现：R' = T * R * T^T
    static void ConvertQuaternionToOrca(Quaternionr& q);
    
    /// 四元数坐标系转换：OrcaLink/MuJoCo (Z-up) -> SPlisHSPlasH (Y-up)
    /// 通过旋转矩阵变换实现：R' = T^T * R * T
    static void ConvertQuaternionFromOrca(Quaternionr& q);

private:
    // 辅助方法
    
    /// 解析 object_id 获取刚体索引
    static uint32_t ParseRigidBodyIndex(const std::string& objectId);
    
    /// 生成 object_id
    static std::string GenerateObjectId(uint32_t rigidBodyIndex);
};

} // namespace OrcaLink

#endif // __ORCALINK_DATA_MAPPER_H__

