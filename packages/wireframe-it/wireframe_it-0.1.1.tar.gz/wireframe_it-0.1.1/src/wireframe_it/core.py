from __future__ import annotations

import base64
import re
from pathlib import Path
from typing import Dict, Iterable, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

LOREM = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed non risus. Suspendisse lectus tortor, "
    "dignissim sit amet, adipiscing nec, ultricies sed, dolor. Cras elementum ultrices diam."
)

PLACEHOLDER_FILES: Dict[str, str] = {
    # Use a single PNG placeholder for consistency across all image types
    "svg": "placeholder.png",
    "png": "placeholder.png",
    "jpg": "placeholder.png",
    "jpeg": "placeholder.png",
}


def fetch_html(url: str, timeout: int = 15) -> str:
    """Download HTML from a URL."""
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def _load_placeholder_data_uri(ext: str) -> str:
    """Return a data URI for a bundled placeholder image."""
    from importlib import resources

    normalized = ext.lower() if ext else "svg"
    filename = PLACEHOLDER_FILES.get(normalized, PLACEHOLDER_FILES["svg"])
    mime = "image/svg+xml" if filename.endswith(".svg") else "image/png" if filename.endswith(".png") else "image/jpeg"

    with resources.files("wireframe_it.placeholders").joinpath(filename).open("rb") as fh:
        encoded = base64.b64encode(fh.read()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


_PLACEHOLDER_CACHE: Dict[str, str] = {}


def placeholder_data_uri(ext: str) -> str:
    if ext not in _PLACEHOLDER_CACHE:
        _PLACEHOLDER_CACHE[ext] = _load_placeholder_data_uri(ext)
    return _PLACEHOLDER_CACHE[ext]


def lorem_chunk(target_length: int) -> str:
    if target_length <= 0:
        return ""
    text = LOREM
    while len(text) < target_length:
        text += " " + LOREM
    return text[:target_length].rstrip()


def _heading_placeholder(tag_name: str, in_aside: bool, target_length: int) -> str:
    prefix = ("Aside " if in_aside else "") + tag_name.upper() + ": "
    min_length = max(target_length, len(prefix) + 12)
    body = lorem_chunk(min_length - len(prefix))
    return (prefix + body)[:min_length]


def _should_keep_heading(heading_text: str) -> bool:
    """Determine if a heading should be kept (descriptive/functional) or replaced (generic/greeting)."""
    text_lower = heading_text.lower().strip()

    # Very long headings become placeholders even if they contain brand words
    if len(heading_text) > 60:
        return False

    # Greetings/generic phrases to replace
    greetings = [
        "welcome",
        "hello",
        "hi there",
        "thanks",
        "thank you",
    ]

    # If text starts with greeting phrases, replace it
    for phrase in greetings:
        if text_lower.startswith(phrase):
            return False

    # Allow brand/section/CTA headings, but cap length so story-style titles are replaced
    if any(x in text_lower for x in ["bbc", "sheffield", "utc", "university"]):
        return len(heading_text) <= 40

    # Keep everything else - CTAs, section descriptors, brand names, etc., within length cap
    return len(heading_text) <= 50


def _detect_image_type(img_tag) -> str:
    """Detect if an image is likely a logo, hero, or icon based on context."""
    # Check for class/id hints
    classes = img_tag.get("class", [])
    img_id = img_tag.get("id", "").lower()
    src = img_tag.get("src", "").lower()
    alt_text = img_tag.get("alt", "").lower()
    
    class_str = " ".join(classes).lower() if isinstance(classes, list) else str(classes).lower()
    
    # Logo detection - check alt text too
    if any(x in class_str for x in ["logo", "brand"]) or any(x in img_id for x in ["logo", "brand"]):
        return "logo"
    if any(x in src for x in ["logo", "brand"]):
        return "logo"
    if any(x in alt_text for x in ["logo", "brand"]):
        return "logo"
    
    # Hero/banner detection
    if any(x in class_str for x in ["hero", "banner", "jumbotron"]) or any(x in img_id for x in ["hero", "banner"]):
        return "hero"
    if any(x in src for x in ["hero", "banner"]):
        return "hero"
    
    # Icon detection
    if any(x in class_str for x in ["icon", "fa-", "svg-icon"]) or any(x in img_id for x in ["icon"]):
        return "icon"
    if any(x in src for x in ["icon", "svg"]):
        return "icon"
    
    # Check parent context
    parent = img_tag.parent
    if parent:
        parent_name = parent.name
        parent_class = str(parent.get("class", [])).lower()
        
        if parent_name == "nav" or "nav" in parent_class or "navbar" in parent_class or "menu" in parent_class:
            return "icon"
        if parent_name == "header" or parent_name == "footer" or any(x in parent_class for x in ["header", "footer"]):
            return "logo"
    
    return "image"


def _get_semantic_content_label(tag) -> str:
    """Get a descriptive label based on semantic HTML context."""
    parent = tag
    for _ in range(3):  # Check up to 3 levels up
        if parent is None:
            break
        if parent.name in ("article", "section", "aside", "nav", "header", "footer", "main"):
            return parent.name.capitalize()
        parent = parent.parent
    
    # Check for common ARIA or data attributes
    role = tag.get("role", "").lower()
    if role:
        return role.capitalize()
    
    return "Content"


BLOCK_TAGS: Iterable[str] = ("p", "li", "figcaption", "blockquote", "dd", "dt", "span", "small", "em", "strong", "div")


def _tag_has_children(tag) -> bool:
    return any(getattr(child, "name", None) for child in tag.children)


def format_html(html: str) -> str:
    """Return prettified HTML for readability without altering structure."""
    soup = BeautifulSoup(html, "html.parser")
    return soup.prettify()


def transform_html(html: str, base_url: Optional[str] = None, keep_remote_assets: bool = True) -> str:
    """Apply wireframe placeholders to HTML text and return the modified HTML.

    keep_remote_assets controls whether a <base> tag is injected and remote CSS/JS are kept.
    """
    soup = BeautifulSoup(html, "html.parser")

    if base_url and keep_remote_assets:
        head = soup.head
        if head is None:
            head = soup.new_tag("head")
            if soup.html:
                soup.html.insert(0, head)
            else:
                soup.insert(0, head)
        if not head.find("base"):
            base_tag = soup.new_tag("base", href=base_url)
            head.insert(0, base_tag)

    if not keep_remote_assets:
        for link in soup.find_all("link", rel=lambda v: v and "stylesheet" in v):
            href = link.get("href", "")
            if href.startswith("http://") or href.startswith("https://"):
                link.decompose()
        for script in soup.find_all("script"):
            src = script.get("src", "")
            if src.startswith("http://") or src.startswith("https://"):
                script.decompose()

    # Replace <picture> elements with a single placeholder image
    for picture in soup.find_all("picture"):
        new_img = soup.new_tag("img")
        new_img["src"] = placeholder_data_uri("png")
        new_img["style"] = "width: 100%; height: 100%; object-fit: cover; display: block;"

        # Try to carry over meaningful alt text from any nested <img>
        inner_img = picture.find("img")
        alt_text = inner_img.get("alt") if inner_img else None
        new_img["alt"] = alt_text or "Image placeholder"

        picture.replace_with(new_img)

    for img in soup.find_all("img"):
        src = img.get("src", "")
        ext = Path(urlparse(src).path).suffix.lstrip(".") if src else "svg"
        img["src"] = placeholder_data_uri(ext)
        img.attrs.pop("srcset", None)

        # Stretch placeholder to fill its container for DTP-style wireframes
        img["style"] = "width: 100%; height: 100%; object-fit: cover; display: block;"
        
        # Detect image type and label appropriately
        img_type = _detect_image_type(img)
        if img_type == "logo":
            img["alt"] = "Logo placeholder"
        elif img_type == "hero":
            img["alt"] = "Hero image placeholder"
        elif img_type == "icon":
            img["alt"] = "Icon placeholder"
        elif not img.get("alt"):
            img["alt"] = "Image placeholder"
    
    # Also replace background images in inline styles
    for element in soup.find_all(style=True):
        style = element.get("style", "")
        if "background-image" in style:
            # Replace background-image URLs with placeholder
            element["style"] = re.sub(
                r'background-image\s*:\s*url\([^)]+\)',
                f'background-image: url({placeholder_data_uri("svg")})',
                style
            )

    # Replace video elements with placeholder images
    for video in soup.find_all("video"):
        new_img = soup.new_tag("img")
        new_img["src"] = placeholder_data_uri("svg")
        new_img["alt"] = "Video placeholder"
        new_img["style"] = "width: 100%; height: auto; display: block;"
        video.replace_with(new_img)

    # Replace iframe elements with placeholder images
    for iframe in soup.find_all("iframe"):
        # Create a wrapper div with display properties to ensure visibility
        wrapper = soup.new_tag("div")
        wrapper["style"] = "width: 100%; background-color: #e0e0e0; display: flex; align-items: center; justify-content: center; min-height: 300px; border: 2px dashed #999;"
        
        # Add a text label
        label_text = soup.new_tag("span")
        label_text.string = "[iframe]"
        label_text["style"] = "position: absolute; font-size: 14px; font-weight: bold; color: #666;"
        
        new_img = soup.new_tag("img")
        new_img["src"] = placeholder_data_uri("svg")
        new_img["alt"] = "iframe placeholder"
        new_img["style"] = "width: 80%; height: auto; max-width: 400px;"
        
        wrapper.append(new_img)
        wrapper.append(label_text)
        iframe.replace_with(wrapper)

    heading_pattern = re.compile(r"^h[1-6]$")
    for heading in soup.find_all(heading_pattern):
        original_text = heading.get_text(strip=True) or ""
        
        in_aside = heading.find_parent("aside") is not None
        # In asides, always replace to avoid leaving original text
        if not in_aside and _should_keep_heading(original_text):
            continue  # Keep the original heading when not in an aside

        target_len = len(original_text) if original_text else 24
        placeholder = _heading_placeholder(heading.name, in_aside, target_len)
        heading.clear()
        heading.append(placeholder)

    # Keep navigation text but replace other content
    # Find all nav elements and mark them to preserve
    nav_elements = set()
    for nav in soup.find_all("nav"):
        nav_elements.add(id(nav))
    
    # Also preserve text in header/footer that looks like navigation
    for header in soup.find_all(["header", "footer"]):
        for link in header.find_all("a"):
            nav_elements.add(id(link))

    for tag_name in BLOCK_TAGS:
        for block in soup.find_all(tag_name):
            in_aside = block.find_parent("aside") is not None

            if not in_aside:
                # Skip if part of navigation or has children
                if id(block) in nav_elements or _tag_has_children(block):
                    continue

                # Check if inside nav
                in_nav = False
                parent = block.parent
                while parent:
                    if parent.name == "nav" or id(parent) in nav_elements:
                        in_nav = True
                        break
                    parent = parent.parent

                if in_nav:
                    continue

            original_text = block.get_text(strip=True)
            # Always use placeholder text instead of basing on original length
            target_len = 64 if not original_text else min(len(original_text), 120)
            block.clear()
            block.append(lorem_chunk(target_len))

    # Also aggressively replace any text in elements with description/summary class names
    description_classes = ["description", "summary", "synopsis", "excerpt", "teaser", "preview"]
    
    for element in soup.find_all(True):
        element_class = str(element.get("class", [])).lower()
        if any(dc in element_class for dc in description_classes) and not _tag_has_children(element):
            text = element.get_text(strip=True)
            if text:
                target_len = min(len(text), 120)
                element.clear()
                element.append(soup.new_string(lorem_chunk(target_len)))

    return str(soup)


def slugify_url(url: str) -> str:
    parsed = urlparse(url)
    raw = (parsed.netloc + parsed.path).strip("/") or "page"
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", raw)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or "page"
