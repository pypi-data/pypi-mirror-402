import json
import logging
import threading
import time
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

import redis

from .bus import Bus
from . import utils


JobCallable = Callable[[Dict[str, Any]], Any]
logger = logging.getLogger(__name__)


class Rider:
    """Queue-Bus worker that drives incoming events to subscribed queues."""

    def __init__(
        self,
        connection: Dict[str, Any],
        jobs: Optional[Dict[str, JobCallable]] = None,
        queues: Optional[List[str]] = None,
        timeout: int = 5,
        to_drive: Optional[bool] = None,
    ):
        self.timeout = timeout
        self.bus = Bus(connection=connection, jobs=jobs)
        self.redis: Optional[redis.Redis] = None
        self.jobs: Dict[str, JobCallable] = jobs or {}
        default_to_drive = utils.defaults()["to_drive"]
        self.to_drive = connection.get("to_drive", default_to_drive) if to_drive is None else to_drive
        self.queue_names: List[str] = queues[:] if queues else []
        self.options = self.bus.options
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def connect(self) -> None:
        self.bus.connect()
        self.redis = self.bus.redis

        # Include incoming queue when driving
        if self.to_drive and self.options["incoming_queue"] not in self.queue_names:
            self.queue_names.append(self.options["incoming_queue"])
        # Deduplicate while preserving order
        seen = set()
        deduped: List[str] = []
        for q in self.queue_names:
            if q not in seen:
                seen.add(q)
                deduped.append(q)
        self.queue_names = deduped

    def start(self, blocking: bool = True) -> None:
        assert self.redis, "Redis connection not established. Call connect()."
        self._running = True
        if blocking:
            self._work_loop()
        else:
            self.start_in_thread()

    def start_in_thread(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._work_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=1)

    # Processing --------------------------------------------------------
    def _work_loop(self) -> None:
        queue_keys = [self.bus._queue_key(q) for q in self.queue_names]
        if not queue_keys:
            raise ValueError("No queues configured for rider.")
        while self._running:
            result = self.redis.blpop(queue_keys, timeout=self.timeout)
            if not result:
                continue
            queue_key, raw_job = result
            try:
                self._process_job(queue_key, raw_job)
            except json.JSONDecodeError:
                logger.exception("Failed to decode job JSON from %s: %s", queue_key, raw_job)
            except Exception:
                logger.exception("Unhandled error processing job from %s: %s", queue_key, raw_job)

    def _process_job(self, queue_key: str, raw_job: str) -> None:
        job = json.loads(raw_job)
        klass = job.get("class")
        args_list = job.get("args", [])
        payload = json.loads(args_list[0]) if args_list else {}

        if klass == self.options["bus_class_key"]:
            self._perform_bus_job(payload)
        else:
            handler = self.jobs.get(klass)
            if handler:
                if callable(handler):
                    handler(payload)
                elif hasattr(handler, "perform"):
                    handler.perform(payload)

    def _perform_bus_job(self, payload: Dict[str, Any]) -> None:
        proxy = payload.get("bus_class_proxy")
        if proxy == "QueueBus::Driver":
            self._driver_perform(payload)
        elif proxy == "QueueBus::Publisher":
            # scheduled jobs would land here later
            self.bus.publish(payload.get("bus_event_type"), payload, callback=None)
        elif proxy == "QueueBus::Heartbeat":
            self._heartbeat_perform()
        else:
            handler = self.jobs.get(proxy)
            if handler:
                if callable(handler):
                    handler(payload)
                elif hasattr(handler, "perform"):
                    handler.perform(payload)

    # Driver ------------------------------------------------------------
    def _driver_perform(self, args: Dict[str, Any]) -> None:
        subscriptions = self.bus.subscriptions()
        for app, subs in subscriptions.items():
            for _, subscription in subs.items():
                if self._subscription_match(args, subscription):
                    payload = self._driver_metadata(
                        args,
                        subscription["queue_name"],
                        app,
                        subscription["key"],
                        subscription["class"],
                        args.get("bus_event_type"),
                    )
                    payload["bus_class_proxy"] = subscription["class"]
                    self.bus._enqueue(subscription["queue_name"], self.options["bus_class_key"], payload)

    def _driver_metadata(
        self,
        args: Dict[str, Any],
        bus_rider_queue: str,
        bus_rider_app_key: str,
        bus_rider_sub_key: str,
        bus_rider_class_name: str,
        bus_event_type: Optional[str],
    ) -> Dict[str, Any]:
        payload = {
            "bus_driven_at": utils.timestamp(),
            "bus_rider_queue": bus_rider_queue,
            "bus_rider_app_key": bus_rider_app_key,
            "bus_rider_sub_key": bus_rider_sub_key,
            "bus_rider_class_name": bus_rider_class_name,
            "bus_event_type": bus_event_type,
        }
        payload.update(args or {})
        return payload

    def _subscription_match(self, args: Dict[str, Any], subscription: Dict[str, Any]) -> bool:
        special = "bus_special_value_"
        matched = True
        parts = 0
        matcher = subscription.get("matcher", {})
        for key, value in matcher.items():
            parts += 1
            if not matched:
                continue

            if value == special + "key":
                matched = key in args and args[key] is not None
            elif value == special + "blank":
                val = args.get(key)
                matched = val is not None and str(val).strip() == ""
            elif value == special + "empty":
                matched = args.get(key) is None
            elif value in (special + "nil", special + "null"):
                matched = key not in args
            elif value == special + "value":
                matched = args.get(key) is not None
            elif value == special + "present":
                val = args.get(key)
                matched = val is not None and str(val).strip() != ""
            else:
                if key in args and args[key] is not None:
                    pattern = utils.to_python_regex(value)
                    matched = bool(pattern.search(str(args[key])))
                else:
                    matched = False

        if parts == 0:
            matched = False
        return matched

    # Heartbeat ---------------------------------------------------------
    def _heartbeat_perform(self) -> None:
        lock_key = f"{self.bus.connection.namespace}:bus:heartbeat:lock"
        ts_key = f"{self.bus.connection.namespace}:bus:heartbeat:timestamp"
        lock_seconds = 60

        now = int(time.time())
        timeout = now + lock_seconds + 2

        if not self._acquire_lock(lock_key, now, timeout):
            return
        try:
            while True:
                last = self.redis.get(ts_key)
                current_minute = int(time.time() // 60)
                if last is not None and current_minute <= int(last):
                    break
                minute = current_minute if last is None else int(last) + 1
                attributes = self._heartbeat_attributes(minute)
                self.bus.publish("heartbeat_minutes", attributes)
                self.redis.set(ts_key, minute)
        finally:
            self.redis.delete(lock_key)

    def _acquire_lock(self, lock_key: str, now: int, timeout: int) -> bool:
        if self.redis.setnx(lock_key, timeout):
            return True
        current = self.redis.get(lock_key)
        if current and now <= int(current):
            return False
        prev = self.redis.getset(lock_key, timeout)
        return now > int(prev or 0)

    def _heartbeat_attributes(self, minute: int) -> Dict[str, Any]:
        seconds = minute * 60
        hours = minute // 60
        days = minute // (60 * 24)
        now_dt = time.gmtime(seconds)
        return {
            "epoch_seconds": seconds,
            "epoch_minutes": minute,
            "epoch_hours": hours,
            "epoch_days": days,
            "minute": now_dt.tm_min,
            "hour": now_dt.tm_hour,
            "day": now_dt.tm_mday,
            "month": now_dt.tm_mon,
            "year": now_dt.tm_year,
            "wday": now_dt.tm_wday,
        }
