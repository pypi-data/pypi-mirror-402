from pathlib import Path
from playwright.sync_api import sync_playwright


def svg_to_png_with_playwright(svg_content: str, png_path: str, wait_time: int = 300):
    """
    Render SVG content to PNG using Playwright (Chromium).
    Args:
        svg_content: SVG XML string.
        png_path: Output PNG file path.
        wait_time: Extra wait time in ms for dynamic content (default 300ms).
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content(svg_content, wait_until="commit")
        page.wait_for_timeout(wait_time)
        svg_locator = page.locator("svg")
        svg_locator.screenshot(path=png_path, type="png")
        browser.close()


if __name__ == "__main__":
    dir = Path(__file__).parent.resolve()
    input = dir / "demo.svg"
    output = dir / "demo.png"
    print(f"Converting {input}")
    svg_to_png_with_playwright(input.read_text(), str(output))
    print(f"Converted to {output}")