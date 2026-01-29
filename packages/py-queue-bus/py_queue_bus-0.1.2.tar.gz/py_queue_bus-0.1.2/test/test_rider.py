import json
import re
import pytest

from py_queue_bus import utils
from py_queue_bus.bus import Bus
from py_queue_bus.rider import Rider


@pytest.fixture()
def rider(fake_redis, default_connection):
    r = Rider(connection=default_connection, jobs={}, queues=["app_default"], to_drive=True)
    r.connect()
    return r


def test_subscription_match_special_keys(rider):
    subscription = {"matcher": {"foo": "bus_special_value_present"}}
    assert rider._subscription_match({"foo": "bar"}, subscription)
    assert not rider._subscription_match({"foo": ""}, subscription)

    subscription = {"matcher": {"foo": "bus_special_value_nil"}}
    assert rider._subscription_match({}, subscription)
    assert not rider._subscription_match({"foo": "x"}, subscription)


def test_subscription_match_regex(rider):
    ruby_regex = utils.to_ruby_regexp(re.compile(r"^test", re.IGNORECASE))
    subscription = {"matcher": {"foo": ruby_regex}}
    assert rider._subscription_match({"foo": "Test123"}, subscription)
    assert not rider._subscription_match({"foo": "nope"}, subscription)


@pytest.mark.parametrize(
    "matcher,payload,should_match",
    [
        ({"foo": "bus_special_value_present"}, {"foo": "bar"}, True),
        ({"foo": "bus_special_value_present"}, {"foo": ""}, False),
        ({"foo": "bus_special_value_nil"}, {}, True),
        ({"foo": "bus_special_value_nil"}, {"foo": "x"}, False),
        ({"foo": "bus_special_value_value"}, {"foo": "x"}, True),
        ({"foo": "bus_special_value_value"}, {}, False),
        ({"foo": utils.to_ruby_regexp(re.compile(r"^test", re.IGNORECASE))}, {"foo": "Test123"}, True),
        ({"foo": utils.to_ruby_regexp(re.compile(r"^test", re.IGNORECASE))}, {"foo": "nope"}, False),
    ],
)
def test_subscription_match_parametrized(rider, matcher, payload, should_match):
    subscription = {"matcher": matcher}
    assert rider._subscription_match(payload, subscription) == should_match


def test_driver_perform_fans_out(fake_redis, default_connection, monkeypatch):
    # Shared fake via monkeypatch happens in fixture
    bus = Bus(connection=default_connection)
    bus.connect()
    bus.subscribe("app", "default", "job_name", {"bus_event_type": "demo"})

    r = Rider(connection=default_connection, jobs={}, queues=["app_default"], to_drive=True)
    r.connect()

    args = {"bus_event_type": "demo", "foo": "bar"}
    r._driver_perform(args)

    queue_key = f"{bus.connection.namespace}:queue:app_default"
    items = fake_redis.lrange(queue_key, 0, -1)
    assert len(items) == 1
    job = json.loads(items[0])
    payload = json.loads(job["args"][0])
    assert job["class"] == r.options["bus_class_key"]
    assert payload["bus_class_proxy"] == "job_name"
    assert payload["bus_event_type"] == "demo"
    assert payload["foo"] == "bar"


def test_process_job_invokes_handler(fake_redis, default_connection):
    called = {}

    def handler(payload):
        called["payload"] = payload

    r = Rider(connection=default_connection, jobs={"job_name": handler}, queues=["app_default"], to_drive=False)
    r.connect()
    job = {
        "class": "job_name",
        "queue": "app_default",
        "args": [json.dumps({"x": 1})],
    }
    raw = json.dumps(job)
    r._process_job(f"{r.bus.connection.namespace}:queue:app_default", raw)
    assert called["payload"]["x"] == 1
