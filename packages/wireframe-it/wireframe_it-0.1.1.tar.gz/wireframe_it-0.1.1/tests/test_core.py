from __future__ import annotations

from wireframe_it.core import slugify_url, transform_html


def test_transform_replaces_images_headings_and_text():
    html = """
    <html><head><link rel="stylesheet" href="https://cdn.example.com/style.css"></head>
    <body>
      <aside><h2>Title</h2></aside>
      <p>hello world</p>
      <img src="http://example.com/a.jpg" />
    </body></html>
    """

    output = transform_html(html, base_url="https://example.com/page")

    assert "data:image" in output  # image replaced with placeholder data URI
    assert "base href=\"https://example.com/page\"" in output
    assert "Aside H2:" in output  # semantic heading placeholder
    assert "hello world" not in output  # paragraph replaced


def test_transform_offline_strips_remote_assets():
    html = """
    <html><head><link rel="stylesheet" href="https://cdn.example.com/style.css"></head>
    <body><script src="https://cdn.example.com/app.js"></script></body></html>
    """

    output = transform_html(html, base_url="https://example.com/page", keep_remote_assets=False)

    assert "style.css" not in output
    assert "app.js" not in output
    assert "<base" not in output


def test_slugify_url():
    assert slugify_url("https://example.com/foo/bar") == "example.com-foo-bar"
    assert slugify_url("https://example.com/") == "example.com"
