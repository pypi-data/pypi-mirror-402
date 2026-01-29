# aiomqtt 高级封装 - 基于纯 async/await 架构

import asyncio
from typing import Callable, Optional, Any, Awaitable, Union
from loguru import logger
import aiomqtt
from paho.mqtt.matcher import MQTTMatcher

from .config import MQTTConfig
from .exceptions import MQTTXError, ErrorCode

# Handler 类型定义：支持同步和异步函数
# 同步：def handler(topic: str, payload: bytes, properties) -> None
# 异步：async def handler(topic: str, payload: bytes, properties) -> None
MessageHandler = Union[
    Callable[[str, bytes, Any], None],
    Callable[[str, bytes, Any], Awaitable[None]],
]


class MQTTClient:
    """基于 aiomqtt 的 MQTT 客户端

    设计决策：
    - aiomqtt 基于 paho-mqtt 封装，成熟稳定
    - 不自动重连，需要手动实现重连循环（官方推荐模式）
    - 使用 `async for message in client.messages` 异步迭代器


    并发安全:
        - ✅ 单 loop 内并发调用 subscribe/unsubscribe：安全

    示例:
        # ✅ 正确：单 loop
        async def main():
            client = MQTTClient(config)
            await client.connect()
            client.subscribe("topic", handler1)  # 安全
            client.subscribe("topic", handler2)  # 安全

    """

    def __init__(self, config: MQTTConfig):
        """初始化 MQTT 客户端

        Args:
            config: MQTT 配置对象

        注意:
            初始化后不会立即连接，需要调用 connect() 或使用 async with
        """
        self.config = config
        self._client: Optional[aiomqtt.Client] = None

        # Raw 订阅（使用 MQTTMatcher 进行通配符匹配）
        self._raw_matcher = MQTTMatcher()
        self._raw_handlers: dict[str, list[Callable]] = {}

        self._running = False
        self._connected = False  # 真实连接状态标志
        self._reconnect_task: Optional[asyncio.Task] = None
        self._message_task: Optional[asyncio.Task] = None

    async def connect(self):
        """连接到 MQTT Broker

        启动后台重连任务，自动处理连接断开和重连

        """
        if self._running:
            logger.warning("客户端已在运行中")
            return

        self._running = True

        # 创建 aiomqtt.Client（只创建一次，在重连循环中复用）
        self._client = aiomqtt.Client(
            hostname=self.config.broker_host,
            port=self.config.broker_port,
            username=self.config.username,
            password=self.config.password,
            identifier=self.config.client_id or None,
            keepalive=self.config.keepalive,
            max_queued_outgoing_messages=self.config.max_queued_messages or None,
            protocol=self.config.protocol,
            clean_start=self.config.clean_start,
        )
        # 修复 aiomqtt 的垃圾警告：高并发 publish 时会产生大量 "pending publish calls" 日志
        # aiomqtt 在 __init__ 中硬编码了 pending_calls_threshold = 10，无法通过参数修改
        # 只能在创建 Client 后手动修改这个实例属性
        self._client.pending_calls_threshold = 999999

        self._reconnect_task = asyncio.create_task(
            self._reconnect_loop(), name="mqtt_reconnect"
        )

        # 等待首次连接建立（最多 60 秒）
        for _ in range(600):  # 60 秒超时，每次检查 0.1 秒
            if self._connected:
                break
            await asyncio.sleep(0.1)
        else:
            self._running = False  # 清理状态
            raise TimeoutError(
                f"MQTT 连接超时（60秒）：{self.config.broker_host}:{self.config.broker_port}"
            )

    async def disconnect(self):
        """断开连接并清理资源"""
        self._running = False
        self._connected = False

        # 取消后台任务
        if self._reconnect_task:
            self._reconnect_task.cancel()
            try:
                await self._reconnect_task
            except asyncio.CancelledError:
                pass

        # 取消消息处理任务（修复 P0-D）
        # 这会导致 _reconnect_loop 中的 async with 块退出，aiomqtt 自动清理连接
        if self._message_task:
            self._message_task.cancel()
            try:
                await self._message_task
            except asyncio.CancelledError:
                pass

        self._client = None

        logger.info("MQTT 客户端已断开")

    async def __aenter__(self):
        """上下文管理器入口

        示例:
            async with MQTTClient(config) as client:
                # 使用客户端
                pass  # 自动断开连接
        """
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """上下文管理器退出"""
        await self.disconnect()

    async def _reconnect_loop(self):
        """重连循环（aiomqtt 核心模式）

        无限循环尝试连接 MQTT Broker，连接断开后自动重连

        重连策略：
        - 初始间隔：config.reconnect.interval（默认 5 秒）
        - 指数退避：每次失败后间隔乘以 backoff_multiplier
        - 最大间隔：config.reconnect.max_interval（默认 60 秒）
        - 最大次数：config.reconnect.max_attempts（0 = 无限）


        异常处理：
        - aiomqtt.MqttError：连接/协议错误，触发重连
        - asyncio.CancelledError：任务被取消，退出循环

        关键改进：
        - Client 在 connect() 中创建（只创建一次）
        - 循环内只使用 async with self._client: 来连接
        - 符合 aiomqtt 官方推荐模式
        """
        attempt = 0
        interval = self.config.reconnect.interval

        while self._running:
            try:
                # 使用已创建的 Client（在 connect() 中创建）
                # async with 会连接，退出时会自动断开
                async with self._client:
                    self._connected = True

                    # 重置重连计数
                    attempt = 0
                    interval = self.config.reconnect.interval

                    # 恢复订阅（重连后需要）
                    await self._restore_subscriptions()

                    # 启动消息处理任务
                    self._message_task = asyncio.create_task(
                        self._message_loop(), name="mqtt_messages"
                    )

                    # 等待消息循环结束（连接断开）
                    await self._message_task

            except aiomqtt.MqttError as e:
                self._connected = False
                if isinstance(e, aiomqtt.MqttCodeError) and e.rc.value == 0x8E:
                    logger.error(f"会话冲突（被接管）: {e}")
                    break
                logger.warning(f"MQTT 连接断开: {e}")
                if (
                    self.config.reconnect.max_attempts > 0
                    and attempt >= self.config.reconnect.max_attempts
                ):
                    logger.error("达到最大重连次数，停止重连")
                    break
                attempt += 1
                interval = min(
                    interval * self.config.reconnect.backoff_multiplier,
                    self.config.reconnect.max_interval,
                )
                logger.info(f"{interval:.1f}s 后重连（第 {attempt} 次）...")
                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                logger.info("重连任务已取消")
                break

            except Exception as e:
                logger.exception(f"重连循环异常: {e}")
                await asyncio.sleep(interval)

    async def _message_loop(self):
        """消息接收循环

        使用 async for 迭代消息，直接并发处理

        异常处理：
        - asyncio.CancelledError：任务被取消，退出循环
        - aiomqtt.MqttError：连接断开/协议错误，重新抛出触发外层重连
        """
        if not self._client:
            return

        try:
            async for message in self._client.messages:
                asyncio.create_task(self._handle_message(message))
        except asyncio.CancelledError:
            logger.info("消息处理任务已取消")
            raise
        except aiomqtt.MqttError as e:
            logger.warning(f"消息循环 MQTT 错误: {e}")
            raise
        except Exception as e:
            logger.exception(f"消息循环异常: {e}")

    async def subscribe(self, pattern: str, handler: MessageHandler):
        """订阅原始消息 (bytes)

        Args:
            pattern: MQTT topic pattern (支持通配符 +/#)
            handler: 回调函数
                - 签名: async def handler(topic: str, payload: bytes, properties)
                - topic: 实际收到消息的 topic
                - payload: 原始 bytes 数据 (未解码)
                - properties: MQTT 5.0 Properties 对象

        并发行为:
            - 同一 pattern 的多个 handlers 按注册顺序**顺序调用**（非并发）
            - 如需并发处理，请在 handler 内部使用 asyncio.create_task()

        注意:
            - 订阅在重连时自动恢复
            - 订阅失败会抛出异常，调用方应处理
        """
        if pattern not in self._raw_handlers:
            self._raw_handlers[pattern] = []
            self._raw_matcher[pattern] = self._raw_handlers[pattern]

            # 等待 broker 订阅完成，异常会正确传播
            if self._client:
                await self._client.subscribe(pattern)

        self._raw_handlers[pattern].append(handler)

        logger.debug(f"订阅已注册 - pattern: {pattern}")

    async def _restore_subscriptions(self):
        """恢复所有订阅（重连后调用）

        注意：
        - 当 clean_start=False 时，Broker 会保留订阅，但客户端仍需重新订阅以确保一致性
        - 当 clean_start=True 或 MQTT_CLEAN_START_FIRST_ONLY 时，必须重新订阅
        """
        if not self._raw_handlers:
            return

        topics = list(self._raw_handlers.keys())
        logger.info(f"恢复 {len(topics)} 个订阅...")

        for topic in topics:
            try:
                await self._client.subscribe(topic)
            except Exception as e:
                logger.error(f"恢复订阅失败 - topic: {topic}, error: {e}")

        logger.success("订阅恢复完成")

    async def unsubscribe(self, pattern: str):
        """取消订阅

        Args:
            pattern: MQTT topic pattern

        注意:
            - 若当前已连接，会向 broker 发送 MQTT UNSUBSCRIBE
            - 无论是否连接，都会清理本地 matcher/handlers
            - 取消订阅失败会抛出异常，调用方应处理
        """
        if pattern not in self._raw_handlers:
            logger.debug(f"取消订阅失败：pattern 不存在 - {pattern}")
            return

        del self._raw_handlers[pattern]
        del self._raw_matcher[pattern]
        logger.debug(f"取消订阅 - pattern: {pattern}")

        if self._client and self.is_connected:
            await self._client.unsubscribe(pattern)
            logger.debug(f"已向 broker 发送 UNSUBSCRIBE - pattern: {pattern}")

    async def _raw_unsubscribe(self, pattern: str):
        """底层取消订阅（只发送 UNSUBSCRIBE，不清理本地状态）

        Args:
            pattern: MQTT topic pattern

        注意:
            - 仅向 broker 发送 UNSUBSCRIBE
            - 不清理本地 _raw_handlers / _raw_matcher
            - 供 EventChannelManager 等有独立 handler 管理的上层模块使用
        """
        if self._client and self.is_connected:
            await self._client.unsubscribe(pattern)
            logger.debug(f"已向 broker 发送 UNSUBSCRIBE（raw） - pattern: {pattern}")

    async def _handle_message(self, message: aiomqtt.Message):
        """处理单条消息（传输层，只处理 bytes）

        核心改变：
        1. 不再解析 JSON/协议
        2. 将 payload (bytes) 和 properties 分发给 raw handlers
        3. 不再区分 RPC/Event（让上层处理）

        Args:
            message: aiomqtt.Message 对象
        """
        topic_str = str(message.topic)
        payload = message.payload  # bytes 类型
        properties = message.properties  # MQTT 5.0 Properties

        # === 唯一职责：将 bytes + properties 分发给所有匹配的 handlers ===
        # MQTTMatcher.iter_match 返回值列表，不是 (pattern, handlers) 元组
        for handlers in self._raw_matcher.iter_match(topic_str):
            for handler in handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(
                            topic_str, payload, properties
                        )  # 传递 bytes + properties
                    else:
                        handler(topic_str, payload, properties)
                except Exception as e:
                    logger.exception(f"Handler 异常 - topic: {topic_str}, error: {e}")

    async def publish(self, topic: str, payload: bytes, qos: int = 0, properties=None):
        """发布消息

        Args:
            topic: 目标主题
            payload: 消息载荷（bytes）
            qos: QoS 等级（0/1/2）
            properties: MQTT 5.0 Properties 对象

        Raises:
            MQTTXError: 客户端未初始化
            aiomqtt.MqttError: 发布失败
        """
        if not self._client:
            raise MQTTXError("MQTT 客户端未初始化", ErrorCode.NOT_CONNECTED)

        await self._client.publish(topic, payload, qos=qos, properties=properties)

    @property
    def is_connected(self) -> bool:
        """检查连接状态

        Returns:
            True = 已连接，False = 未连接

        注意:
            连接成功后 _connected 设为 True
            连接断开或失败时 _connected 设为 False
        """
        return self._connected
