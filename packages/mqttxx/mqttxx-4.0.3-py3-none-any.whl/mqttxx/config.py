# MQTT 客户端配置对象

from dataclasses import dataclass, field
from typing import Optional, Union
from paho.mqtt.client import MQTTv5, MQTT_CLEAN_START_FIRST_ONLY




@dataclass
class ReconnectConfig:
    """重连配置

    配置 MQTT 连接断开后的自动重连行为

    Attributes:
        enabled: 是否启用自动重连
        interval: 初始重连间隔（秒）
        max_attempts: 最大重连次数（0 = 无限重试）
        backoff_multiplier: 指数退避倍数（每次重连失败后，间隔乘以此倍数）
        max_interval: 最大重连间隔（秒）

    示例:
        # 无限重试，指数退避
        reconnect = ReconnectConfig(
            enabled=True,
            interval=5,
            max_attempts=0,
            backoff_multiplier=1.5,
            max_interval=60
        )

        # 固定间隔，最多重试 10 次
        reconnect = ReconnectConfig(
            interval=5,
            max_attempts=10,
            backoff_multiplier=1.0  # 不使用指数退避
        )
    """

    enabled: bool = True
    interval: int = 5
    max_attempts: int = 0
    backoff_multiplier: float = 1.5
    max_interval: int = 60


@dataclass
class MQTTConfig:
    """MQTT 客户端配置

    Attributes:
        broker_host: Broker 地址
        broker_port: Broker 端口（默认 1883）
        client_id: 客户端 ID（空=自动生成）
        keepalive: 心跳间隔秒数（默认 60）
        username: 用户名
        password: 密码
        protocol: 协议版本（默认 MQTTv5）
        reconnect: 重连配置
        max_queued_messages: 最大排队消息数（0=无限）
    """

    # 连接参数
    broker_host: str
    broker_port: int = 1883
    client_id: str = ""
    keepalive: int = 60
    username: Optional[str] = None
    password: Optional[str] = None
    protocol: int = MQTTv5
    clean_start: Union[bool, int] = MQTT_CLEAN_START_FIRST_ONLY

    # 子配置对象
    reconnect: ReconnectConfig = field(default_factory=ReconnectConfig)

    # 消息限制
    max_queued_messages: int = 0  # 0 = 无限


