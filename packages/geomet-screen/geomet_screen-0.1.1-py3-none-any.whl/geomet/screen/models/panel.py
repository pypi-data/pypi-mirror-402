from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Union
from pathlib import Path
from enum import Enum

RGBA = Tuple[int, int, int, int]
ColorLike = Tuple[int, int, int, int]


class Orientation(Enum):
    """Defines the orientation of apertures in a screen panel."""
    WITH_FLOW = "with-flow"
    CROSS_FLOW = "cross-flow"
    BLANK = "blank"  # Represents no apertures


@dataclass
class PanelSpec:
    name: str | None = None
    panel_width: int = 300
    panel_height: int = 300
    aperture_long: float = 65.0
    aperture_short: float = 35.0
    orientation: Orientation | str = Orientation.WITH_FLOW
    material: str | None = None
    duro_hardness: float | None = None
    min_border: float = 15.0
    min_ligament: float = 16.0
    radius: float = 0.0
    px_per_mm: float = 3.0
    panel_color_rgba: RGBA = (127, 127, 127, 255)
    aperture_rgba: RGBA = (0, 0, 0, 0)
    aperture_color_map: Dict[Tuple[int, int], ColorLike] | None = None
    image_path: Path | None = None


    def __post_init__(self):
        """Validate radius and orientation after initialization."""
        # Normalize orientation to `Orientation`
        if isinstance(self.orientation, str):
            try:
                self.orientation = Orientation(self.orientation)
            except ValueError as exc:
                raise ValueError(
                    "Orientation must be one of: "
                    f"{', '.join(o.value for o in Orientation)}."
                ) from exc

        if not isinstance(self.orientation, Orientation):
            raise TypeError("orientation must be an `Orientation` enum value.")

        # Validate radius: cannot exceed half of the smallest aperture dimension
        min_aperture_dim = min(self.aperture_long, self.aperture_short)
        if self.radius > (min_aperture_dim / 2):
            raise ValueError(
                f"Radius {self.radius} mm is too large. "
                f"Must be <= {min_aperture_dim / 2:.2f} mm."
            )

    def to_pixels(self) -> Dict[str, int]:
        """Convert dimensions to pixels."""
        return dict(
            panel_w_px=int(round(self.panel_width * self.px_per_mm)),
            panel_h_px=int(round(self.panel_height * self.px_per_mm)),
            ap_long_px=int(round(self.aperture_long * self.px_per_mm)),
            ap_short_px=int(round(self.aperture_short * self.px_per_mm)),
            min_border_px=int(round(self.min_border * self.px_per_mm)),
            min_lig_px=int(round(self.min_ligament * self.px_per_mm)),
            radius_px=int(round(self.radius * self.px_per_mm)),
        )
