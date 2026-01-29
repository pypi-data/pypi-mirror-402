import pytest

from terraback.terraform_generator.filters import sanitize_public_key


def test_sanitize_public_key_collapses_whitespace():
    key = "ssh-rsa AAAA\nBBBB\t  CCC  DDD\n"
    assert sanitize_public_key(key) == "ssh-rsa AAAA BBBB CCC DDD"


def test_sanitize_public_key_none_passthrough():
    assert sanitize_public_key(None) is None
