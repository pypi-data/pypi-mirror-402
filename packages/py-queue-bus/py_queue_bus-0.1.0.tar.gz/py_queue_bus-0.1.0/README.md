# py-queue-bus

Python implementation of Queue-Bus semantics compatible with `node-queue-bus` and Ruby `resque-bus`. Uses `redis-py` to publish bus events and a rider worker to fan out events to subscribed queues.

## Install
```bash
pip install py-queue-bus
```

## Basic usage (explicit)

Publish Events (no rider needed in the publishing process):
```python
from py_queue_bus import Bus

connection = {"host": "127.0.0.1", "port": 6379, "db": 0, "namespace": "resque"}
bus = Bus(connection=connection)
bus.connect()
bus.publish("order_created", {"order_id": 1, "total": 10.0})
```

Subscribe Events:
```python
from py_queue_bus import Bus, Rider

connection = {"host": "127.0.0.1", "port": 6379, "db": 0, "namespace": "resque"}
app_key = "example_service"
priority = "default"
queue = f"{app_key}_{priority}"

bus = Bus(connection=connection)
bus.connect()

# Define handlers
def order_created_handler(payload):
    print("order_created_handler received:", payload)

def heartbeat_handler(payload):
    print("heartbeat_handler received:", payload)

jobs = {
    "order_created_job": order_created_handler,
    "heartbeat_job": heartbeat_handler,
}

# Subscribe
# Note: job name can differ from handler function name and event name; it must exist in the jobs dict
bus.subscribe(app_key, priority, "order_created_job", {"bus_event_type": "order_created"})
bus.subscribe(app_key, priority, "heartbeat_job", {"bus_event_type": "heartbeat_minutes"}) # See Heartbeat section below.

rider = Rider(connection=connection, jobs=jobs, queues=[queue], to_drive=True)
rider.connect()
rider.start()  # blocking worker
```

## Scheduling (RQ)
- `publish_at` / `publish_in` enqueue scheduled publishes using RQ. Run a worker:
  ```bash
  rq worker --with-scheduler queue_bus_schedule
  ```
- Example entrypoint: `py-queue-bus/examples/rq_worker.py`.
- Note: Scheduling is Python-native via RQ. Node/Ruby schedulers (resque-scheduler/node-resque) won’t see Python-scheduled jobs; they only see fired jobs after RQ publishes them.

## Heartbeat
- `publish_heartbeat()` emits a `QueueBus::Heartbeat` job; riders emit `heartbeat_minutes` once per minute (with Redis locking) for cron-like tasks.

## Examples
- Subscriber + Rider: `py-queue-bus/examples/subscriber_service.py`
- Publisher: `py-queue-bus/examples/publisher_service.py`
- RQ worker stub: `py-queue-bus/examples/rq_worker.py`
- **Tip:**
  In production, keep handlers in a folder and import the jobs dict into your rider entrypoint, e.g.:
  ```
  app/
    subscribers/
      __init__.py  # exports jobs = {"my_job": handler}
      order_handlers.py
    worker.py      # from subscribers import jobs; Rider(..., jobs=jobs)
  ```

## Tests
- Unit tests (pytest): `pytest py-queue-bus/test`
- Microservice harnesses (manual cross-language checks):
  - Python service scripts: `py-queue-bus/test/python_service`
  - Node service scripts (npm `node-queue-bus`): `py-queue-bus/test/node_service`
  - Payloads include `ts` and explicit logs for debugging.

## Compatibility notes
- Redis schema matches node/resque (queues, subscription hashes/sets).
- Payload metadata matches node/resque-bus, so Node/Ruby workers can consume events published here and vice versa.
