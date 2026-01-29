# MQTT RPC 模块 - 基于 MQTT 5.0 原生字段

import asyncio
import uuid
from typing import Any, Callable
from loguru import logger

from .client import MQTTClient
from .exceptions import (
    RPCTimeoutError,
    RPCRemoteError,
    MQTTXError,
    ErrorCode,
    MessageError,
)
from .protocol import (
    RPCRequest,
    RPCResponse,
    encode_request,
    encode_response,
    parse_message,
)


class RPCManager:
    """RPC 调用管理器（基于 MQTT 5.0 原生字段）

    使用 ResponseTopic/CorrelationData 替代 User Properties，符合 MQTT 5.0 标准。
    """

    def __init__(
        self,
        client: MQTTClient,
    ):
        """初始化 RPC 管理器

        Args:
            client: MQTTClient 实例
        """
        self._client = client
        self._my_topic = f"rpc/r/{client.config.client_id}"

        # RPC 状态
        self._pending_calls: dict[str, asyncio.Future] = {}
        self._handlers: dict[str, Callable] = {}

        # 注册内部 ping 方法
        self._handlers["__ping__"] = self._ping_handler
        # 创建即订阅，加入 RPC 网络
        asyncio.create_task(self._subscribe())

    @property
    def my_topic(self) -> str:
        """获取本节点的响应主题"""
        return self._my_topic

    async def _subscribe(self):
        """订阅响应主题"""
        """执行订阅"""

        async def handle_bytes(topic: str, payload: bytes, properties=None):
            """bytes → RPC message → handle"""
            try:
                message = parse_message(payload, properties)

                if isinstance(message, RPCRequest):
                    await self._handle_request(topic, message)
                elif isinstance(message, RPCResponse):
                    await self._handle_response(topic, message)
            except MessageError as e:
                logger.debug(f"非 RPC 消息 - topic: {topic}, reason: {e}")
            except Exception as e:
                logger.exception(f"RPC 消息处理失败: {e}")

        await self._client.subscribe(self._my_topic, handle_bytes)

    def register(self, method_name: str):
        """装饰器：注册本地 RPC 方法供远程调用"""

        def decorator(func: Callable):
            self._handlers[method_name] = func
            return func

        return decorator

    def unregister(self, method_name: str):
        """注销 RPC 方法"""
        if method_name in self._handlers:
            del self._handlers[method_name]
            logger.info(f"RPC 方法已注销: {method_name}")

    def handle_rpc_bytes(self, topic: str, payload: bytes, properties):
        """处理 RPC 消息（由 MQTTClient 调用）"""
        try:
            message = parse_message(payload, properties)
        except MessageError:
            return

        if isinstance(message, RPCRequest):
            asyncio.create_task(
                self._handle_request(topic, message),
                name=f"rpc_req_{message.request_id[:8]}",
            )
        elif isinstance(message, RPCResponse):
            asyncio.create_task(
                self._handle_response(topic, message),
                name=f"rpc_resp_{message.request_id[:8]}",
            )

    async def call(
        self,
        topic: str,
        method: str,
        params: Any = None,
        timeout: float = 30.0,
    ) -> Any:
        """远程调用 RPC 方法"""
        if not self._client.is_connected:
            raise MQTTXError("MQTT 客户端未连接", ErrorCode.NOT_CONNECTED)

        # 生成请求
        request_id = str(uuid.uuid4())

        request = RPCRequest(
            request_id=request_id,
            method=method,
            params=params,
            reply_to=self._my_topic,
            caller_id=self._client.config.client_id,
        )

        # 创建 Future（用于 RPC 响应）
        future = asyncio.get_event_loop().create_future()
        self._pending_calls[request_id] = future

        # 发送请求（使用 MQTT 5.0 原生字段）
        payload, properties = encode_request(request)
        await self._client.publish(topic, payload, qos=1, properties=properties)
        logger.debug(f"RPC 请求已发送 - method: {method}, request_id: {request_id[:8]}")

        try:
            # 等待响应
            result = await asyncio.wait_for(future, timeout=timeout)
            logger.debug(f"RPC 调用成功 - method: {method}")
            return result
        except asyncio.TimeoutError:
            logger.error(f"RPC 超时 - method: {method}, timeout: {timeout}s")
            raise RPCTimeoutError(f"RPC 调用超时: {method}")
        finally:
            # 清理 Future
            self._pending_calls.pop(request_id, None)

    async def _handle_response(self, topic: str, message: RPCResponse):
        """处理 RPC 响应"""
        future = self._pending_calls.get(message.request_id)

        if not future or future.done():
            logger.warning(f"收到未知/过期响应 - request_id: {message.request_id[:8]}")
            return

        if message.error:
            future.set_exception(RPCRemoteError(message.error))
        else:
            future.set_result(message.result)

    async def _handle_request(self, topic: str, message: RPCRequest):
        """处理 RPC 请求"""
        # 查找处理器
        handler = self._handlers.get(message.method)

        if not handler:
            logger.warning(f"方法未找到 - method: {message.method}")
            response = RPCResponse(
                request_id=message.request_id, error=f"方法未找到: {message.method}"
            )
        else:
            # 执行方法
            response = await self._execute_handler(handler, message)

        # 发送响应
        await self._send_response(message.reply_to, response)

    async def _execute_handler(
        self, handler: Callable, message: RPCRequest
    ) -> RPCResponse:
        """执行 RPC 方法处理器"""
        try:
            # 自动处理同步/异步函数
            if asyncio.iscoroutinefunction(handler):
                result = await handler(message.params)
            else:
                result = handler(message.params)

            logger.debug(f"RPC 方法执行成功 - method: {message.method}")
            return RPCResponse(request_id=message.request_id, result=result)

        except asyncio.CancelledError:
            # 任务被取消，向上传播
            raise

        except Exception as e:
            logger.exception(f"RPC 方法执行失败 - method: {message.method}")
            return RPCResponse(request_id=message.request_id, error=str(e))

    async def _send_response(self, topic: str, response: RPCResponse):
        """发送 RPC 响应"""
        payload, properties = encode_response(response)
        await self._client.publish(topic, payload, qos=1, properties=properties)

    async def ping(self, topic: str, count: int = 3, timeout: float = 3.0) -> bool:
        """检测 RPC 对方是否在线（并发 ping 三次）"""

        async def _single_ping():
            try:
                result = await self.call(
                    topic, "__ping__", params=None, timeout=timeout
                )
                return result is True
            except (RPCTimeoutError, RPCRemoteError, MQTTXError):
                return False

        results = await asyncio.gather(*(_single_ping() for _ in range(count)))
        return any(results)

    def _ping_handler(self, params: Any = None) -> bool:
        """内部 ping 处理器，返回 True 表示在线"""
        return True
