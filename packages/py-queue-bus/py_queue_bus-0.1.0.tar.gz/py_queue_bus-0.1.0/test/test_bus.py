import json

import pytest

from py_queue_bus.bus import Bus


@pytest.fixture()
def bus(fake_redis, default_connection):
    b = Bus(connection=default_connection)
    b.connect()
    return b


def test_subscribe_writes_hash_and_set(bus, fake_redis):
    bus.subscribe("app", "priority", "job", {"bus_event_type": "demo"})
    hash_key = f"{bus.connection.namespace}:bus_app:app"
    set_key = f"{bus.connection.namespace}:bus_apps"

    stored = fake_redis.hgetall(hash_key)
    assert "app_priority_job" in stored
    subscription = json.loads(stored["app_priority_job"])
    assert subscription["queue_name"] == "app_priority"
    assert subscription["class"] == "job"
    assert subscription["matcher"]["bus_event_type"] == "demo"

    assert fake_redis.sismember(set_key, "app")


def test_unsubscribe_removes_entries(bus, fake_redis):
    bus.subscribe("app", "priority", "job", {"bus_event_type": "demo"})
    bus.unsubscribe("app", "priority", "job")
    hash_key = f"{bus.connection.namespace}:bus_app:app"
    set_key = f"{bus.connection.namespace}:bus_apps"
    assert fake_redis.hlen(hash_key) == 0
    assert not fake_redis.sismember(set_key, "app")


def test_publish_enqueues_payload(bus, fake_redis):
    bus.publish("demo_event", {"x": 1})
    queue_key = f"{bus.connection.namespace}:queue:{bus.options['incoming_queue']}"
    items = fake_redis.lrange(queue_key, 0, -1)
    assert len(items) == 1
    job = json.loads(items[0])
    payload = json.loads(job["args"][0])
    assert job["class"] == bus.options["bus_class_key"]
    assert job["queue"] == bus.options["incoming_queue"]
    assert payload["bus_class_proxy"] == "QueueBus::Driver"
    assert payload["bus_event_type"] == "demo_event"
    assert payload["x"] == 1


def test_publish_at_uses_rq_enqueue_at(monkeypatch, bus):
    captured = {}

    class FakeQueue:
        def enqueue_at(self, when, fn, conn_kwargs, event_type, args):
            captured["when"] = when
            captured["fn"] = fn
            captured["conn_kwargs"] = conn_kwargs
            captured["event_type"] = event_type
            captured["args"] = args
            return type("job", (), {"id": "job-id"})

    monkeypatch.setattr(bus, "_rq", lambda: FakeQueue())
    job_id = bus.publish_at(1_500_000_000_000, "demo_event", {"x": 1})
    assert job_id == "job-id"
    assert captured["event_type"] == "demo_event"
    assert captured["args"]["x"] == 1
    assert captured["conn_kwargs"]["incoming_queue"] == bus.options["incoming_queue"]


def test_publish_in_uses_rq_enqueue_at(monkeypatch, bus):
    captured = {}

    class FakeQueue:
        def enqueue_at(self, when, fn, conn_kwargs, event_type, args):
            captured["when"] = when
            captured["event_type"] = event_type
            captured["args"] = args
            return type("job", (), {"id": "job-id"})

    monkeypatch.setattr(bus, "_rq", lambda: FakeQueue())
    job_id = bus.publish_in(1000, "demo_event", {"x": 2})
    assert job_id == "job-id"
    assert captured["event_type"] == "demo_event"
    assert captured["args"]["x"] == 2
