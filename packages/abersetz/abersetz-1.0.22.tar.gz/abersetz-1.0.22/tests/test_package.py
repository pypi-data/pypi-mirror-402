"""Test suite for abersetz."""
# this_file: tests/test_package.py

import pytest


def test_version() -> None:
    """Verify package exposes version."""
    import abersetz

    assert abersetz.__version__


def test_getattr_rejects_unknown_symbol() -> None:
    """Ensure lazy exports fail loudly for typos while caching successes."""
    import abersetz

    with pytest.raises(AttributeError) as excinfo:
        abersetz.not_real_attribute

    assert "not_real_attribute" in str(excinfo.value)

    first = abersetz.translate_path
    second = abersetz.translate_path
    assert first is second
