"""
This script reads 'input.md', finds all .svg image URLs, downloads and converts them to .png using cairosvg,
and replaces the URL in the markdown with the uploaded .png file url. The result is written to 'input_png.md'.
"""

import httpx

import argparse

from pathlib import Path

import hashlib
import os
import re
import tempfile

from dotenv import load_dotenv
from .cos_uploader import upload
from .svg2png import svg_to_png_with_playwright

# To speed up playwright screenshotting when fonts are not needed
os.environ["PW_TEST_SCREENSHOT_NO_FONTS_READY"] = "1"

load_dotenv()


def main():
    parser = argparse.ArgumentParser(
        description="Convert SVG images in a Markdown file to PNG and upload them."
    )
    parser.add_argument("input_file", help="Path to the input markdown file.")
    parser.add_argument(
        "--save-svg",
        action="store_true",
        help="Save downloaded SVG files for debugging.",
    )
    args = parser.parse_args()
    input_file = args.input_file

    output_file = f"{os.path.splitext(input_file)[0]}_output.md"

    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Directory to store temporary PNGs
    png_dir = os.path.join(tempfile.gettempdir(), "svg2png_imgs")
    os.makedirs(png_dir, exist_ok=True)

    # Regex to match .svg URLs (http/https, .svg at end, not already .svg? or .svg#)
    pattern = re.compile(r"https?://[^\s)]+?\.svg(?![\w#?])")
    matches = list(pattern.finditer(content))
    print(f"Find {len(matches)} SVGs links")

    # convert finded .svg to .png
    url_paths = {}  # Map from SVG URL to local PNG path
    for match in matches:
        url = match.group(0)
        if url in url_paths:
            png_path = url_paths[url]
            print(f"Reusing converted PNG for {url} -> {png_path}")
            continue
        # Use a hash or basename for unique filename
        basename = os.path.basename(url)
        name, _ = os.path.splitext(basename)
        # Use hash to avoid collision
        url_hash = hashlib.md5(url.encode("utf-8")).hexdigest()[:8]
        png_filename = f"{name}_{url_hash}.png"
        png_path = os.path.join(png_dir, png_filename)

        # Download SVG and convert
        print(f"Downloading {url}")
        resp = httpx.get(url, timeout=10)
        resp.raise_for_status()

        # debug: save downloaded svg
        if args.save_svg:
            svg_path = os.path.join(png_dir, f"{name}_{url_hash}.svg")
            with open(svg_path, "wb") as f:
                f.write(resp.content)
            print(f"Saved SVG to {svg_path}")

        # Convert SVG to PNG using Playwright
        svg_to_png_with_playwright(resp.text, png_path)

        url_paths[url] = png_path
        print(f"Converted to {png_path}")

    # upload .png
    svg_to_png_map = {}
    for url, png_path in url_paths.items():
        print(f"Uploading {png_path}")
        png_url = upload(Path(png_path))
        svg_to_png_map[url] = png_url
        print(f"Uploaded to COS: {png_url}")

    # Replace all occurrences of the SVG URL with the PNG URL
    def replace_svg_with_png(match):
        svg_url = match.group(0)
        return svg_to_png_map.get(svg_url)

    new_content = pattern.sub(replace_svg_with_png, content)

    # Write the modified content to output file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"Written output to {output_file}")


if __name__ == "__main__":
    main()
