"""CLI for exporting Markmap HTML to high-resolution PNG."""

import subprocess
import sys
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console

from . import __version__

console = Console()


def version_callback(value: bool) -> None:
    if value:
        console.print(f"markmap-export v{__version__}")
        raise typer.Exit()


def detect_optimal_size(page, svg_selector: str, padding: int = 100) -> tuple[int, int]:
    """
    Detect optimal viewport size based on actual SVG content.

    Returns (width, height) that fits the entire mindmap.
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
            const svg = document.querySelector('{svg_selector}');
            if (!svg) return null;

            // Get the <g> element that contains all content
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

    # Add padding and ensure minimum size
    width = max(int(bbox["width"]) + padding * 2, 800)
    height = max(int(bbox["height"]) + padding * 2, 600)

    return width, height


app = typer.Typer(add_completion=False)


@app.command()
def main(
    html_file: Annotated[
        Optional[Path],
        typer.Argument(
            help="Path to Markmap HTML file",
        ),
    ] = None,
    output: Annotated[
        Optional[Path],
        typer.Option(
            "-o", "--output",
            help="Output PNG file path (default: same name as input)",
        ),
    ] = None,
    width: Annotated[
        Optional[int],
        typer.Option(
            "-w", "--width",
            help="Viewport width in pixels (default: auto-detect)",
            min=100,
            max=16000,
        ),
    ] = None,
    height: Annotated[
        Optional[int],
        typer.Option(
            "-H", "--height",
            help="Viewport height in pixels (default: auto-detect)",
            min=100,
            max=16000,
        ),
    ] = None,
    scale: Annotated[
        float,
        typer.Option(
            "-s", "--scale",
            help="Device scale factor (2.0 = Retina)",
            min=0.5,
            max=10.0,
        ),
    ] = 2.0,
    wait: Annotated[
        int,
        typer.Option(
            "--wait",
            help="Wait time for rendering in milliseconds",
            min=0,
            max=30000,
        ),
    ] = 2000,
    quiet: Annotated[
        bool,
        typer.Option(
            "-q", "--quiet",
            help="Suppress output except errors",
        ),
    ] = False,
    install_browser: Annotated[
        bool,
        typer.Option(
            "--install-browser",
            help="Install Chromium browser for Playwright and exit",
        ),
    ] = False,
    version: Annotated[
        Optional[bool],
        typer.Option(
            "-v", "--version",
            help="Show version and exit",
            callback=version_callback,
            is_eager=True,
        ),
    ] = None,
) -> None:
    """
    Export Markmap HTML to high-resolution PNG.

    By default, viewport size is auto-detected based on mindmap content.
    Use -w and -H to override with fixed dimensions.

    \b
    Examples:
        markmap-export mindmap.html
        markmap-export mindmap.html -o output.png
        markmap-export mindmap.html -w 3000 -H 4000 -s 2
    """
    # Handle --install-browser
    if install_browser:
        console.print("Installing Chromium for Playwright...")
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            console.print("[green]✓[/green] Chromium installed successfully")
        else:
            console.print(f"[red]Error:[/red] {result.stderr}")
            raise typer.Exit(1)
        raise typer.Exit()

    # Validate html_file
    if html_file is None:
        console.print("[red]Error:[/red] Missing argument 'HTML_FILE'")
        console.print("Usage: markmap-export [OPTIONS] HTML_FILE")
        console.print("Try 'markmap-export --help' for help.")
        raise typer.Exit(1)

    if not html_file.exists():
        console.print(f"[red]Error:[/red] File not found: {html_file}")
        raise typer.Exit(1)

    # Import playwright
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        console.print(
            "[red]Error:[/red] playwright is not installed.\n"
            "Run: [cyan]markmap-export --install-browser[/cyan]"
        )
        raise typer.Exit(1)

    # Determine output path
    html_file = html_file.resolve()
    output_path = output.resolve() if output else html_file.with_suffix(".png")
    file_url = f"file://{html_file}"

    auto_size = width is None or height is None

    if not quiet:
        console.print(f"[dim]Input:[/dim]  {html_file}")
        console.print(f"[dim]Output:[/dim] {output_path}")

    with sync_playwright() as p:
        browser = p.chromium.launch()

        # SVG selector (markmap uses either #mindmap or #markmap)
        svg_selector = "svg#mindmap, svg#markmap, svg.markmap"

        if auto_size:
            # Phase 1: Load with initial viewport to detect content size
            if not quiet:
                console.print("[dim]Detecting optimal size...[/dim]")

            page = browser.new_page(
                viewport={"width": 4000, "height": 4000},
                device_scale_factor=1,
            )
            page.goto(file_url, wait_until="networkidle")
            page.wait_for_timeout(wait)

            detected_w, detected_h = detect_optimal_size(page, svg_selector)
            page.close()

            # Use detected size, allow manual override for one dimension
            final_width = width if width is not None else detected_w
            final_height = height if height is not None else detected_h

            if not quiet:
                console.print(f"[dim]Detected content size:[/dim] {detected_w}x{detected_h}")
        else:
            final_width = width
            final_height = height

        # Phase 2: Render at final size
        if not quiet:
            console.print(
                f"[dim]Rendering at:[/dim] {final_width}x{final_height} "
                f"[dim]@ {scale}x = {int(final_width * scale)}x{int(final_height * scale)} pixels[/dim]"
            )

        page = browser.new_page(
            viewport={"width": final_width, "height": final_height},
            device_scale_factor=scale,
        )
        page.goto(file_url, wait_until="networkidle")
        page.wait_for_timeout(wait)

        # Trigger fit() to adapt to new viewport
        page.evaluate("""
            () => {
                if (window.mm && typeof window.mm.fit === 'function') {
                    window.mm.fit();
                }
            }
        """)
        page.wait_for_timeout(500)

        # Find and screenshot the SVG
        svg = page.locator(svg_selector).first

        if svg.count() == 0:
            if not quiet:
                console.print("[yellow]Warning:[/yellow] SVG not found, capturing full page")
            page.screenshot(path=str(output_path), full_page=True)
        else:
            svg.screenshot(path=str(output_path))

        browser.close()

    # Report result
    if output_path.exists():
        size_kb = output_path.stat().st_size / 1024
        if size_kb > 1024:
            size_str = f"{size_kb / 1024:.2f} MB"
        else:
            size_str = f"{size_kb:.0f} KB"

        if not quiet:
            console.print(f"[green]✓[/green] Exported: {output_path} ({size_str})")
    else:
        console.print("[red]Error:[/red] Export failed")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
