"""Minimal Kafka worker used by the Docker exercise."""

from __future__ import annotations

import json
import os
import time
from urllib.request import Request, urlopen

from kafka import KafkaConsumer, KafkaProducer

from .contract import ContractError, validate


def post(reading: dict) -> None:
    base_url = os.getenv("GLACIS_API_URL", "http://localhost:8090")
    request = Request(f"{base_url}/api/readings", data=json.dumps(reading).encode(), headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=8):
        pass


def main() -> None:
    bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    topic = os.getenv("KAFKA_TOPIC", "coldchain.reading.v1")
    invalid_topic = os.getenv("KAFKA_INVALID_TOPIC", "coldchain.invalid.v1")
    while True:
        try:
            consumer = KafkaConsumer(topic, bootstrap_servers=bootstrap, group_id="glacis-watch", auto_offset_reset="earliest", value_deserializer=lambda value: json.loads(value.decode()))
            producer = KafkaProducer(bootstrap_servers=bootstrap, value_serializer=lambda value: json.dumps(value).encode())
            for message in consumer:
                try:
                    post(validate(message.value))
                except ContractError as exc:
                    producer.send(invalid_topic, {"reading": message.value, "reason": str(exc)})
                except Exception as exc:
                    print(f"retrying after delivery failure: {exc}")
                    break
        except Exception as exc:
            print(f"waiting for Kafka: {exc}")
        time.sleep(4)


if __name__ == "__main__":
    main()
