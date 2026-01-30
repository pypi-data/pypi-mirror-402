from pathlib import Path
from typing import Literal
from PIL import Image, ImageDraw
import plotly.graph_objects as go

from geomet.screen.models import PanelSpec
from geomet.screen.models import PanelLayoutCalculator


class PanelRenderer:
    """Render a single panel using different backends (Pillow, Plotly, ...)."""

    @staticmethod
    def get_or_create_image(panel: PanelSpec) -> Image.Image:
        """
        Pull-or-create policy:
        - If `panel.image_path` exists, load and return it.
        - Otherwise, generate a Pillow image in-memory.
        """
        if panel.image_path is not None:
            path = Path(panel.image_path)
            if path.is_file():
                return Image.open(path).convert("RGBA")

        # Fallback: generate from spec, do not force saving
        return PanelRenderer.render_pillow(panel)

    @staticmethod
    def render_pillow(panel: PanelSpec, output_path: Path | None = None) -> Image.Image:
        grid = PanelLayoutCalculator.compute_grid(panel)

        img = Image.new("RGBA", (grid["panel_w"], grid["panel_h"]), panel.panel_color_rgba)
        draw = ImageDraw.Draw(img)

        x = grid["border"] + grid["lig_x"]
        for _col in range(grid["cols"]):
            y = grid["border"] + grid["lig_y"]
            for _row in range(grid["rows"]):
                x1, y1 = x, y
                x2, y2 = x + grid["ap_w"], y + grid["ap_h"]
                draw.rounded_rectangle(
                    [x1, y1, x2, y2],
                    radius=grid["radius"],
                    fill=panel.aperture_rgba,
                )
                y += grid["ap_h"] + grid["lig_y"]
            x += grid["ap_w"] + grid["lig_x"]

        if output_path is not None:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(output_path)

        return img


    @staticmethod
    def render_plotly(panel: PanelSpec) -> go.Figure:
        grid = PanelLayoutCalculator.compute_grid(panel)

        # Simple coarse representation: each aperture becomes one heatmap cell.
        z = [[1 for _ in range(grid["cols"])] for _ in range(grid["rows"])]

        hover_text = [[
            f"Panel: {panel.name or ''}<br>"
            f"Aperture: {panel.aperture_short} x {panel.aperture_long} mm<br>"
            f"Orientation: {panel.orientation}"
            for _ in range(grid["cols"])
        ] for _ in range(grid["rows"])]

        fig = go.Figure(data=go.Heatmap(
            z=z,
            text=hover_text,
            hoverinfo="text",
            colorscale="Greys"
        ))

        fig.update_layout(
            title=f"Panel Layout: {panel.name or ''}",
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=False),
        )

        return fig

    @staticmethod
    def render(panel: PanelSpec, mode: Literal["pillow", "plotly"], output_path: Path | None = None):
        if mode == "pillow":
            if output_path is None:
                raise ValueError("output_path is required for Pillow rendering.")
            return PanelRenderer.render_pillow(panel, output_path)
        elif mode == "plotly":
            return PanelRenderer.render_plotly(panel)
        else:
            raise ValueError("Invalid mode. Choose 'pillow' or 'plotly'.")
