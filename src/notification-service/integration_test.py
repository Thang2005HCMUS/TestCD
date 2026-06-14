# src/notification-service/integration_test.py
import pytest
import os
import asyncio
from aiokafka import AIOKafkaConsumer

# Kết nối tới Kafka trong K8s
KAFKA_SERVER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka-service:9092")

@pytest.mark.asyncio
async def test_kafka_event_subscription():
    """
    Integration test kiểm tra khả năng lắng nghe event từ Kafka
    """
    consumer = AIOKafkaConsumer(
        "order-events",
        bootstrap_servers=KAFKA_SERVER,
        group_id="test-group",
        auto_offset_reset='earliest'
    )
    await consumer.start()
    try:
        # Kiểm tra xem có nhận được message trong vòng 5s không
        msg = await asyncio.wait_for(consumer.getone(), timeout=5.0)
        assert msg is not None
    finally:
        await consumer.stop()