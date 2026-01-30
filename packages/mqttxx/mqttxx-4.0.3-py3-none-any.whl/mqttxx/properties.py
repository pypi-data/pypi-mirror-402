# MQTT 5.0 Properties 工具模块

from typing import Any
import json
from paho.mqtt.properties import Properties
from paho.mqtt.packettypes import PacketTypes


def user_properties_to_dict(properties: Properties | None) -> dict[str, str]:
    """将 User Properties 转为字典"""
    if properties is None or not properties.UserProperty:
        return {}
    return dict(properties.UserProperty)


def dict_to_user_properties(data: dict[str, str]) -> list[tuple[str, str]]:
    """字典转 User Properties 列表"""
    return list(data.items())


def create_publish_properties(**user_props: str) -> Properties:
    """创建 PUBLISH 包的 Properties"""
    props = Properties(PacketTypes.PUBLISH)
    if user_props:
        props.UserProperty = dict_to_user_properties(user_props)
    return props


def encode_payload_with_properties(
    payload_data: Any,
    **user_props: str,
) -> tuple[bytes, Properties]:
    """编码 payload 和 User Properties"""
    payload = json.dumps(payload_data).encode("utf-8")
    properties = create_publish_properties(**user_props)
    return payload, properties


def get_property(properties: Properties | None, key: str, default: str = "") -> str:
    """获取单个 User Property"""
    props_dict = user_properties_to_dict(properties)
    return props_dict.get(key, default)


def get_property_or_raise(properties: Properties | None, key: str) -> str:
    """获取 User Property（不存在则抛出异常）"""
    value = get_property(properties, key)
    if not value:
        raise ValueError(f"缺少必需的 User Property: {key}")
    return value


def extract_payload(payload: bytes) -> Any:
    """从 payload bytes 提取数据（JSON 反序列化）"""
    return json.loads(payload.decode("utf-8"))
