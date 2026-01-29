# dino-lib

Utilities for RabbitMQ consumer/publisher and Postgres lock patterns.

## Packages
- `dino_rabbitmq_consumer`: Async RabbitMQ consumer and publisher utilities built on aio-pika.
- `dino_lock_patterns`: Pragmatic patterns for Postgres row locks.

## Install
```bash
pip install .
```

## Development
```bash
pip install -e .[test]
```

## Build
```bash
python -m build
```

pip install build twine

rm -rf dist
rm -rf *.egg-info
python -m build

python -m twine upload dist/*

pip install --upgrade dino-temporal-lib-helper