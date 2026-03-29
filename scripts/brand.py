# /// script
# dependencies = [
#   "cairosvg",
# ]
# ///
from pathlib import Path

from cairosvg import svg2png  # ty:ignore[unresolved-import]

ROOT = Path(__file__).parent.parent
IMAGES = ROOT / "docs/images"
BRAND = ROOT / "custom_components/poolman/brand"


def brand(filename: str) -> str:
    """Get the resolved filename in the brand directory."""
    return str(BRAND / filename)


def image(filename: str) -> str:
    """Get the resolved filename in the images directory."""
    return str(IMAGES / filename)


svg2png(url=image("icon.svg"), write_to=brand("icon.png"), output_width=256, output_height=256)
svg2png(url=image("icon.svg"), write_to=brand("icon@2x.png"), output_width=512, output_height=512)

svg2png(url=image("logo.svg"), write_to=brand("logo.png"), output_width=256)
svg2png(url=image("logo.svg"), write_to=brand("logo@2x.png"), output_width=512)

svg2png(url=image("icon.svg"), write_to=image("favicon.png"), output_width=256, output_height=256)
