# 在线状态追踪模块

import asyncio
import json
import time
from typing import Dict, Optional
from dataclasses import dataclass
from loguru import logger


@dataclass
class PresenceState:
    """在线状态数据结构"""

    status: str  # "online" | "offline"
    timestamp: int  # Unix 时间戳
    client_id: str


class PresenceTracker:
    """在线状态追踪器

    维护 client_id → 在线状态的映射，自动清理过期状态

    示例:
        tracker = PresenceTracker(state_ttl=300)
        tracker.update_state("device_1", "online", int(time.time()))
        is_online = tracker.is_online("device_1")
    """

    def __init__(self, state_ttl: int = 300):
        """初始化在线状态追踪器

        Args:
            state_ttl: 状态过期时间（秒），默认 300 秒
        """
        self._states: Dict[str, PresenceState] = {}
        self._state_ttl = state_ttl
        self._lock = asyncio.Lock()

    def update_state(self, client_id: str, status: str, timestamp: int) -> None:
        """更新客户端在线状态

        Args:
            client_id: 客户端 ID
            status: 状态 ("online" | "offline")
            timestamp: 时间戳
        """
        current_time = int(time.time())
        if current_time - timestamp > self._state_ttl:
            return

        self._states[client_id] = PresenceState(
            status=status, timestamp=timestamp, client_id=client_id
        )
        logger.debug(f"更新在线状态: {client_id} -> {status}")

    def is_online(self, client_id: str) -> bool:
        """检查客户端是否在线

        Args:
            client_id: 客户端 ID

        Returns:
            True 如果在线且未过期，否则 False
        """
        state = self._states.get(client_id)
        if not state:
            return False

        # 检查状态是否过期
        current_time = int(time.time())
        if current_time - state.timestamp > self._state_ttl:
            logger.debug(f"状态已过期: {client_id}")
            return False

        return state.status == "online"

    def get_state(self, client_id: str) -> Optional[PresenceState]:
        """获取客户端状态

        Args:
            client_id: 客户端 ID

        Returns:
            PresenceState 或 None
        """
        return self._states.get(client_id)

    def cleanup_expired(self) -> int:
        """清理过期状态

        Returns:
            清理的状态数量
        """
        current_time = int(time.time())
        expired_clients = [
            client_id
            for client_id, state in self._states.items()
            if current_time - state.timestamp > self._state_ttl
        ]

        for client_id in expired_clients:
            del self._states[client_id]
            logger.debug(f"清理过期状态: {client_id}")

        return len(expired_clients)

    def parse_presence_message(self, payload: bytes) -> Optional[tuple[str, int]]:
        """解析在线状态消息

        Args:
            payload: MQTT 消息 payload

        Returns:
            (status, timestamp) 或 None
        """
        try:
            data = json.loads(payload.decode())
            status = data.get("status")
            timestamp = data.get("timestamp")

            if not status or not timestamp:
                logger.warning(f"在线状态消息缺少必需字段: {data}")
                return None

            return (status, timestamp)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.warning(f"解析在线状态消息失败: {e}")
            return None

    def get_all_online(self) -> list[str]:
        """获取所有在线客户端

        Returns:
            在线客户端 ID 列表
        """
        current_time = int(time.time())
        return [
            client_id
            for client_id, state in self._states.items()
            if state.status == "online"
            and current_time - state.timestamp <= self._state_ttl
        ]

    def clear(self) -> None:
        """清空所有状态"""
        self._states.clear()
        logger.debug("清空所有在线状态")
