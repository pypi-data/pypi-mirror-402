import re
from py_queue_bus import utils


def test_to_ruby_regexp_round_trip():
    pattern = re.compile(r"^hello.*world$", re.IGNORECASE | re.MULTILINE)
    ruby = utils.to_ruby_regexp(pattern)
    assert ruby.startswith("(?")
    # Back to python regex
    py = utils.to_python_regex(ruby)
    assert py.search("hello WORLD")


def test_publish_metadata_defaults_and_overrides():
    payload = utils.publish_metadata("demo", {"x": 1})
    assert payload["bus_event_type"] == "demo"
    assert payload["bus_published_at"] > 0
    assert "bus_id" in payload
    assert payload["x"] == 1


def test_normalize_and_hash_key():
    key = utils.hash_key("My App", "priority", "job")
    assert key == "my_app_priority_job"
