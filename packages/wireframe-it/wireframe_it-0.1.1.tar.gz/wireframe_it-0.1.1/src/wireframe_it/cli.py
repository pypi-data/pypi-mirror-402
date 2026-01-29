from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

import typer

from wireframe_it.core import fetch_html, slugify_url, transform_html, format_html
from wireframe_it.screenshot import capture_screenshots

app = typer.Typer(help="Generate wireframe placeholders and screenshots from a URL.")


@app.command()
def url(
    target: str = typer.Argument(..., help="URL to fetch and wireframe"),
    output: Path = typer.Option(Path("wireframes"), "--output", "-o", help="Output directory"),
    browser: str = typer.Option(
        "chromium",
        "--browser",
        case_sensitive=False,
        help="Browser for screenshots (chromium or msedge)",
    ),
    timeout: int = typer.Option(15, help="Request timeout (seconds)"),
    screenshots: bool = typer.Option(True, "--screenshots/--no-screenshots", help="Capture PNG screenshots"),
    keep_remote_assets: bool = typer.Option(
        True,
        "--keep-remote-assets/--offline",
        help="Keep remote CSS/JS (default) or strip them for offline preview",
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Force refetch and retransform, ignoring cached wireframe.html"),
) -> None:
    """Fetch a URL, replace content with placeholders, and write HTML + PNGs."""
    parsed = urlparse(target)
    if parsed.scheme not in {"http", "https"}:
        typer.echo("Error: target must be an http(s) URL.")
        raise typer.Exit(code=1)

    slug = slugify_url(target)
    out_dir = output / slug
    html_path = out_dir / "wireframe.html"

    if html_path.exists() and not force:
        typer.echo(f"Using existing wireframe at {html_path}")
        transformed = html_path.read_text(encoding="utf-8")
    else:
        out_dir.mkdir(parents=True, exist_ok=True)
        typer.echo(f"Fetching {target}…")
        html = fetch_html(target, timeout=timeout)
        transformed = transform_html(html, base_url=target, keep_remote_assets=keep_remote_assets)
        formatted = format_html(transformed)
        html_path.write_text(formatted, encoding="utf-8")
        typer.echo(f"Saved HTML to {html_path}")

    if screenshots:
        typer.echo("Capturing screenshots (desktop/tablet/mobile)…")
        try:
            capture_screenshots(transformed, target, out_dir, slug, browser=browser.lower())
            typer.echo(f"Screenshots in {out_dir}")
        except RuntimeError as exc:
            typer.echo(f"Screenshot error: {exc}")
            raise typer.Exit(code=1)
    else:
        typer.echo("Skipping screenshots.")


if __name__ == "__main__":
    app()
