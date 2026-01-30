"""
OrcaLink Python Client Library

提供与 C++ OrcaLinkClient 功能对等的 Python 实现，包括流控、时间控制等完整功能。
"""

__version__ = "1.0.0"

__all__ = [
    "OrcaLinkClient",
    "ChannelFlowControl",
    "load_config_from_json",
    "RigidBodyForce",
    "RigidBodyPosition",
    "OrcaLinkChannelConfig",
    "FlowControlChannelPair",
    "FlowControlConfig",
    "OrcaLinkConfig",
]


def __getattr__(name):
    """延迟导入模块，避免在导入 cli 时触发不必要的导入"""
    if name == "OrcaLinkClient":
        from .orcalink_client import OrcaLinkClient
        return OrcaLinkClient
    elif name == "ChannelFlowControl":
        from .channel_flow_control import ChannelFlowControl
        return ChannelFlowControl
    elif name == "load_config_from_json":
        from .config_loader import load_config_from_json
        return load_config_from_json
    elif name == "RigidBodyForce":
        from .data_structures import RigidBodyForce
        return RigidBodyForce
    elif name == "RigidBodyPosition":
        from .data_structures import RigidBodyPosition
        return RigidBodyPosition
    elif name == "OrcaLinkChannelConfig":
        from .data_structures import OrcaLinkChannelConfig
        return OrcaLinkChannelConfig
    elif name == "FlowControlChannelPair":
        from .data_structures import FlowControlChannelPair
        return FlowControlChannelPair
    elif name == "FlowControlConfig":
        from .data_structures import FlowControlConfig
        return FlowControlConfig
    elif name == "OrcaLinkConfig":
        from .data_structures import OrcaLinkConfig
        return OrcaLinkConfig
    
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
