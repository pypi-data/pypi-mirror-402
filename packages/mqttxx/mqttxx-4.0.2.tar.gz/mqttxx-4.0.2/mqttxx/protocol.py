# MQTT RPC 消息协议 - MQTT 5.0 原生字段版本

from dataclasses import dataclass
from typing import Any, Optional
from paho.mqtt.properties import Properties
from paho.mqtt.packettypes import PacketTypes
import json

from .exceptions import MessageError, ErrorCode


@dataclass
class RPCRequest:
    """RPC 请求消息（MQTT 5.0 原生版）

    使用 MQTT 5.0 原生字段存储元数据：
    - ResponseTopic: reply_to（响应主题）
    - CorrelationData: request_id（请求关联数据）
    - UserProperty: caller_id（应用级元数据）

    Payload 存储业务数据：
    - method: 方法名
    - params: 参数

    Attributes:
        request_id: 请求唯一标识符（UUID）→ CorrelationData
        method: 远程方法名 → Payload
        params: 方法参数 → Payload
        reply_to: 响应主题 → ResponseTopic
        caller_id: 调用者标识符 → UserProperty

    示例:
        request = RPCRequest(
            request_id="123e4567-e89b-12d3-a456-426614174000",
            method="get_status",
            params={"device_id": "dev_001"},
            reply_to="client/response",
            caller_id="client_123"
        )

        # 编码为 MQTT 5.0 消息
        payload, props = encode_request(request)
        await client.publish("topic", payload, properties=props, qos=1)
    """

    request_id: str
    method: str
    params: Any = None
    reply_to: str = ""
    caller_id: str = ""


@dataclass
class RPCResponse:
    """RPC 响应消息（MQTT 5.0 原生版）

    使用 MQTT 5.0 原生字段存储元数据：
    - CorrelationData: request_id（请求关联数据）

    Payload 存储业务数据：
    - result: 返回值（成功时）
    - error: 错误消息（失败时）

    Attributes:
        request_id: 对应请求的唯一标识符 → CorrelationData
        result: 方法返回值（成功时） → Payload
        error: 错误消息（失败时） → Payload

    注意:
        result 和 error 只能有一个非空

    示例:
        # 成功响应
        response = RPCResponse(
            request_id="123e4567-e89b-12d3-a456-426614174000",
            result={"status": "online", "temperature": 25.5}
        )

        # 错误响应
        response = RPCResponse(
            request_id="123e4567-e89b-12d3-a456-426614174000",
            error="方法未找到: unknown_method"
        )
    """

    request_id: str
    result: Any = None
    error: Optional[str] = None


# 订阅标识符常量（用于区分请求/响应，替代 type 字段）
RPC_REQUEST_SUB_ID = 100
RPC_RESPONSE_SUB_ID = 200


# ============ 编码 ============

def encode_request(request: RPCRequest) -> tuple[bytes, Properties]:
    """编码 RPC 请求（使用 MQTT 5.0 原生字段）

    元数据分配：
    - ResponseTopic: reply_to
    - CorrelationData: request_id (bytes)
    - UserProperty: caller_id（可选）

    Args:
        request: RPC 请求对象

    Returns:
        (payload, properties) 元组

    示例:
        payload, props = encode_request(request)
        await client.publish("topic", payload, properties=props, qos=1)
    """
    payload = json.dumps({
        "method": request.method,
        "params": request.params,
    }).encode("utf-8")

    props = Properties(PacketTypes.PUBLISH)
    props.ResponseTopic = request.reply_to
    props.CorrelationData = request.request_id.encode("utf-8")

    if request.caller_id:
        props.UserProperty = [("caller_id", request.caller_id)]

    return payload, props


def encode_response(response: RPCResponse) -> tuple[bytes, Properties]:
    """编码 RPC 响应（使用 MQTT 5.0 原生字段）

    元数据分配：
    - CorrelationData: request_id (bytes)

    Args:
        response: RPC 响应对象

    Returns:
        (payload, properties) 元组

    示例:
        payload, props = encode_response(response)
        await client.publish("topic", payload, properties=props, qos=1)
    """
    if response.error is not None:
        payload_data = {"error": response.error}
    else:
        payload_data = {"result": response.result}

    payload = json.dumps(payload_data).encode("utf-8")

    props = Properties(PacketTypes.PUBLISH)
    props.CorrelationData = response.request_id.encode("utf-8")

    return payload, props


# ============ 解码 ============

def decode_request(payload: bytes, properties: Properties) -> RPCRequest:
    """从 MQTT 5.0 消息解码 RPC 请求

    Args:
        payload: 消息载荷（JSON bytes）
        properties: MQTT 5.0 Properties 对象

    Returns:
        RPC 请求对象

    Raises:
        MessageError: 缺少必需字段时抛出
        json.JSONDecodeError: JSON 解析失败
        UnicodeDecodeError: UTF-8 解码失败
    """
    try:
        data = json.loads(payload.decode("utf-8"))

        # 从 UserProperty 提取 caller_id
        caller_id = ""
        if properties.UserProperty:
            caller_id = dict(properties.UserProperty).get("caller_id", "")

        # 验证必需的原生字段
        if not properties.CorrelationData:
            raise ValueError("缺少 CorrelationData")

        return RPCRequest(
            request_id=properties.CorrelationData.decode("utf-8"),
            method=data.get("method", ""),
            params=data.get("params"),
            reply_to=properties.ResponseTopic or "",
            caller_id=caller_id,
        )
    except (ValueError, KeyError, UnicodeDecodeError) as e:
        raise MessageError(
            f"RPC 请求解码失败: {e}", ErrorCode.DECODE_ERROR
        )


def decode_response(payload: bytes, properties: Properties) -> RPCResponse:
    """从 MQTT 5.0 消息解码 RPC 响应

    Args:
        payload: 消息载荷（JSON bytes）
        properties: MQTT 5.0 Properties 对象

    Returns:
        RPC 响应对象

    Raises:
        MessageError: 缺少必需字段时抛出
        json.JSONDecodeError: JSON 解析失败
        UnicodeDecodeError: UTF-8 解码失败
    """
    try:
        data = json.loads(payload.decode("utf-8"))

        # 验证必需的原生字段
        if not properties.CorrelationData:
            raise ValueError("缺少 CorrelationData")

        return RPCResponse(
            request_id=properties.CorrelationData.decode("utf-8"),
            result=data.get("result"),
            error=data.get("error"),
        )
    except (ValueError, UnicodeDecodeError) as e:
        raise MessageError(
            f"RPC 响应解码失败: {e}", ErrorCode.DECODE_ERROR
        )


# ============ 消息类型路由 ============

def get_message_type(properties: Properties) -> str | None:
    """从 Subscription Identifier 获取消息类型

    Args:
        properties: MQTT 5.0 Properties 对象

    Returns:
        "request" | "response" | None
    """
    sub_id = getattr(properties, "SubscriptionIdentifier", None)
    if sub_id == RPC_REQUEST_SUB_ID:
        return "request"
    elif sub_id == RPC_RESPONSE_SUB_ID:
        return "response"
    return None


def parse_message(
    payload: bytes, properties: Properties
) -> RPCRequest | RPCResponse:
    """从 MQTT 5.0 消息解析 RPC 消息

    优先使用 SubscriptionIdentifier 区分类型（最快）
    如果不可用，则通过 Payload 内容兜底（向后兼容）

    Args:
        payload: 消息载荷（JSON bytes）
        properties: MQTT 5.0 Properties 对象

    Returns:
        RPC 请求或响应对象

    Raises:
        MessageError: 消息类型无效或解码失败
        json.JSONDecodeError: JSON 解析失败
        UnicodeDecodeError: UTF-8 解码失败

    示例:
        message = parse_message(msg.payload, msg.properties)

        if isinstance(message, RPCRequest):
            # 处理请求
            pass
        elif isinstance(message, RPCResponse):
            # 处理响应
            pass
    """
    # 优先使用 SubscriptionIdentifier（最快路径）
    msg_type = get_message_type(properties)

    if msg_type == "request":
        return decode_request(payload, properties)
    elif msg_type == "response":
        return decode_response(payload, properties)

    # 兜底：通过 Payload 内容判断（向后兼容非标准订阅）
    try:
        data = json.loads(payload.decode("utf-8"))
        if "method" in data:
            return decode_request(payload, properties)
        else:
            return decode_response(payload, properties)
    except (json.JSONDecodeError, UnicodeDecodeError, MessageError):
        raise MessageError(
            "无法确定消息类型（缺少 SubscriptionIdentifier 且 Payload 无法解析）",
            ErrorCode.INVALID_MESSAGE_TYPE
        )
