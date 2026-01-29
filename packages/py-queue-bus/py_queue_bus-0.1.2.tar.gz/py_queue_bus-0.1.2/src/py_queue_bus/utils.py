import os
import re
import time
import uuid
from typing import Any, Dict, Iterable

import tzlocal


def defaults() -> Dict[str, Any]:
    return {
        "incoming_queue": "bus_incoming",
        "bus_class_key": "QueueBus::Worker",
        "app_prefix": ":bus_app:",
        "subscription_set": ":bus_apps",
        "to_drive": True,
        "namespace": "resque",
    }


def timestamp() -> int:
    return int(time.time())


def hash_key(app_key: str, priority: str, job: str) -> str:
    app_key = normalize(app_key)
    return f"{app_key}_{priority}_{job}"


def normalize(value: Any) -> str:
    s = str(value)
    s = s.replace(" ", "_")
    return s.lower()


def unique_list(items: Iterable[Any]) -> list:
    seen = set()
    out = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def to_ruby_regexp(value: Any) -> Any:
    """Convert a Python regex to a Ruby-like string used by queue-bus."""
    if isinstance(value, re.Pattern):
        allowed = ["m", "i", "x"]
        present = []
        if value.flags & re.MULTILINE:
            present.append("m")
        if value.flags & re.IGNORECASE:
            present.append("i")
        if value.flags & re.VERBOSE:
            present.append("x")
        present = unique_list(present)
        missing = [m for m in allowed if m not in present]
        modifier_prefix = "?" + "".join(present) + "-" + "".join(missing)
        return f"({modifier_prefix}:{value.pattern})"
    return value


def to_python_regex(value: Any) -> re.Pattern:
    """Mirror node utils.toJSRegExp semantics for Python regex use."""
    if isinstance(value, re.Pattern):
        return value

    if isinstance(value, str) and value.startswith("(?") and value.endswith(")"):
        # Ruby-style "(?-mix:^.*thing.*$)"
        try:
            without_parens = value[1:-1]  # drop leading '(' and trailing ')'
            modifier_section, pattern = without_parens.split(":", 1)
            modifier_section = modifier_section.lstrip("?")
            if "-" in modifier_section:
                enabled, _ = modifier_section.split("-", 1)
            else:
                enabled = modifier_section
            flags = 0
            if "m" in enabled:
                flags |= re.MULTILINE
            if "i" in enabled:
                flags |= re.IGNORECASE
            if "x" in enabled:
                flags |= re.VERBOSE
            return re.compile(pattern, flags=flags)
        except ValueError:
            return re.compile(value)

    return re.compile(str(value))


def system_timezone() -> str:
    try:
        return tzlocal.get_localzone_name()
    except Exception:
        return "UTC"


def publish_metadata(event_type: str | None, args: Dict[str, Any]) -> Dict[str, Any]:
    payload: Dict[str, Any] = {}
    payload["bus_event_type"] = event_type if event_type else None
    payload["bus_published_at"] = timestamp()
    payload["bus_id"] = f"{payload['bus_published_at']}-{uuid.uuid4()}"
    payload["bus_app_hostname"] = os.uname().nodename
    payload["bus_timezone"] = system_timezone()
    lang = os.environ.get("LANG")
    payload["bus_locale"] = lang.split(".")[0] if lang and "." in lang else lang

    payload.update(args or {})
    return payload
