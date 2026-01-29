import json
import logging
from terraback.utils.cross_scan_registry import (
    cross_scan_registry,
    SCAN_FUNCTIONS,
    register_resource_scanner,
)


def setup_function():
    cross_scan_registry.clear()
    SCAN_FUNCTIONS.clear()


def test_successful_registration():
    register_resource_scanner(
        "dummy_resource",
        "json:loads",
        priority=5,
        tier="gold",
    )
    norm = cross_scan_registry._normalize("dummy_resource")
    assert norm in SCAN_FUNCTIONS
    entry = SCAN_FUNCTIONS[norm]
    assert entry["function"] is json.loads
    assert entry["tier"] == "gold"
    assert entry["priority"] == 5


def test_bad_import_path(caplog):
    with caplog.at_level(logging.ERROR):
        register_resource_scanner("bad_resource", "no.such.module:fn")
    norm = cross_scan_registry._normalize("bad_resource")
    assert norm not in SCAN_FUNCTIONS
    assert any("Could not import scanner" in r.message for r in caplog.records)
