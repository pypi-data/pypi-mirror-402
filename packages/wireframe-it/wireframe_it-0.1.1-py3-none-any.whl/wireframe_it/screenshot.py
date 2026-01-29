from __future__ import annotations

from pathlib import Path
from typing import Dict

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

VIEWPORTS: Dict[str, Dict[str, int]] = {
    "tablet": {"width": 820, "height": 1180},
    "desktop": {"width": 1280, "height": 720},
    "mobile": {"width": 390, "height": 844},
}


def capture_screenshots(html: str, base_url: str, out_dir: Path, base_name: str, browser: str = "chromium") -> None:
    """Render HTML in Playwright and emit screenshots for multiple viewports."""
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        with sync_playwright() as p:
            browser_type = p.chromium
            launch_kwargs = {"headless": True}
            if browser == "msedge":
                launch_kwargs["channel"] = "msedge"
            try:
                browser_instance = browser_type.launch(**launch_kwargs)
            except PlaywrightError as exc:  # e.g., channel not installed
                requested = launch_kwargs.get("channel", "chromium")
                raise RuntimeError(
                    f"Playwright browser '{requested}' is not available. Run 'playwright install {requested}'."
                ) from exc

            try:
                context = browser_instance.new_context()
                page = context.new_page()
                for i, (label, size) in enumerate(VIEWPORTS.items()):
                    page.set_viewport_size(size)
                    page.set_content(html, wait_until="networkidle")
                    # Increase timeout for first viewport to allow content to fully load
                    timeout = 5000 if i == 0 else 500
                    page.wait_for_timeout(timeout)
                    screenshot_path = out_dir / f"{base_name}-{label}.png"
                    page.screenshot(path=str(screenshot_path), full_page=True)
                
                # Check if first screenshot is blank (suspiciously small file) and retry if needed
                first_screenshot = list(out_dir.glob(f"{base_name}-{list(VIEWPORTS.keys())[0]}.png"))
                if first_screenshot and first_screenshot[0].stat().st_size < 100000:  # Less than 100KB is likely blank
                    label = list(VIEWPORTS.keys())[0]
                    size = VIEWPORTS[label]
                    page.set_viewport_size(size)
                    page.set_content(html, wait_until="networkidle")
                    page.wait_for_timeout(2000)
                    screenshot_path = out_dir / f"{base_name}-{label}.png"
                    page.screenshot(path=str(screenshot_path), full_page=True)
            finally:
                browser_instance.close()
    except PlaywrightError as exc:
        raise RuntimeError("Playwright failed to capture screenshots. Is the browser installed?") from exc
    
