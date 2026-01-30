import string
from pathlib import Path
from typing import Dict, Literal
from PIL import Image
import plotly.graph_objects as go
import plotly.express as px

from geomet.screen.models import DeckSpec, PanelSpec
from geomet.screen.render.panel_renderer import PanelRenderer

# Max total pixels for the deck mosaic (tune as needed, below Pillow default)
MAX_DECK_PIXELS = 25_000_000


class DeckRenderer:
    """Handles rendering of deck layouts using different visualization methods."""

    @staticmethod
    def render_pillow(deck: DeckSpec, panels: Dict[str, PanelSpec], output_path: Path) -> Path:
        # Validate panel references only (let PanelRenderer handle images)
        for row in deck.layout:
            for panel_id in row:
                if panel_id not in panels:
                    raise ValueError(f"Panel ID '{panel_id}' not found in panels dictionary.")

        # Calculate mosaic dimensions in pixels at native resolution
        row_heights = [
            max(int(panels[panel_id].panel_height * panels[panel_id].px_per_mm) for panel_id in row)
            for row in deck.layout
        ]
        col_widths = [
            max(int(panels[row[col_idx]].panel_width * panels[row[col_idx]].px_per_mm) for row in deck.layout)
            for col_idx in range(deck.cols)
        ]

        total_width = sum(col_widths)
        total_height = sum(row_heights)

        # Compute global scale factor to keep total pixels under MAX_DECK_PIXELS
        total_pixels = total_width * total_height
        scale = 1.0
        if total_pixels > MAX_DECK_PIXELS:
            scale = (MAX_DECK_PIXELS / total_pixels) ** 0.5
            total_width = max(1, int(total_width * scale))
            total_height = max(1, int(total_height * scale))
            row_heights = [max(1, int(h * scale)) for h in row_heights]
            col_widths = [max(1, int(w * scale)) for w in col_widths]

        mosaic = Image.new("RGBA", (total_width, total_height), color=(255, 255, 255, 255))

        y_offset = 0
        for row_idx, row in enumerate(deck.layout):
            x_offset = 0
            for col_idx, panel_id in enumerate(row):
                panel_spec = panels[panel_id]
                panel_img = PanelRenderer.get_or_create_image(panel_spec)

                # Apply same scale factor to each panel
                native_w = int(panel_spec.panel_width * panel_spec.px_per_mm)
                native_h = int(panel_spec.panel_height * panel_spec.px_per_mm)
                target_w = max(1, int(native_w * scale))
                target_h = max(1, int(native_h * scale))
                panel_img = panel_img.resize((target_w, target_h))

                mosaic.paste(panel_img, (x_offset, y_offset), panel_img)
                x_offset += col_widths[col_idx]
            y_offset += row_heights[row_idx]

        output_path.parent.mkdir(parents=True, exist_ok=True)
        mosaic.save(output_path)
        return output_path


    @staticmethod
    def render_plotly(deck: "DeckSpec", panels: Dict[str, "PanelSpec"]) -> go.Figure:
        # Identify active rows and columns (non-empty cells)
        active_rows = [i for i, row in enumerate(deck.layout) if any(cell in panels for cell in row)]
        active_cols = [j for j in range(len(deck.layout[0])) if any(row[j] in panels for row in deck.layout)]

        min_row, max_row = min(active_rows), max(active_rows)
        min_col, max_col = min(active_cols), max(active_cols)

        # Crop layout to active region
        cropped_layout = [row[min_col:max_col + 1] for row in deck.layout[min_row:max_row + 1]]

        rows = len(cropped_layout)
        cols = len(cropped_layout[0])

        # Build z and hover text
        panel_ids = sorted(panels.keys())
        color_map = {pid: i for i, pid in enumerate(panel_ids)}

        z = [[color_map[cell] if cell in color_map else None for cell in row] for row in cropped_layout]

        hover_text = [[
            (
                f"ID: {cell}<br>Name: {panels[cell].name}<br>"
                f"Aperture: {panels[cell].aperture_short} x {panels[cell].aperture_long}<br>"
                f"Material: {panels[cell].material}<br>Duro: {panels[cell].duro_hardness}"
            ) if cell in panels else ""
            for cell in row
        ] for row in cropped_layout]

        # Use px.imshow for equal-aspect heatmap
        fig = px.imshow(
            z,
            text_auto=False,
            aspect="equal",
            color_continuous_scale="Viridis",
        )

        # Build x tick labels: 0 -> A, 1 -> B, ...
        x_tickvals = list(range(cols))
        x_ticktext = list(string.ascii_uppercase[:cols])

        # Build y tick labels: 1..rows (instead of 0..rows-1)
        y_tickvals = list(range(rows))  # underlying indices
        y_ticktext = [str(i + 1) for i in y_tickvals]

        fig.update_coloraxes(showscale=False)

        fig.data[0].customdata = hover_text
        fig.data[0].hovertemplate = "%{customdata}<extra></extra>"

        fig.update_layout(
            title=f"Deck Layout: {deck.name}",
            plot_bgcolor="white",
            xaxis=dict(
                side="top",
                dtick=1,
                tickmode="array",
                tickvals=x_tickvals,
                ticktext=x_ticktext,
                showgrid=True,
                gridcolor="rgba(0,0,0,0.5)",
                zeroline=False,
                constrain="domain",
                scaleanchor="y",
                scaleratio=1,
                range=[-0.5, cols - 0.5],
                tickfont=dict(
                    color="rgba(0, 0, 0, 0.8)",
                ),
            ),
            yaxis=dict(
                autorange="reversed",
                dtick=1,
                tickmode="array",
                tickvals=y_tickvals,
                ticktext=y_ticktext,  # shown as 1..rows
                showgrid=True,
                gridcolor="rgba(0,0,0,0.5)",
                zeroline=False,
                constrain="domain",
                range=[-0.5, rows - 0.5],
                tickfont=dict(
                    color="rgba(0, 0, 0, 0.8)",
                ),
            ),
        )

        return fig

    @staticmethod
    def render(deck: DeckSpec, panels: Dict[str, PanelSpec],
               mode: Literal["pillow", "plotly"],
               output_path: Path = None):
        if mode == "pillow":
            if output_path is None:
                raise ValueError("output_path is required for Pillow rendering.")
            return DeckRenderer.render_pillow(deck, panels, output_path)
        elif mode == "plotly":
            return DeckRenderer.render_plotly(deck, panels)
        else:
            raise ValueError("Invalid mode. Choose 'pillow' or 'plotly'.")
