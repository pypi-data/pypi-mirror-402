import pytest
from terraback.utils.cross_scan_registry import CrossScanRegistry


@pytest.fixture(autouse=True)
def clear_normalize_cache():
    CrossScanRegistry._normalize.cache_clear()
    yield
    CrossScanRegistry._normalize.cache_clear()

def test_normalize_singular_suffixes():
    reg = CrossScanRegistry()
    assert reg._normalize("analysis") == "analysis"
    assert reg._normalize("radius") == "radius"


def test_normalize_plural_word():
    reg = CrossScanRegistry()
    assert reg._normalize("instances") == "instance"
