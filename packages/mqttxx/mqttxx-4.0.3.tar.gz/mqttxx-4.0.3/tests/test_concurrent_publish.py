"""并发发布测试 - 真实 MQTT Broker 环境下每秒发送 100 条消息

运行要求:
1. 需要运行中的 MQTT Broker (配置见 conftest.py)
2. 安装依赖: pip install pytest pytest-asyncio
3. 运行: pytest tests/test_concurrent_publish.py -v

测试场景:
- 单个客户端每秒并发发布 100 条消息
- 每个 payload 包含时间戳和序号
- 验证消息发送成功
"""
import asyncio
import time
import pytest
from loguru import logger


@pytest.mark.asyncio
async def test_concurrent_publish_100_messages_per_second(connected_client):
    """测试每秒并发发送 100 条消息

    策略:
    1. 使用 asyncio.gather 并发发送所有消息
    2. 每个 payload 包含时间戳和序号
    3. 测量总耗时，确保在 1 秒左右完成
    4. 所有消息都应发送成功
    """
    topic = "test/concurrent/publish"
    message_count = 100

    # 准备 100 条消息
    base_time = time.time()
    payloads = [f"msg_{i}_{base_time}".encode() for i in range(message_count)]

    start_time = time.time()

    # 并发发送所有消息
    tasks = [
        connected_client.publish(topic, payload, qos=0) for payload in payloads
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    end_time = time.time()
    elapsed = end_time - start_time

    # 统计结果
    success_count = sum(1 for r in results if r is None)
    error_count = sum(1 for r in results if isinstance(r, Exception))

    logger.info(
        f"发送完成 - 成功: {success_count}/{message_count}, "
        f"失败: {error_count}, 耗时: {elapsed:.3f}s"
    )

    assert success_count == message_count, f"预期 {message_count} 条成功，实际 {success_count} 条"
    assert error_count == 0, f"存在失败消息: {error_count} 条"
    assert elapsed < 2.0, f"性能不达标: {elapsed:.3f}s > 2.0s"

    logger.success(f"✅ 通过 - {message_count} 条消息耗时 {elapsed:.3f}s")


@pytest.mark.asyncio
async def test_sequential_publish_100_messages(connected_client):
    """对比测试：顺序发送 100 条消息

    用于对比并发和顺序发送的性能差异
    """
    topic = "test/sequential/publish"
    message_count = 100

    start_time = time.time()

    for i in range(message_count):
        payload = f"seq_{i}_{start_time}".encode()
        await connected_client.publish(topic, payload, qos=0)

    end_time = time.time()
    elapsed = end_time - start_time

    logger.info(f"顺序发送完成 - {message_count} 条消息耗时 {elapsed:.3f}s")
    assert elapsed < 5.0, f"顺序发送过慢: {elapsed:.3f}s"


@pytest.mark.asyncio
async def test_concurrent_publish_with_qos1(connected_client):
    """测试 QoS 1 的并发发布

    QoS 1 需要等待 PUBACK，会比 QoS 0 慢
    """
    topic = "test/concurrent/qos1"
    message_count = 100

    start_time = time.time()

    tasks = [
        connected_client.publish(topic, f"qos1_{i}".encode(), qos=1)
        for i in range(message_count)
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    end_time = time.time()
    elapsed = end_time - start_time

    success_count = sum(1 for r in results if r is None)
    error_count = sum(1 for r in results if isinstance(r, Exception))

    logger.info(
        f"QoS 1 发送完成 - 成功: {success_count}/{message_count}, "
        f"失败: {error_count}, 耗时: {elapsed:.3f}s"
    )

    assert success_count == message_count
    assert error_count == 0
    assert elapsed < 5.0, f"QoS 1 发送过慢: {elapsed:.3f}s"


@pytest.mark.asyncio
async def test_concurrent_publish_500_messages(connected_client):
    """压力测试：并发发送 500 条消息

    验证更高并发下的稳定性
    """
    topic = "test/concurrent/stress"
    message_count = 500

    start_time = time.time()

    tasks = [
        connected_client.publish(topic, f"stress_{i}".encode(), qos=0)
        for i in range(message_count)
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    end_time = time.time()
    elapsed = end_time - start_time

    success_count = sum(1 for r in results if r is None)
    error_count = sum(1 for r in results if isinstance(r, Exception))

    logger.info(
        f"压力测试完成 - 成功: {success_count}/{message_count}, "
        f"失败: {error_count}, 耗时: {elapsed:.3f}s, "
        f"吞吐: {message_count/elapsed:.0f} msg/s"
    )

    assert success_count == message_count
    assert error_count == 0
