import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, Optional

import redis
from rq import Queue

from . import utils


Callback = Optional[Callable[..., None]]
SCHEDULE_QUEUE_NAME = "queue_bus_schedule"


@dataclass
class ConnectionOptions:
    host: str = "127.0.0.1"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    namespace: str = utils.defaults()["namespace"]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "host": self.host,
            "port": self.port,
            "db": self.db,
            "password": self.password,
            "namespace": self.namespace,
        }


class Bus:
    """Publishes events and manages queue-bus subscriptions using Redis."""

    def __init__(self, connection: Dict[str, Any], jobs: Optional[Dict[str, Callable]] = None):
        self.options: Dict[str, Any] = utils.defaults()
        self.options.update(
            {
                "incoming_queue": connection.get("incoming_queue", self.options["incoming_queue"]),
                "bus_class_key": connection.get("bus_class_key", self.options["bus_class_key"]),
                "app_prefix": connection.get("app_prefix", self.options["app_prefix"]),
                "subscription_set": connection.get("subscription_set", self.options["subscription_set"]),
            }
        )
        self.connection = ConnectionOptions(
            host=connection.get("host", ConnectionOptions.host),
            port=connection.get("port", ConnectionOptions.port),
            db=connection.get("db", connection.get("database", ConnectionOptions.db)),
            password=connection.get("password"),
            namespace=connection.get("namespace", ConnectionOptions.namespace),
        )
        self.jobs = jobs or {}
        self.redis: Optional[redis.Redis] = None
        self._rq_queue: Optional[Queue] = None

    def connect(self) -> None:
        self.redis = redis.Redis(
            host=self.connection.host,
            port=self.connection.port,
            db=self.connection.db,
            password=self.connection.password,
            decode_responses=True,
        )

    # RQ ---------------------------------------------------------------
    def _rq(self) -> Queue:
        assert self.redis, "Redis connection not established. Call connect()."
        if self._rq_queue is None:
            self._rq_queue = Queue(name=SCHEDULE_QUEUE_NAME, connection=self.redis)
        return self._rq_queue

    # Redis helpers -----------------------------------------------------
    def _ns(self, suffix: str) -> str:
        return f"{self.connection.namespace}{suffix}"

    def _queue_key(self, queue_name: str) -> str:
        return f"{self.connection.namespace}:queue:{queue_name}"

    # Subscription helpers ---------------------------------------------
    def subscriptions(self, callback: Callback = None):
        assert self.redis, "Redis connection not established. Call connect()."
        subscriptions: Dict[str, Dict[str, Any]] = {}
        count = 0

        apps = self.redis.smembers(self._ns(self.options["subscription_set"]))
        if not apps:
            if callback:
                callback(None, subscriptions, count)
            return subscriptions

        for app in apps:
            raw = self.redis.hgetall(self._ns(self.options["app_prefix"] + app))
            if not raw:
                continue
            for key, val in raw.items():
                if subscriptions.get(app) is None:
                    subscriptions[app] = {}
                subscriptions[app][key] = json.loads(val)
                count += 1

        if callback:
            callback(None, subscriptions, count)
        return subscriptions

    def _rubyize_matcher(self, matcher: Dict[str, Any]) -> Dict[str, Any]:
        rubyized: Dict[str, Any] = {}
        for key, value in matcher.items():
            rubyized[key] = utils.to_ruby_regexp(value)
        return rubyized

    def subscribe(self, app_key: str, priority: str, job: str, matcher: Dict[str, Any], callback: Callback = None):
        assert self.redis, "Redis connection not established. Call connect()."
        app_key = utils.normalize(app_key)
        key = utils.hash_key(app_key, priority, job)
        combined_queue_name = f"{app_key}_{priority}"
        subscription = {
            "queue_name": combined_queue_name,
            "key": key,
            "class": job,
            "matcher": self._rubyize_matcher(matcher),
        }
        self.redis.hset(self._ns(self.options["app_prefix"] + app_key), key, json.dumps(subscription))
        self.redis.sadd(self._ns(self.options["subscription_set"]), app_key)
        if callback:
            callback(None, combined_queue_name)
        return combined_queue_name

    def unsubscribe(self, app_key: str, priority: str, job: str, callback: Callback = None):
        assert self.redis, "Redis connection not established. Call connect()."
        app_key = utils.normalize(app_key)
        key = utils.hash_key(app_key, priority, job)
        app_key_key = self._ns(self.options["app_prefix"] + app_key)
        self.redis.hdel(app_key_key, key)
        remaining = self.redis.hkeys(app_key_key)
        if not remaining:
            self.unsubscribe_all(app_key)
        if callback:
            callback()

    def unsubscribe_all(self, app_key: str, callback: Callback = None):
        assert self.redis, "Redis connection not established. Call connect()."
        app_key = utils.normalize(app_key)
        self.redis.srem(self._ns(self.options["subscription_set"]), app_key)
        self.redis.delete(self._ns(self.options["app_prefix"] + app_key))
        if callback:
            callback()

    # Publish -----------------------------------------------------------
    def _enqueue(self, queue_name: str, klass: str, payload: Dict[str, Any]) -> bool:
        assert self.redis, "Redis connection not established. Call connect()."
        job = {"class": klass, "queue": queue_name, "args": [json.dumps(payload)]}
        self.redis.sadd(f"{self.connection.namespace}:queues", queue_name)
        self.redis.rpush(self._queue_key(queue_name), json.dumps(job))
        return True

    def publish(self, event_type: str, args: Dict[str, Any], callback: Callback = None):
        payload = utils.publish_metadata(event_type, args)
        payload["bus_class_proxy"] = "QueueBus::Driver"
        to_run = self._enqueue(self.options["incoming_queue"], self.options["bus_class_key"], payload)
        if callback:
            callback(None, to_run)
        return to_run

    def publish_heartbeat(self, callback: Callback = None):
        payload = utils.publish_metadata("QueueBus::Heartbeat", {})
        payload["bus_class_proxy"] = "QueueBus::Heartbeat"
        to_run = self._enqueue(self.options["incoming_queue"], self.options["bus_class_key"], payload)
        if callback:
            callback(None, to_run)
        return to_run

    def publish_at(self, timestamp_ms: int, event_type: str, args: Dict[str, Any], callback: Callback = None):
        """Schedule a publish at a Unix timestamp in milliseconds using RQ."""
        when = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
        job = self._rq().enqueue_at(when, _scheduled_publish, self._connection_kwargs(), event_type, args or {})
        if callback:
            callback(None, True)
        return job.id

    def publish_in(self, delay_ms: int, event_type: str, args: Dict[str, Any], callback: Callback = None):
        """Schedule a publish in N milliseconds using RQ."""
        when = datetime.now(tz=timezone.utc) + timedelta(milliseconds=delay_ms)
        job = self._rq().enqueue_at(when, _scheduled_publish, self._connection_kwargs(), event_type, args or {})
        if callback:
            callback(None, True)
        return job.id

    def _connection_kwargs(self) -> Dict[str, Any]:
        data = self.connection.to_dict()
        data.update(
            {
                "incoming_queue": self.options["incoming_queue"],
                "bus_class_key": self.options["bus_class_key"],
                "app_prefix": self.options["app_prefix"],
                "subscription_set": self.options["subscription_set"],
            }
        )
        return data


def _scheduled_publish(connection_kwargs: Dict[str, Any], event_type: str, args: Dict[str, Any]):
    """Function run by RQ workers to perform a scheduled publish."""
    bus = Bus(connection=connection_kwargs)
    bus.connect()
    bus.publish(event_type, args or {})
