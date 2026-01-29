import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, Optional

import redis
from redis.connection import parse_url
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
    url: Optional[str] = None
    namespace: str = utils.defaults()["namespace"]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "host": self.host,
            "port": self.port,
            "db": self.db,
            "password": self.password,
            "url": self.url,
            "namespace": self.namespace,
        }


class Bus:
    """Publishes events and manages queue-bus subscriptions using Redis."""

    def __init__(self, connection: Dict[str, Any], jobs: Optional[Dict[str, Callable]] = None):
        """
        Create a Bus with Redis connection settings and optional job handlers.

        Args:
            connection: Redis settings (host/port/db/password/namespace or url, optional redis_kwargs).
            jobs: Optional mapping of job name to handler (callable or object with perform()).
        """
        self.options: Dict[str, Any] = utils.defaults()
        self.options.update(
            {
                "incoming_queue": connection.get("incoming_queue") or self.options["incoming_queue"],
                "bus_class_key": connection.get("bus_class_key") or self.options["bus_class_key"],
                "app_prefix": connection.get("app_prefix") or self.options["app_prefix"],
                "subscription_set": connection.get("subscription_set") or self.options["subscription_set"],
            }
        )
        self.connection = ConnectionOptions(
            host=connection.get("host") or ConnectionOptions.host,
            port=connection.get("port") or ConnectionOptions.port,
            db=connection.get("db") or ConnectionOptions.db,
            namespace=connection.get("namespace") or ConnectionOptions.namespace,
            password=connection.get("password") or ConnectionOptions.password,
            url=connection.get("url") or ConnectionOptions.url,
        )
        self.redis_kwargs = connection.get("redis_kwargs", {})
        self.jobs = jobs or {}
        self.redis: Optional[redis.Redis] = None
        self._rq_queue: Optional[Queue] = None

    def connect(self) -> None:
        """Establish a Redis client using host/port or URL with optional overrides."""
        kwargs: Dict[str, Any]
        if self.connection.url:
            kwargs = parse_url(self.connection.url)
        else:
            kwargs = {
                "host": self.connection.host,
                "port": self.connection.port,
                "db": self.connection.db,
                "password": self.connection.password,
            }
        defaults = {
            "decode_responses": True,
            "socket_keepalive": True,
            "health_check_interval": 30,
            "socket_connect_timeout": 10,
            "retry_on_timeout": True,
        }
        for key, val in defaults.items():
            kwargs.setdefault(key, val)
        kwargs.update(self.redis_kwargs)
        self.redis = redis.Redis(**kwargs)

    # RQ ---------------------------------------------------------------
    def _rq(self) -> Queue:
        """Lazy-init the RQ queue used for scheduled publishes."""
        assert self.redis, "Redis connection not established. Call connect()."
        if self._rq_queue is None:
            self._rq_queue = Queue(name=SCHEDULE_QUEUE_NAME, connection=self.redis)
        return self._rq_queue

    # Redis helpers -----------------------------------------------------
    def _ns(self, suffix: str) -> str:
        """Apply the configured namespace to a Redis key suffix."""
        return f"{self.connection.namespace}{suffix}"

    def _queue_key(self, queue_name: str) -> str:
        """Namespace a queue key."""
        return f"{self.connection.namespace}:queue:{queue_name}"

    # Subscription helpers ---------------------------------------------
    def subscriptions(self, callback: Callback = None):
        """Return all subscriptions grouped by app_key."""
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
        """
        Register a subscription for an app/priority/job with a matcher.

        Args:
            app_key: Application key (normalized).
            priority: Queue priority (e.g., "default").
            job: Job name (must exist in the rider's jobs dict).
            matcher: Matcher dict (e.g., {"bus_event_type": "order_created"}).
            callback: Optional callback invoked after subscription is stored.
        """
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
        """Remove a specific subscription."""
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
        """Remove all subscriptions for an app."""
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
        """Publish an event immediately to the incoming queue."""
        payload = utils.publish_metadata(event_type, args)
        payload["bus_class_proxy"] = "QueueBus::Driver"
        to_run = self._enqueue(self.options["incoming_queue"], self.options["bus_class_key"], payload)
        if callback:
            callback(None, to_run)
        return to_run

    def publish_heartbeat(self, callback: Callback = None):
        """Publish a heartbeat event immediately."""
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
        base = {
            "namespace": self.connection.namespace,
            "incoming_queue": self.options["incoming_queue"],
            "bus_class_key": self.options["bus_class_key"],
            "app_prefix": self.options["app_prefix"],
            "subscription_set": self.options["subscription_set"],
        }
        if self.connection.url:
            base["url"] = self.connection.url
        else:
            base.update(
                {
                    "host": self.connection.host,
                    "port": self.connection.port,
                    "db": self.connection.db,
                    "password": self.connection.password,
                }
            )
        return base


def _scheduled_publish(connection_kwargs: Dict[str, Any], event_type: str, args: Dict[str, Any]):
    """Function run by RQ workers to perform a scheduled publish."""
    bus = Bus(connection=connection_kwargs)
    bus.connect()
    bus.publish(event_type, args or {})
