# wireframe-it

CLI and library to convert live web pages into wireframe-style HTML and PNG screenshots.

## Quick start

```bash
pip install wireframe-it
playwright install chromium  # or msedge if you prefer
wireframe-it https://pypi.org/
```

This writes `wireframes/pypi.org/wireframe.html` plus three screenshots: desktop, tablet, and mobile. Re-run with `--force` to regenerate the wireframe even if a cached `wireframe.html` already exists.

## How it works

- Downloads the page HTML
- Replaces images with bundled placeholders (SVG/PNG/JPG)
- Fills headings and text blocks with Lorem Ipsum based on their length/context (aside headings are labeled)
- Adds a `<base>` tag so remote CSS and assets still resolve
- Renders the transformed page in Playwright and saves screenshots at multiple viewports
- Formats the generated `wireframe.html` for readability (structure unchanged)
- Reuses an existing `wireframe.html` for screenshots unless `--force` is provided

## CLI usage

```bash
wireframe-it <url> [options]

Options:
	-o, --output PATH     Output folder (default: wireframes)
	--browser TEXT        chromium | msedge (default: chromium)
	--screenshots / --no-screenshots  Capture PNGs (default: on)
	--keep-remote-assets / --offline Keep remote CSS/JS (default) or strip for offline preview
	--timeout INTEGER     HTTP timeout in seconds (default: 15)
	--force               Refetch and regenerate wireframe.html even if one already exists
```

Examples:

```bash
wireframe-it https://www.bhf.org.uk -o output
wireframe-it https://example.com --browser msedge --no-screenshots
wireframe-it https://example.com --offline  # strips remote CSS/JS if you need a fully self-contained wireframe
wireframe-it https://www.utcsheffield.org.uk --force  # refresh a cached UTC Sheffield wireframe
```

## Example outputs (UTC wireframes)

Sample previews captured at common breakpoints for UTC-related pages (click to view full size, visit source for original):

- Desktop (1280×720) — [UTC Sheffield website](https://www.utcsheffield.org.uk):  
  <a href="www.utcsheffield.org.uk-desktop.png">
    <img src="www.utcsheffield.org.uk-desktop.png" alt="UTC desktop wireframe" width="260" />
  </a>

- Mobile (390×844) — [UTC Sheffield GitHub Pages](https://utcsheffield.github.io):  
  <a href="utcsheffield.github.io-mobile.png">
    <img src="utcsheffield.github.io-mobile.png" alt="UTC mobile wireframe" width="180" />
  </a>

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[all]
playwright install chromium

pytest
```

## Notes

- Screenshots are taken at desktop (1280x720), tablet (820x1180), and mobile (390x844).
- Use `--browser msedge` if you have Edge installed via Playwright (`playwright install msedge`).
- Placeholder images and Lorem Ipsum generation are bundled; no external assets required for the wireframe content itself.
- If Playwright reports the browser is missing, run `playwright install chromium` (or `playwright install msedge`).

