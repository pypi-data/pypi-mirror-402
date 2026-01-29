"""Minimal RQ scheduler worker for queue_bus_schedule."""
from typing import Any, Dict

import redis
from redis.connection import parse_url
from rq import Worker

from .bus import SCHEDULE_QUEUE_NAME


def _make_redis(redis_config: dict) -> redis.Redis:
    """Build a Redis client for the scheduler, forcing bytes responses."""
    kwargs: Dict[str, Any]
    if redis_config.get("url"):
        kwargs = parse_url(redis_config["url"])
    else:
        kwargs = {
            "host": redis_config.get("host", "127.0.0.1"),
            "port": redis_config.get("port", 6379),
            "db": redis_config.get("db") or redis_config.get("database") or 0,
            "password": redis_config.get("password"),
        }
    defaults = {
        "socket_keepalive": True,
        "health_check_interval": 30,
        "socket_connect_timeout": 10,
        "retry_on_timeout": True,
    }
    for k, v in defaults.items():
        kwargs.setdefault(k, v)
    kwargs.update(redis_config.get("redis_kwargs", {}))
    kwargs["decode_responses"] = False  # keep bytes for RQ internals
    return redis.Redis(**kwargs)


def run_scheduler_worker(redis_config: dict, with_scheduler: bool = True):
    """Run an RQ worker for queue_bus_schedule with optional scheduler loop."""
    worker = Worker([SCHEDULE_QUEUE_NAME], connection=_make_redis(redis_config))
    worker.work(with_scheduler=with_scheduler)
