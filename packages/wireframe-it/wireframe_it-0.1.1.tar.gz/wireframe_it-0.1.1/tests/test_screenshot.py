from __future__ import annotations

import types
from pathlib import Path

import pytest
from playwright.sync_api import Error as PlaywrightError

from wireframe_it.screenshot import capture_screenshots


def test_capture_screenshots_missing_browser(monkeypatch, tmp_path: Path):
    """Capture should surface a helpful error when browser channel is missing."""

    class FakeContextManager:
        def __enter__(self):
            raise PlaywrightError("Browser not found")

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr("wireframe_it.screenshot.sync_playwright", lambda: FakeContextManager())

    with pytest.raises(RuntimeError) as excinfo:
        capture_screenshots("<html></html>", "https://example.com", tmp_path, "page", browser="msedge")

    assert "playwright install" in str(excinfo.value).lower() or "browser" in str(excinfo.value).lower()
