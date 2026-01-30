from geomet.screen.models.panel import PanelSpec
from geomet.screen.models.panel_layout import PanelLayoutCalculator

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np


class PanelColorMapper:
    """Generate aesthetically pleasing color mapping for screen panels.

    Attributes:
        panels (dict): Dictionary of panel names and aperture areas {name: area}.
    """

    def __init__(self, panels: dict[str, float]):
        """
        Args:
            panels (dict): Dictionary of panel names and aperture areas {name: area}.
        """
        self.panels = panels

    @classmethod
    def from_specs(cls, specs: dict[str, PanelSpec]) -> "PanelColorMapper":
        """Create a mapper from panel specs by computing open area internally.

        Args:
            specs: Mapping of panel names to `PanelSpec`.

        Returns:
            PanelColorMapper: Instance with {name: open_area_mm2}.
        """
        areas: dict[str, float] = {}
        for name, spec in specs.items():
            if spec.orientation.name == "BLANK":
                # Treat blank panels as impact panels
                areas[name] = 0.0
            else:
                open_data = PanelLayoutCalculator.compute_open_area(spec)
                areas[name] = float(open_data["total_open_area_mm2"])
        return cls(areas)

    def generate_colormap(self) -> dict[str, str]:
        """Generate a color mapping for panels based on aperture size.

        Returns:
            dict: Mapping of panel names to color hex codes.
        """
        # Separate impact panels
        impact_panels = {k: v for k, v in self.panels.items() if v == 0}
        active_panels = {k: v for k, v in self.panels.items() if v > 0}

        if not active_panels:
            # Only impact panels
            return {name: "#808080" for name in impact_panels.keys()}

        # Sort by aperture size
        sorted_panels = sorted(active_panels.items(), key=lambda x: x[1])
        names, sizes = zip(*sorted_panels)

        # Split into two groups (top-like and bottom-like)
        mid = len(sizes) // 2
        bottom_names, bottom_sizes = names[:mid], sizes[:mid]
        top_names, top_sizes = names[mid:], sizes[mid:]

        bottom_cmap = plt.get_cmap("Greens_r")  # more saturated
        top_cmap = plt.get_cmap("Blues_r")  # more saturated

        def normalize(values):
            arr = np.array(values, dtype=float)
            if arr.size <= 1 or np.isclose(arr.max(), arr.min()):
                return np.full_like(arr, 0.7, dtype=float)  # mid/high saturation
            norm = (arr - arr.min()) / (arr.max() - arr.min())
            # Push away from the very pale ends
            low, high = 0.3, 0.95
            return low + norm * (high - low)

        bottom_norm = normalize(bottom_sizes)
        top_norm = normalize(top_sizes)

        color_map: dict[str, str] = {}
        for i, name in enumerate(bottom_names):
            color_map[name] = mcolors.to_hex(bottom_cmap(bottom_norm[i]))
        for i, name in enumerate(top_names):
            color_map[name] = mcolors.to_hex(top_cmap(top_norm[i]))

        for name in impact_panels.keys():
            color_map[name] = "#808080"

        return color_map