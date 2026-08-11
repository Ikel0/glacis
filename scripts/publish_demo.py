from __future__ import annotations

import json
import os
from pathlib import Path

from kafka import KafkaProducer


def main() -> None:
    producer = KafkaProducer(bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "redpanda:9092"), value_serializer=lambda value: json.dumps(value).encode())
    source = Path(__file__).resolve().parents[1] / "data" / "demo_readings.jsonl"
    for line in source.read_text().splitlines():
        producer.send(os.getenv("KAFKA_TOPIC", "coldchain.reading.v1"), json.loads(line))
    producer.flush()
    print("Published Glacis demo readings.")


if __name__ == "__main__":
    main()
