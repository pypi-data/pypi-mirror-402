"""Core functionality for exporting Markmap to PNG."""

from pathlib import Path
from typing import Optional

from playwright.sync_api import sync_playwright, Page

SVG_SELECTOR = "svg#mindmap, svg#markmap, svg.markmap"


def detect_content_size(page: Page, padding: int = 100) -> tuple[int, int]:
    """
    Detect optimal viewport size based on actual SVG content.

    Args:
        page: Playwright page with loaded markmap
        padding: Padding around content in pixels

    Returns:
        (width, height) tuple that fits the entire mindmap
    """
    # Trigger fit() to ensure content is laid out
    page.evaluate("""
        () => {
            if (window.mm && typeof window.mm.fit === 'function') {
                window.mm.fit();
            }
        }
    """)
    page.wait_for_timeout(500)

    # Get the actual bounding box of all content within SVG
    bbox = page.evaluate(f"""
        () => {{
            const svg = document.querySelector('{SVG_SELECTOR}');
            if (!svg) return null;

            const g = svg.querySelector('g');
            if (!g) return svg.getBBox();

            const bbox = g.getBBox();
            return {{
                width: bbox.width,
                height: bbox.height,
                x: bbox.x,
                y: bbox.y
            }};
        }}
    """)

    if not bbox:
        return 2000, 1500  # fallback

    width = max(int(bbox["width"]) + padding * 2, 800)
    height = max(int(bbox["height"]) + padding * 2, 600)

    return width, height


def export_png(
    html: str | Path,
    output: Optional[str | Path] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
    scale: float = 2.0,
    wait_ms: int = 2000,
) -> Path:
    """
    Export a Markmap HTML file to PNG.

    Args:
        html: Path to HTML file or HTML content string
        output: Output PNG path (default: same name as input)
        width: Viewport width (default: auto-detect)
        height: Viewport height (default: auto-detect)
        scale: Device scale factor (2.0 = Retina)
        wait_ms: Wait time for rendering in milliseconds

    Returns:
        Path to the exported PNG file

    Example:
        >>> from markmap_export import export_png
        >>> export_png("mindmap.html")
        PosixPath('mindmap.png')

        >>> export_png("mindmap.html", output="out.png", scale=3)
        PosixPath('out.png')
    """
    # Handle input
    html_path = Path(html).resolve()
    if not html_path.exists():
        raise FileNotFoundError(f"HTML file not found: {html_path}")

    # Determine output path
    output_path = Path(output).resolve() if output else html_path.with_suffix(".png")
    file_url = f"file://{html_path}"

    auto_size = width is None or height is None

    with sync_playwright() as p:
        browser = p.chromium.launch()

        if auto_size:
            # Phase 1: Detect content size
            page = browser.new_page(
                viewport={"width": 4000, "height": 4000},
                device_scale_factor=1,
            )
            page.goto(file_url, wait_until="networkidle")
            page.wait_for_timeout(wait_ms)

            detected_w, detected_h = detect_content_size(page)
            page.close()

            final_width = width if width is not None else detected_w
            final_height = height if height is not None else detected_h
        else:
            final_width = width
            final_height = height

        # Phase 2: Render at final size
        page = browser.new_page(
            viewport={"width": final_width, "height": final_height},
            device_scale_factor=scale,
        )
        page.goto(file_url, wait_until="networkidle")
        page.wait_for_timeout(wait_ms)

        # Trigger fit()
        page.evaluate("""
            () => {
                if (window.mm && typeof window.mm.fit === 'function') {
                    window.mm.fit();
                }
            }
        """)
        page.wait_for_timeout(500)

        # Screenshot
        svg = page.locator(SVG_SELECTOR).first
        if svg.count() == 0:
            page.screenshot(path=str(output_path), full_page=True)
        else:
            svg.screenshot(path=str(output_path))

        browser.close()

    return output_path


def export_bytes(
    html: str | Path,
    width: Optional[int] = None,
    height: Optional[int] = None,
    scale: float = 2.0,
    wait_ms: int = 2000,
) -> bytes:
    """
    Export a Markmap HTML file to PNG bytes (useful for web APIs).

    Args:
        html: Path to HTML file
        width: Viewport width (default: auto-detect)
        height: Viewport height (default: auto-detect)
        scale: Device scale factor
        wait_ms: Wait time for rendering

    Returns:
        PNG image as bytes

    Example:
        >>> from markmap_export import export_bytes
        >>> png_data = export_bytes("mindmap.html")
        >>> len(png_data)
        1234567
    """
    html_path = Path(html).resolve()
    if not html_path.exists():
        raise FileNotFoundError(f"HTML file not found: {html_path}")

    file_url = f"file://{html_path}"
    auto_size = width is None or height is None

    with sync_playwright() as p:
        browser = p.chromium.launch()

        if auto_size:
            page = browser.new_page(
                viewport={"width": 4000, "height": 4000},
                device_scale_factor=1,
            )
            page.goto(file_url, wait_until="networkidle")
            page.wait_for_timeout(wait_ms)

            detected_w, detected_h = detect_content_size(page)
            page.close()

            final_width = width if width is not None else detected_w
            final_height = height if height is not None else detected_h
        else:
            final_width = width
            final_height = height

        page = browser.new_page(
            viewport={"width": final_width, "height": final_height},
            device_scale_factor=scale,
        )
        page.goto(file_url, wait_until="networkidle")
        page.wait_for_timeout(wait_ms)

        page.evaluate("""
            () => {
                if (window.mm && typeof window.mm.fit === 'function') {
                    window.mm.fit();
                }
            }
        """)
        page.wait_for_timeout(500)

        svg = page.locator(SVG_SELECTOR).first
        if svg.count() == 0:
            png_bytes = page.screenshot(full_page=True)
        else:
            png_bytes = svg.screenshot()

        browser.close()

    return png_bytes
