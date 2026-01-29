"""
Playwright Screenshot Generator for FinOps Dashboard

Captures high-quality screenshots of HTML-exported dashboards using Playwright MCP.
Optimized for executive presentations and visual analysis.

Requirements:
- Playwright MCP server configured in .mcp-networking.json
- Node.js with npx available
- HTML exports from Jupyter notebooks (finops-ceo-simple.ipynb, finops-cto-simple.ipynb)

Author: CloudOps-Runbooks
Version: 1.1.20
"""

import asyncio
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from rich.console import Console

console = Console()


class PlaywrightScreenshotGenerator:
    """Generate high-quality screenshots using Playwright MCP."""

    def __init__(
        self,
        output_dir: str = "artifacts/screenshots",
        viewport_width: int = 1920,
        viewport_height: int = 1080,
        scale: int = 2,
    ):
        """
        Initialize Playwright screenshot generator.

        Args:
            output_dir: Directory for screenshot outputs
            viewport_width: Browser viewport width (default: 1920px, HD standard)
            viewport_height: Browser viewport height (default: 1080px)
            scale: Device scale factor for high-DPI (default: 2 for retina)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.scale = scale

    def check_playwright_availability(self) -> bool:
        """
        Check if Playwright is available via npx.

        Returns:
            True if Playwright can be executed, False otherwise
        """
        try:
            result = subprocess.run(
                ["npx", "-y", "playwright", "--version"], capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    async def capture_screenshot_async(
        self, html_path: Path, output_filename: Optional[str] = None, full_page: bool = True
    ) -> Path:
        """
        Capture screenshot of HTML file using Playwright (async).

        Args:
            html_path: Path to HTML file to screenshot
            output_filename: Optional custom output filename
            full_page: Capture full page vs viewport only (default: True)

        Returns:
            Path to generated screenshot PNG

        Raises:
            FileNotFoundError: If HTML file doesn't exist
            RuntimeError: If Playwright execution fails
        """
        if not html_path.exists():
            raise FileNotFoundError(f"HTML file not found: {html_path}")

        # Generate output filename
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            output_filename = f"screenshot-{html_path.stem}-{timestamp}.png"

        screenshot_path = self.output_dir / output_filename

        # Create Playwright script
        playwright_script = self._generate_playwright_script(
            html_path=html_path, screenshot_path=screenshot_path, full_page=full_page
        )

        script_path = self.output_dir / ".playwright_temp_script.js"
        script_path.write_text(playwright_script)

        try:
            # Execute Playwright script via npx
            console.print(f"[dim]🎭 Launching Playwright to capture screenshot...[/]")

            process = await asyncio.create_subprocess_exec(
                "npx",
                "-y",
                "playwright",
                "test",
                str(script_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode("utf-8") if stderr else "Unknown error"
                raise RuntimeError(f"Playwright execution failed: {error_msg}")

            # Verify screenshot was created
            if not screenshot_path.exists():
                raise RuntimeError(f"Screenshot was not created at {screenshot_path}")

            console.print(f"[green]✅ Screenshot saved: {screenshot_path}[/]")
            return screenshot_path

        finally:
            # Cleanup temporary script
            if script_path.exists():
                script_path.unlink()

    def capture_screenshot(
        self, html_path: Path, output_filename: Optional[str] = None, full_page: bool = True
    ) -> Path:
        """
        Capture screenshot of HTML file using Playwright (synchronous wrapper).

        Args:
            html_path: Path to HTML file to screenshot
            output_filename: Optional custom output filename
            full_page: Capture full page vs viewport only (default: True)

        Returns:
            Path to generated screenshot PNG
        """
        return asyncio.run(
            self.capture_screenshot_async(html_path=html_path, output_filename=output_filename, full_page=full_page)
        )

    def _generate_playwright_script(self, html_path: Path, screenshot_path: Path, full_page: bool) -> str:
        """
        Generate Playwright test script for screenshot capture.

        Args:
            html_path: Path to HTML file
            screenshot_path: Path for output screenshot
            full_page: Capture full page or viewport only

        Returns:
            JavaScript Playwright test script
        """
        # Convert paths to absolute for cross-platform compatibility
        html_url = f"file://{html_path.absolute()}"
        screenshot_path_str = str(screenshot_path.absolute())

        full_page_str = "true" if full_page else "false"

        script = f"""
const {{ test }} = require('@playwright/test');

test('capture dashboard screenshot', async ({{ page }}) => {{
    // Configure viewport for executive presentation
    await page.setViewportSize({{
        width: {self.viewport_width},
        height: {self.viewport_height}
    }});

    // Navigate to HTML export
    await page.goto('{html_url}');

    // Wait for page to fully render
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000); // Additional buffer for rendering

    // Capture screenshot
    await page.screenshot({{
        path: '{screenshot_path_str}',
        fullPage: {full_page_str},
        scale: 'device', // Use device scale factor ({self.scale}x)
        type: 'png'
    }});

    console.log('Screenshot captured successfully');
}});
"""
        return script

    def capture_multiple_screenshots(self, html_paths: list[Path], full_page: bool = True) -> list[Tuple[Path, Path]]:
        """
        Capture screenshots for multiple HTML files.

        Args:
            html_paths: List of HTML file paths
            full_page: Capture full page for all screenshots

        Returns:
            List of tuples (html_path, screenshot_path)
        """
        results = []

        for html_path in html_paths:
            try:
                screenshot_path = self.capture_screenshot(html_path=html_path, full_page=full_page)
                results.append((html_path, screenshot_path))
            except Exception as e:
                console.print(f"[red]❌ Failed to screenshot {html_path.name}: {e}[/]")
                continue

        return results

    async def generate_pdf_async(
        self, html_path: Path, output_filename: Optional[str] = None, mode: str = "architect"
    ) -> Path:
        """
        Generate PDF from HTML file using Playwright (async).

        v1.1.24: PDF export with persona-specific page sizes.

        Args:
            html_path: Path to HTML file
            output_filename: Optional custom output filename
            mode: Dashboard mode for page size (executive=A4, architect=Letter, sre=Legal)

        Returns:
            Path to generated PDF

        Raises:
            FileNotFoundError: If HTML file doesn't exist
            RuntimeError: If Playwright execution fails
        """
        if not html_path.exists():
            raise FileNotFoundError(f"HTML file not found: {html_path}")

        # Generate output filename
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            output_filename = f"dashboard-{html_path.stem}-{timestamp}.pdf"

        pdf_path = self.output_dir / output_filename

        # Create Playwright script for PDF generation
        playwright_script = self._generate_playwright_pdf_script(html_path=html_path, pdf_path=pdf_path, mode=mode)

        script_path = self.output_dir / ".playwright_pdf_temp_script.js"
        script_path.write_text(playwright_script)

        try:
            # Execute Playwright script via npx
            console.print(f"[dim]📄 Launching Playwright to generate PDF...[/]")

            process = await asyncio.create_subprocess_exec(
                "npx",
                "-y",
                "playwright",
                "test",
                str(script_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode("utf-8") if stderr else "Unknown error"
                raise RuntimeError(f"Playwright PDF generation failed: {error_msg}")

            # Verify PDF was created
            if not pdf_path.exists():
                raise RuntimeError(f"PDF was not created at {pdf_path}")

            console.print(f"[green]✅ PDF generated: {pdf_path}[/]")
            return pdf_path

        finally:
            # Cleanup temporary script
            if script_path.exists():
                script_path.unlink()

    def generate_pdf(self, html_path: Path, output_filename: Optional[str] = None, mode: str = "architect") -> Path:
        """
        Generate PDF from HTML file using Playwright (synchronous wrapper).

        Args:
            html_path: Path to HTML file
            output_filename: Optional custom output filename
            mode: Dashboard mode for page size (executive/architect/sre)

        Returns:
            Path to generated PDF
        """
        return asyncio.run(self.generate_pdf_async(html_path=html_path, output_filename=output_filename, mode=mode))

    def _generate_playwright_pdf_script(self, html_path: Path, pdf_path: Path, mode: str) -> str:
        """
        Generate Playwright test script for PDF generation.

        v1.1.24: Persona-specific page sizes for executive/architect/sre modes.

        Args:
            html_path: Path to HTML file
            pdf_path: Path for output PDF
            mode: Dashboard mode (executive/architect/sre)

        Returns:
            JavaScript Playwright test script
        """
        # Convert paths to absolute for cross-platform compatibility
        html_url = f"file://{html_path.absolute()}"
        pdf_path_str = str(pdf_path.absolute())

        # Persona-specific page formats
        page_format_map = {
            "executive": "A4",  # International standard for exec reports
            "architect": "Letter",  # US standard for technical docs
            "sre": "Legal",  # Extra length for detailed logs
        }
        page_format = page_format_map.get(mode, "Letter")

        script = f"""
const {{ test }} = require('@playwright/test');

test('generate dashboard PDF', async ({{ page }}) => {{
    // Navigate to HTML export
    await page.goto('{html_url}');

    // Wait for page to fully render
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1500); // Extra buffer for complex layouts

    // Generate PDF with persona-specific format
    await page.pdf({{
        path: '{pdf_path_str}',
        format: '{page_format}',
        printBackground: true,
        margin: {{
            top: '0.5in',
            right: '0.5in',
            bottom: '0.5in',
            left: '0.5in'
        }}
    }});

    console.log('PDF generated successfully: {page_format} format for {mode} mode');
}});
"""
        return script


def capture_dashboard_screenshot(
    html_path: Path, output_dir: str = "artifacts/screenshots", viewport_size: Tuple[int, int] = (1920, 1080)
) -> Path:
    """
    Convenience function to capture dashboard screenshot.

    Args:
        html_path: Path to HTML export
        output_dir: Output directory for screenshot
        viewport_size: Browser viewport (width, height)

    Returns:
        Path to generated screenshot

    Example:
        >>> html_path = Path("artifacts/screenshots/finops-dashboard-prod.html")
        >>> screenshot = capture_dashboard_screenshot(html_path)
        >>> print(f"Screenshot: {screenshot}")
    """
    generator = PlaywrightScreenshotGenerator(
        output_dir=output_dir,
        viewport_width=viewport_size[0],
        viewport_height=viewport_size[1],
        scale=2,  # High DPI for executive presentations
    )

    # Check Playwright availability
    if not generator.check_playwright_availability():
        console.print("[red]❌ Playwright not available. Install: npm install -g playwright[/]")
        raise RuntimeError("Playwright not found")

    return generator.capture_screenshot(html_path)


if __name__ == "__main__":
    """CLI for standalone screenshot generation."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate Playwright screenshots of FinOps dashboards")
    parser.add_argument("html_path", type=Path, help="Path to HTML export")
    parser.add_argument("--output", "-o", type=str, help="Output screenshot filename")
    parser.add_argument("--output-dir", type=str, default="artifacts/screenshots", help="Output directory")
    parser.add_argument("--viewport-width", type=int, default=1920, help="Viewport width")
    parser.add_argument("--viewport-height", type=int, default=1080, help="Viewport height")
    parser.add_argument("--viewport-only", action="store_true", help="Capture viewport only (not full page)")

    args = parser.parse_args()

    generator = PlaywrightScreenshotGenerator(
        output_dir=args.output_dir, viewport_width=args.viewport_width, viewport_height=args.viewport_height
    )

    if not generator.check_playwright_availability():
        console.print("[red]❌ Playwright not available[/]")
        console.print("[yellow]Install: npm install -g playwright && playwright install[/]")
        sys.exit(1)

    try:
        screenshot_path = generator.capture_screenshot(
            html_path=args.html_path, output_filename=args.output, full_page=not args.viewport_only
        )
        console.print(f"[green]✅ Screenshot saved: {screenshot_path}[/]")
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/]")
        sys.exit(1)
