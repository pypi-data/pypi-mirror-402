"""Compile-only integration test placeholder."""

import pytest


@pytest.mark.compile
def test_compile_marker_smoke() -> None:
    """Ensure compile-marked tests exist for CI collection."""
    assert True
