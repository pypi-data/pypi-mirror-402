from dataclasses import dataclass
from typing import Dict, Optional, Tuple
from pathlib import Path
from PIL import Image, ImageDraw
import math

RGBA = Tuple[int, int, int, int]
ColorLike = Tuple[int, int, int, int]


@dataclass
class PanelSpec:
    """Specification for a screen panel.

    Attributes:
        name (Optional[str]): Optional name for the panel.
        panel_width (int): Panel width in millimeters.
        panel_height (int): Panel height in millimeters.
        aperture_long (float): Aperture length in millimeters.
        aperture_short (float): Aperture width in millimeters.
        orientation (str): Orientation of apertures ("with-flow" or "cross-flow").
        material (Optional[str]): Material name.
        duro_hardness (Optional[float]): Duro hardness value.
        min_border (float): Minimum border in millimeters.
        min_ligament (float): Minimum ligament width in millimeters.
        radius (float): Corner radius in millimeters.
        px_per_mm (int): Scale factor in pixels per millimeter.
        panel_color_rgba (RGBA): RGBA color for the panel.
        aperture_rgba (RGBA): RGBA color for apertures (default transparent).
        aperture_color_map (Optional[Dict[Tuple[int, int], ColorLike]]): Optional color map for apertures.
        image_filepath (Optional[Path]): Optional file path for saving or accessing the generated image
    """

    name: Optional[str] = None
    panel_width: int = 300
    panel_height: int = 300
    aperture_long: float = 65.0
    aperture_short: float = 35.0
    orientation: str = "with-flow"  # "with-flow" or "cross-flow"
    material: Optional[str] = None
    duro_hardness: Optional[float] = None
    min_border: float = 10.0
    min_ligament: float = 16.0
    radius: float = 0.0
    px_per_mm: int = 3
    panel_color_rgba: RGBA = (127, 127, 127, 255)
    aperture_rgba: RGBA = (0, 0, 0, 0)  # Default transparent
    aperture_color_map: Optional[Dict[Tuple[int, int], ColorLike]] = None
    image_path: Optional[Path] = None

    def __post_init__(self):
        """Validate radius and orientation after initialization."""
        # Validate orientation
        if self.orientation not in ("with-flow", "cross-flow"):
            raise ValueError("Orientation must be 'with-flow' or 'cross-flow'.")

        # Validate radius: cannot exceed half of the smallest aperture dimension
        min_aperture_dim = min(self.aperture_long, self.aperture_short)
        if self.radius > (min_aperture_dim / 2):
            raise ValueError(
                f"Radius {self.radius} mm is too large. "
                f"Must be <= {min_aperture_dim / 2:.2f} mm."
            )

    def to_pixels(self) -> Dict[str, int]:
        """Convert dimensions to pixels.

        Returns:
            Dict[str, int]: Dictionary of scaled dimensions in pixels.
        """
        return dict(
            panel_w_px=int(round(self.panel_width * self.px_per_mm)),
            panel_h_px=int(round(self.panel_height * self.px_per_mm)),
            ap_long_px=int(round(self.aperture_long * self.px_per_mm)),
            ap_short_px=int(round(self.aperture_short * self.px_per_mm)),
            min_border_px=int(round(self.min_border * self.px_per_mm)),
            min_lig_px=int(round(self.min_ligament * self.px_per_mm)),
            radius_px=int(round(self.radius * self.px_per_mm)),
        )


class PanelTileGenerator:
    """Generate panel images with apertures packed dynamically."""

    def __init__(self, spec: PanelSpec):
        self.spec = spec

    def compute_grid(self) -> Dict[str, float]:
        """Compute grid layout dynamically based on constraints."""
        dims = self.spec.to_pixels()
        panel_w = dims["panel_w_px"]
        panel_h = dims["panel_h_px"]
        border = dims["min_border_px"]
        lig = dims["min_lig_px"]

        # Aperture dimensions based on orientation
        if self.spec.orientation == "with-flow":
            ap_w = dims["ap_short_px"]
            ap_h = dims["ap_long_px"]
        elif self.spec.orientation == "cross-flow":
            ap_w = dims["ap_long_px"]
            ap_h = dims["ap_short_px"]
        else:
            raise ValueError("Orientation must be 'with-flow' or 'cross-flow'.")

        usable_w = panel_w - 2 * border
        usable_h = panel_h - 2 * border

        cols = math.floor((usable_w + lig) / (ap_w + lig))
        rows = math.floor((usable_h + lig) / (ap_h + lig))

        remaining_w = usable_w - cols * ap_w
        remaining_h = usable_h - rows * ap_h
        lig_x = remaining_w / (cols + 1) if cols > 0 else 0
        lig_y = remaining_h / (rows + 1) if rows > 0 else 0

        return {
            "cols": cols,
            "rows": rows,
            "ap_w": ap_w,
            "ap_h": ap_h,
            "lig_x": lig_x,
            "lig_y": lig_y,
            "border": border,
            "panel_w": panel_w,
            "panel_h": panel_h,
            "radius": dims["radius_px"],
        }

    def compute_open_area(self) -> Dict[str, float]:
        """Compute total open area and percentage."""
        grid = self.compute_grid()
        cols, rows = grid["cols"], grid["rows"]
        ap_w_mm = self.spec.aperture_short if self.spec.orientation == "with-flow" else self.spec.aperture_long
        ap_h_mm = self.spec.aperture_long if self.spec.orientation == "with-flow" else self.spec.aperture_short
        r_mm = self.spec.radius

        # Aperture area with rounded corners
        rect_area = ap_w_mm * ap_h_mm
        corner_cutout = (4 - math.pi) * (r_mm ** 2)
        aperture_area = rect_area - corner_cutout

        total_open_area = aperture_area * cols * rows
        panel_area = self.spec.panel_width * self.spec.panel_height
        open_percent = (total_open_area / panel_area) * 100

        return {
            "aperture_area_mm2": aperture_area,
            "total_open_area_mm2": total_open_area,
            "panel_area_mm2": panel_area,
            "open_area_percent": open_percent,
        }


    def generate_image(self, output_dir: Path) -> Path:
        """Generate the panel image and save it."""
        img = self._create_image()
        filename = f"panel_{self.spec.panel_width}x{self.spec.panel_height}_{self.spec.aperture_long}x{self.spec.aperture_short}_{self.spec.orientation}.png"
        output_path = output_dir / filename
        img.save(output_path)
        return output_path

    def show(self) -> Image.Image:
        """Generate and display the panel image.

        Returns:
            Image.Image: The Pillow image object for further use.
        """
        img = self._create_image()
        img.show()  # Opens in default image viewer
        return img

    def _create_image(self) -> Image.Image:
        """Internal helper to create the panel image without saving."""
        grid = self.compute_grid()
        img = Image.new("RGBA", (grid["panel_w"], grid["panel_h"]), self.spec.panel_color_rgba)
        draw = ImageDraw.Draw(img)

        x = grid["border"] + grid["lig_x"]
        for col in range(grid["cols"]):
            y = grid["border"] + grid["lig_y"]
            for row in range(grid["rows"]):
                x1, y1 = x, y
                x2, y2 = x + grid["ap_w"], y + grid["ap_h"]
                draw.rounded_rectangle([x1, y1, x2, y2], radius=grid["radius"], fill=self.spec.aperture_rgba)
                y += grid["ap_h"] + grid["lig_y"]
            x += grid["ap_w"] + grid["lig_x"]

        return img
