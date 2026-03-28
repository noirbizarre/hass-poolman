# /// script
# dependencies = [
#   "cairosvg",
# ]
# ///
from pathlib import Path

from cairosvg import svg2png  # ty:ignore[unresolved-import]

ROOT = Path(__file__).parent.parent
BRAND = ROOT / "custom_components/poolman/brand"


def brand(filename: str) -> str:
    """Get the resolved filename in the brand directory."""
    return str(BRAND / filename)


svg2png(url=brand("icon.svg"), write_to=brand("icon.png"), output_width=256, output_height=256)
svg2png(url=brand("icon.svg"), write_to=brand("icon@2x.png"), output_width=512, output_height=512)

svg2png(url=brand("logo.svg"), write_to=brand("logo.png"), output_width=256)
svg2png(url=brand("logo.svg"), write_to=brand("logo@2x.png"), output_width=512)
