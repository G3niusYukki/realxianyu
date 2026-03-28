# XianyuFlow Common Library

Shared library for XianyuFlow v10 microservices.

## Installation

```bash
cd services/common
pip install -e .
```

For development:

```bash
pip install -e ".[dev]"
```

## Usage

### Configuration

```python
from xianyuflow_common.config import ServiceConfig

config = ServiceConfig()
print(config.database.dsn)
print(config.redis.host)
```

### Database

```python
from xianyuflow_common.database import Database
from xianyuflow_common.config import DatabaseConfig

config = DatabaseConfig()
db = Database(config)
await db.connect()

async with db.session() as session:
    result = await session.execute(select(SomeModel))

await db.disconnect()
```

### Kafka

```python
from xianyuflow_common.kafka import KafkaClient, TOPICS
from xianyuflow_common.config import KafkaConfig

config = KafkaConfig()
client = KafkaClient(config)
client.connect()

client.publish(TOPICS["chat_messages"], {"message": "hello"})
```

### Logging & Telemetry

```python
from xianyuflow_common.telemetry import get_logger, get_tracer

logger = get_logger("my_service")
logger.info("message", key="value")

tracer = get_tracer("my_service")
with tracer.start_as_current_span("operation") as span:
    span.set_attribute("key", "value")
```

## Modules

- `config` - Pydantic-based configuration management
- `database` - SQLAlchemy 2.0 async database client
- `kafka` - Kafka producer/consumer client
- `models` - Shared Pydantic models
- `telemetry` - Structured logging and OpenTelemetry

## Environment Variables

See `config.py` for all available environment variables. Key prefixes:
- `DATABASE_*` - Database configuration
- `REDIS_*` - Redis configuration
- `KAFKA_*` - Kafka configuration
- `AI_*` - AI service configuration
- `XIANYU_*` - Xianyu API configuration
