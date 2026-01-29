# Event Channel 层 - 基于 MQTT 5.0 的事件广播通道

import asyncio
import time
from typing import Callable, Any, Optional, overload, Awaitable, Union
from dataclasses import dataclass
from loguru import logger

from .client import MQTTClient
from .properties import (
    encode_payload_with_properties,
    get_property,
    extract_payload,
)
from paho.mqtt.properties import Properties


def _safe_subscribe_task(client: MQTTClient, pattern: str, dispatcher: Callable):
    """安全地执行异步订阅，处理异常

    这是一个 fire-and-forget 任务，但会记录异常。
    """
    async def _do_subscribe():
        try:
            await client.subscribe(pattern, dispatcher)
        except Exception as e:
            logger.error(f"订阅失败 - pattern: {pattern}, error: {e}")

    return asyncio.create_task(_do_subscribe())


def _safe_unsubscribe_task(client: MQTTClient, pattern: str, dispatcher: Callable):
    """安全地执行异步取消订阅，处理异常

    这是一个 fire-and-forget 任务，但会记录异常。

    Args:
        client: MQTTClient 实例
        pattern: MQTT 主题模式
        dispatcher: 事件分发器（未使用，保留用于兼容性）
    """
    async def _do_unsubscribe():
        try:
            # 使用底层取消订阅（不清理 MQTTClient 的 handlers）
            await client._raw_unsubscribe(pattern)
        except Exception as e:
            logger.error(f"取消订阅失败 - pattern: {pattern}, error: {e}")

    return asyncio.create_task(_do_unsubscribe())


@dataclass
class EventMessage:
    """事件消息（MQTT 5.0 版本）

    元数据通过 User Properties 传输：type, event_type, timestamp, source
    Payload 存储业务数据

    Attributes:
        event_type: 事件类型（如 "sensor.temperature"）
        data: 事件数据（任意 JSON 可序列化对象）
        timestamp: Unix 时间戳（自动填充）
        source: 事件源（可选）
    """

    event_type: str = ""
    data: Any = None
    timestamp: float = 0.0
    source: str = ""

    def __post_init__(self):
        """自动填充时间戳"""
        if self.timestamp == 0.0:
            self.timestamp = time.time()


# 事件处理器类型定义：支持同步和异步函数
# 参数：(topic: str, data: dict, properties: Properties)
EventHandler = Union[
    Callable[[str, dict, Properties], None],
    Callable[[str, dict, Properties], Awaitable[None]],
]


# 延迟注册全局注册表
_pending_subscriptions: list[tuple[str, EventHandler]] = []


def event_subscribe(pattern: str):
    """延迟订阅装饰器（模块级函数，不依赖实例）

    允许在模块导入时注册处理器，延迟到 EventChannelManager 实例化时自动绑定。
    """
    def decorator(handler: EventHandler):
        _pending_subscriptions.append((pattern, handler))
        return handler
    return decorator


class EventChannelManager:
    """Event Channel 管理器 - 基于 MQTT 5.0 的发布订阅层

    特性：
    - 使用 MQTT 5.0 User Properties 存储元数据
    - 支持通配符订阅（+, #）
    - 无返回值（fire-and-forget，非 RPC）

    与 RPC 共存：通过 User Properties 的 type 字段分流
    """

    def __init__(self, client: MQTTClient, auto_import: bool = True):
        """初始化 Event Channel 管理器

        Args:
            client: MQTTClient 实例
            auto_import: 是否自动导入延迟注册的处理器
        """
        self._client = client
        self._patterns: dict[str, list[EventHandler]] = {}
        self._dispatchers: dict[str, Callable] = {}

        if auto_import:
            self._import_pending_subscriptions()

        logger.info("EventChannelManager 已初始化")

    @overload
    def subscribe(
        self,
        pattern: str,
        handler: None = None
    ) -> Callable[[EventHandler], EventHandler]:
        """装饰器模式：返回装饰器函数"""
        ...

    @overload
    def subscribe(
        self,
        pattern: str,
        handler: EventHandler
    ) -> EventHandler:
        """直接注册模式：返回处理器本身"""
        ...

    def subscribe(self, pattern: str, handler: Optional[EventHandler] = None):
        """订阅事件主题（支持通配符）

        Args:
            pattern: MQTT 主题模式（支持 + 单级通配符、# 多级通配符）
            handler: 事件处理器，签名 handler(topic, data, properties)

        Returns:
            装饰器函数（如果 handler 为 None）
        """

        def decorator(func: EventHandler):
            if pattern not in self._patterns:
                self._patterns[pattern] = []

                # 创建专属 dispatcher
                async def dispatcher(topic: str, payload: bytes, properties=None):
                    """专属 dispatcher（bytes → dict → handlers）

                    性能优化：
                    1. 解码一次，传递给所有 handlers
                    2. 并发调用所有 handlers（非串行）
                    """
                    try:
                        # 解码 payload（只解码一次）
                        data = extract_payload(payload)

                        # 并发分发到所有 handlers
                        handlers = self._patterns.get(pattern, [])
                        if not handlers:
                            return

                        # 创建并发任务
                        tasks = []
                        for h in handlers:
                            if asyncio.iscoroutinefunction(h):
                                tasks.append(h(topic, data, properties))
                            else:
                                # 同步函数在线程池执行，避免阻塞事件循环
                                tasks.append(
                                    asyncio.get_event_loop().run_in_executor(
                                        None, h, topic, data, properties
                                    )
                                )

                        # 并发等待所有 handlers 完成
                        results = await asyncio.gather(*tasks, return_exceptions=True)

                        # 记录异常（不影响其他 handlers）
                        for h, result in zip(handlers, results):
                            if isinstance(result, Exception):
                                logger.exception(
                                    f"Event handler 异常 - pattern: {pattern}, error: {result}"
                                )

                    except Exception as e:
                        logger.error(f"事件消息解码失败 - topic: {topic}, error: {e}")

                # 保存 dispatcher 引用
                self._dispatchers[pattern] = dispatcher

                # 注册到 MQTTClient 层（异步，但 fire-and-forget 以保持装饰器可用）
                _safe_subscribe_task(self._client, pattern, dispatcher)

            self._patterns[pattern].append(func)
            logger.debug(
                f"事件订阅成功 - pattern: {pattern}, handlers: {len(self._patterns[pattern])}"
            )
            return func

        if handler is None:
            return decorator
        else:
            return decorator(handler)

    def unsubscribe(self, pattern: str, handler: Optional[EventHandler] = None):
        """取消订阅

        Args:
            pattern: MQTT 主题模式
            handler: 要移除的处理器（None = 移除所有）
        """
        if pattern not in self._patterns:
            return

        if handler is None:
            # 移除所有处理器
            del self._patterns[pattern]

            # 清理 dispatcher
            dispatcher = self._dispatchers.pop(pattern, None)
            if dispatcher:
                _safe_unsubscribe_task(self._client, pattern, dispatcher)

            logger.info(f"已取消订阅 - pattern: {pattern}")
        else:
            # 移除指定处理器
            if handler in self._patterns[pattern]:
                self._patterns[pattern].remove(handler)

                # 如果没有处理器了，清理 dispatcher
                if not self._patterns[pattern]:
                    del self._patterns[pattern]

                    dispatcher = self._dispatchers.pop(pattern, None)
                    if dispatcher:
                        _safe_unsubscribe_task(self._client, pattern, dispatcher)

                    logger.info(f"已取消订阅（最后一个 handler）- pattern: {pattern}")
                else:
                    logger.debug(
                        f"已移除处理器 - pattern: {pattern}, 剩余 {len(self._patterns[pattern])} 个"
                    )

    def _import_pending_subscriptions(self):
        """导入所有延迟注册的处理器"""
        if not _pending_subscriptions:
            return

        logger.info(f"导入 {len(_pending_subscriptions)} 个延迟订阅...")

        for pattern, handler in _pending_subscriptions:
            self.subscribe(pattern, handler)

        _pending_subscriptions.clear()
        logger.success("延迟订阅导入完成")

    async def publish(
        self,
        topic: str,
        message: EventMessage | dict | Any,
        qos: int = 0,
    ):
        """发布事件（fire-and-forget）

        Args:
            topic: 目标主题
            message: 事件消息（EventMessage / dict / 其他类型）
            qos: QoS 等级（0/1/2）
        """
        # 编码消息
        if isinstance(message, EventMessage):
            payload, properties = encode_event_message(message)
        elif isinstance(message, dict):
            payload, properties = encode_payload_with_properties(
                message,
                type="event",
            )
        else:
            # 其他类型自动包装
            payload, properties = encode_payload_with_properties(
                {"data": message},
                type="event",
            )

        # 发布消息
        await self._client.publish(topic, payload, qos=qos, properties=properties)


def encode_event_message(message: EventMessage) -> tuple[bytes, Properties]:
    """编码事件消息为 MQTT 5.0 消息

    Args:
        message: EventMessage 对象

    Returns:
        (payload, properties) 元组
    """
    return encode_payload_with_properties(
        message.data,
        type="event",
        event_type=message.event_type,
        timestamp=str(message.timestamp),
        source=message.source,
    )


def decode_event_message(payload: bytes, properties: Properties) -> EventMessage:
    """从 MQTT 5.0 消息解码事件消息

    Args:
        payload: 消息载荷（JSON bytes）
        properties: MQTT 5.0 Properties 对象

    Returns:
        EventMessage 对象
    """
    data = extract_payload(payload)
    return EventMessage(
        event_type=get_property(properties, "event_type"),
        data=data,
        timestamp=float(get_property(properties, "timestamp", "0")),
        source=get_property(properties, "source"),
    )
