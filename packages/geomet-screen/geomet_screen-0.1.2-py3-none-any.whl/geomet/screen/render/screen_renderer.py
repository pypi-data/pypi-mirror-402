
from pathlib import Path
from typing import Dict, List, Literal
from PIL import Image
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from geomet.screen.models.screen import ScreenSpec
from geomet.screen.models import PanelSpec
from .deck_renderer import DeckRenderer


class ScreenRenderer:
    """Handles rendering of full screens composed of multiple decks.

    Supports:
        - Pillow: Static combined mosaic image.
        - Plotly: Interactive visualization with multiple decks.
    """

    @staticmethod
    def render_pillow(screen: ScreenSpec, panels: Dict[str, PanelSpec], output_path: Path, layout: str = "horizontal") -> Path:
        """Render a screen with multiple decks as a static image using Pillow.

        Args:
            screen (ScreenSpec): Screen specification containing multiple decks.
            panels (Dict[str, PanelSpec]): Dictionary of panel specifications keyed by panel ID.
            output_path (Path): Path where the combined mosaic image will be saved.
            layout (str): Layout mode for decks ("horizontal" or "vertical").

        Returns:
            Path: Path to the saved screen mosaic image.

        Raises:
            ValueError: If layout mode is invalid.
        """

        if layout not in ("horizontal", "vertical"):
            raise ValueError("Layout must be 'horizontal' or 'vertical'.")

        # 1\) Render each deck to a temporary image
        deck_images: List[Image.Image] = []
        deck_names: List[str] = []
        for deck_name, deck in screen.decks.items():
            temp_path = output_path.parent / f"{deck_name}_mosaic.png"
            DeckRenderer.render_pillow(deck, panels, temp_path)
            deck_images.append(Image.open(temp_path))
            deck_names.append(deck_name)

        # 2\) Combine all deck images with 1\-panel padding
        if not deck_images:
            raise ValueError("No deck images to combine.")

        # Use the first deck to derive per\-panel size
        first_deck_name = deck_names[0]
        first_deck = screen.decks[first_deck_name]
        rows = len(first_deck.layout)
        cols = len(first_deck.layout[0])

        first_img = deck_images[0]
        panel_height = first_img.height / rows
        panel_width = first_img.width / cols

        # 1\-panel padding in pixels, depending on orientation
        if layout == "horizontal":
            panel_padding = int(round(panel_width))
        else:  # vertical
            panel_padding = int(round(panel_height))

        if layout == "horizontal":
            total_width = sum(img.width for img in deck_images) + panel_padding * (len(deck_images) - 1)
            total_height = max(img.height for img in deck_images)
            combined = Image.new("RGBA", (total_width, total_height), color=(255, 255, 255, 255))

            x_offset = 0
            for idx, img in enumerate(deck_images):
                combined.paste(img, (x_offset, 0))
                x_offset += img.width
                if idx < len(deck_images) - 1:
                    x_offset += panel_padding
        else:  # vertical
            total_width = max(img.width for img in deck_images)
            total_height = sum(img.height for img in deck_images) + panel_padding * (len(deck_images) - 1)
            combined = Image.new("RGBA", (total_width, total_height), color=(255, 255, 255, 255))

            y_offset = 0
            for idx, img in enumerate(deck_images):
                combined.paste(img, (0, y_offset))
                y_offset += img.height
                if idx < len(deck_images) - 1:
                    y_offset += panel_padding

        output_path.parent.mkdir(parents=True, exist_ok=True)
        combined.save(output_path)
        return output_path

    @staticmethod
    def render_plotly(screen: ScreenSpec, panels: Dict[str, PanelSpec]) -> go.Figure:
        """Render a screen with multiple decks as an interactive Plotly figure.

        Args:
            screen (ScreenSpec): Screen specification containing multiple decks.
            panels (Dict[str, PanelSpec]): Dictionary of panel specifications keyed by panel ID.

        Returns:
            go.Figure: Plotly figure object with multiple deck heatmaps.
        """
        from geomet.screen.render.panel_colors import PanelColorMapper

        deck_items = list(screen.decks.items())
        n_decks = len(deck_items)
        if n_decks == 0:
            raise ValueError("Screen has no decks to render.")

        fig = make_subplots(
            rows=1,
            cols=n_decks,
            horizontal_spacing=0.05,
            subplot_titles=[deck_name for deck_name, _ in deck_items],
        )

        # Move subplot titles a bit higher
        if fig.layout.annotations:
            for ann in fig.layout.annotations:
                ann.update(y=ann.y + 0.03, yanchor="bottom")

        # 1\) Map panel id \-> panel type label (PanelSpec.name)
        panel_type_by_id: Dict[str, str] = {}
        for pid, pspec in panels.items():
            panel_type_by_id[pid] = pspec.name

        # 2\) Determine unique type labels actually used in the decks
        type_labels = set()
        for _, deck in deck_items:
            for row in deck.layout:
                for pid in row:
                    if pid in panel_type_by_id:
                        type_labels.add(panel_type_by_id[pid])

        # 3\) Build a unique PanelSpec per type label, for color mapping
        unique_specs: Dict[str, PanelSpec] = {}
        for pid, pspec in panels.items():
            tlabel = pspec.name
            if tlabel in type_labels and tlabel not in unique_specs:
                unique_specs[tlabel] = pspec

        # 4\) Use PanelColorMapper to assign a color per panel type (by open area)
        if unique_specs:
            mapper = PanelColorMapper.from_specs(unique_specs)
            type_color_map = mapper.generate_colormap()  # {type_label: hex}
        else:
            type_color_map = {}

        # Fallback: if mapper did not return a color for some label, use grey
        color_by_type: Dict[str, str] = {
            tlabel: type_color_map.get(tlabel, "#808080") for tlabel in type_labels
        }

        shown_labels = set()

        # 5\) For each deck and each type, add a masked heatmap trace
        deck_axis_configs = []
        for col_idx, (deck_name, deck) in enumerate(deck_items, start=1):
            layout = deck.layout
            rows = len(layout)
            cols = len(layout[0]) if rows > 0 else 0
            deck_axis_configs.append((rows, cols))

            # Precompute type grid
            type_grid: List[List[str]] = [
                [panel_type_by_id.get(pid, None) for pid in row] for row in layout
            ]

            # For each type, build a mask: 1 where that type is present, None elsewhere
            for tlabel in sorted(type_labels):
                z_mask: List[List[float]] = []
                any_found = False
                for r in range(rows):
                    row_vals: List[float] = []
                    for c in range(cols):
                        if type_grid[r][c] == tlabel:
                            row_vals.append(1.0)
                            any_found = True
                        else:
                            row_vals.append(None)
                    z_mask.append(row_vals)

                if not any_found:
                    # Skip types not present in this deck
                    continue

                color = color_by_type.get(tlabel, "#808080")

                fig.add_trace(
                    go.Heatmap(
                        z=z_mask,
                        x=list(range(cols)),
                        y=list(range(rows)),
                        colorscale=[[0.0, color], [1.0, color]],
                        showscale=False,  # no colorbar, legend only
                        name=tlabel,
                        hovertemplate=(
                                f"Deck: {deck_name}<br>"
                                "Col: %{x}<br>"
                                "Row: %{y}<extra>" + tlabel + "</extra>"
                        ),
                        legendgroup=tlabel,
                        showlegend=tlabel not in shown_labels,
                    ),
                    row=1,
                    col=col_idx,
                )

                shown_labels.add(tlabel)

        # 6\) Configure axes so each subplot behaves like DeckRenderer
        for col_idx, (rows, cols) in enumerate(deck_axis_configs, start=1):
            x_tickvals = list(range(cols))
            x_ticktext = [chr(ord("A") + i) for i in range(cols)]
            y_tickvals = list(range(rows))
            y_ticktext = [str(i + 1) for i in y_tickvals]

            fig.update_xaxes(
                row=1,
                col=col_idx,
                side="top",
                dtick=1,
                tickmode="array",
                tickvals=x_tickvals,
                ticktext=x_ticktext,
                showgrid=True,
                gridcolor="rgba(0,0,0,0.5)",
                zeroline=False,
                constrain="domain",
                scaleanchor=f"y{col_idx}" if col_idx > 1 else "y",
                scaleratio=1,
                range=[-0.5, cols - 0.5],
                tickfont=dict(color="rgba(0, 0, 0, 0.8)"),
            )

            fig.update_yaxes(
                row=1,
                col=col_idx,
                autorange="reversed",
                dtick=1,
                tickmode="array",
                tickvals=y_tickvals,
                ticktext=y_ticktext,
                showgrid=True,
                gridcolor="rgba(0,0,0,0.5)",
                zeroline=False,
                constrain="domain",
                range=[-0.5, rows - 0.5],
                tickfont=dict(color="rgba(0, 0, 0, 0.8)"),
            )

        # 7\) Layout: discrete legend on RHS, vertical stack
        fig.update_layout(
            title_text=f"Screen Layout: {screen.name}",
            showlegend=True,
            legend=dict(
                x=1.02,
                y=1.0,
                xanchor="left",
                yanchor="top",
                orientation="v",
                traceorder="normal",
            ),
            margin=dict(r=120),  # extra room for RHS legend
        )

        # No global colorbar
        fig.update_coloraxes(showscale=False)

        return fig

    @staticmethod
    def render(screen: ScreenSpec, panels: Dict[str, PanelSpec], mode: Literal["pillow", "plotly"], output_path: Path = None, layout: str = "horizontal"):
        """Factory method to render a screen using the specified mode.

        Args:
            screen (ScreenSpec): Screen specification containing multiple decks.
            panels (Dict[str, PanelSpec]): Dictionary of panel specifications keyed by panel ID.
            mode (Literal["pillow", "plotly"]): Rendering mode.
            output_path (Path, optional): Path for saving image if mode is 'pillow'.
            layout (str): Layout mode for Pillow rendering ("horizontal" or "vertical").

        Returns:
            Path or go.Figure: Path to saved image (Pillow) or Plotly figure object.

        Raises:
            ValueError: If mode is invalid or output_path is missing for Pillow mode.
        """
        if mode == "pillow":
            if output_path is None:
                raise ValueError("output_path is required for Pillow rendering.")
            return ScreenRenderer.render_pillow(screen, panels, output_path, layout)
        elif mode == "plotly":
            return ScreenRenderer.render_plotly(screen, panels)
        else:
            raise ValueError("Invalid mode. Choose 'pillow' or 'plotly'.")