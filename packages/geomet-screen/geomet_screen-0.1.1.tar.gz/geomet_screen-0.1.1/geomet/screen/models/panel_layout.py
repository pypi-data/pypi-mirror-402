from typing import Dict
import math
from geomet.screen.models.panel import PanelSpec, Orientation

class PanelLayoutCalculator:
    """Pure geometry and open-area calculations for a `PanelSpec`."""

    @staticmethod
    def compute_grid(spec: PanelSpec) -> Dict[str, float]:
        dims = spec.to_pixels()
        panel_w = dims["panel_w_px"]
        panel_h = dims["panel_h_px"]
        border = dims["min_border_px"]
        lig = dims["min_lig_px"]

        # Aperture dimensions based on orientation
        if spec.orientation == Orientation.WITH_FLOW:
            ap_w = dims["ap_short_px"]
            ap_h = dims["ap_long_px"]
        elif spec.orientation == Orientation.CROSS_FLOW:
            ap_w = dims["ap_long_px"]
            ap_h = dims["ap_short_px"]
        elif spec.orientation == Orientation.BLANK:
            ap_w = 0
            ap_h = 0
        else:
            raise ValueError("Orientation must be one of: "
                    f"{', '.join(o.value for o in Orientation)}.")

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

    @staticmethod
    def compute_open_area(spec: PanelSpec) -> Dict[str, float]:
        grid = PanelLayoutCalculator.compute_grid(spec)
        cols, rows = grid["cols"], grid["rows"]

        ap_w_mm = spec.aperture_short if spec.orientation == "with-flow" else spec.aperture_long
        ap_h_mm = spec.aperture_long if spec.orientation == "with-flow" else spec.aperture_short
        r_mm = spec.radius

        rect_area = ap_w_mm * ap_h_mm
        corner_cutout = (4 - math.pi) * (r_mm ** 2)
        aperture_area = rect_area - corner_cutout

        total_open_area = aperture_area * cols * rows
        panel_area = spec.panel_width * spec.panel_height
        open_percent = (total_open_area / panel_area) * 100 if panel_area > 0 else 0.0

        return {
            "aperture_area_mm2": aperture_area,
            "total_open_area_mm2": total_open_area,
            "panel_area_mm2": panel_area,
            "open_area_percent": open_percent,
        }
