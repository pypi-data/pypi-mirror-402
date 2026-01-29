"""MQTTX - 基于 MQTT 5.0 的高级 MQTT 客户端和 RPC 框架

提供：
- MQTTClient: MQTT 连接管理（自动重连、订阅队列化）
- RPCManager: 双向对等 RPC 调用（超时控制、离线检测）
- EventChannelManager: 高吞吐事件广播通道（单向、无返回值）
- 配置对象: MQTTConfig, ReconnectConfig
- 协议定义: RPCRequest, RPCResponse, EventMessage
- 异常系统: 统一错误码和异常层次

MQTT 5.0 特性：
- 使用 ResponseTopic/CorrelationData 存储请求-响应元数据
- Payload 纯净，只包含业务数据
- 使用 User Properties 存储应用级元数据
"""

__version__ = "4.0.2"
__author__ = "MQTTX Team"

# 核心客户端
from .client import MQTTClient

# RPC 管理器
from .rpc import RPCManager

# Event Channel 管理器
from .events import EventChannelManager, EventMessage, event_subscribe

# Properties 工具
from .properties import (
    encode_payload_with_properties,
    user_properties_to_dict,
    get_property,
    extract_payload,
)

# 配置对象
from .config import (
    MQTTConfig,
    ReconnectConfig,
)

# 协议定义
from .protocol import (
    RPCRequest,
    RPCResponse,
    encode_request,
    encode_response,
    decode_request,
    decode_response,
    parse_message,
)

# 异常系统
from .exceptions import (
    # 错误码
    ErrorCode,
    # 基础异常
    MQTTXError,
    MessageError,
    RPCError,
    # RPC 异常
    RPCTimeoutError,
    RPCRemoteError,
)

__all__ = [
    # MQTT 客户端
    "MQTTClient",
    # RPC 管理器
    "RPCManager",
    # Event Channel 管理器
    "EventChannelManager",
    "EventMessage",
    "event_subscribe",
    # Properties 工具
    "encode_payload_with_properties",
    "user_properties_to_dict",
    "get_property",
    "extract_payload",
    # 配置对象
    "MQTTConfig",
    "ReconnectConfig",
    # 协议定义
    "RPCRequest",
    "RPCResponse",
    "encode_request",
    "encode_response",
    "decode_request",
    "decode_response",
    "parse_message",
    # 异常系统
    "ErrorCode",
    "MQTTXError",
    "MessageError",
    "RPCError",
    "RPCTimeoutError",
    "RPCRemoteError",
]
