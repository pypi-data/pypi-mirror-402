
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

        # Move subplot titles a bit higher to avoid overlap with top tick labels
        if fig.layout.annotations:
            for ann in fig.layout.annotations:
                ann.update(y=ann.y + 0.03, yanchor="bottom")

        for col_idx, (deck_name, deck) in enumerate(deck_items, start=1):
            deck_fig = DeckRenderer.render_plotly(deck, panels)
            if not deck_fig.data:
                continue

            deck_trace = deck_fig.data[0]

            # Place trace into correct subplot
            fig.add_trace(
                deck_trace,
                row=1,
                col=col_idx,
            )

            # First, add one trace per deck
            deck_axis_configs = []
            for col_idx, (deck_name, deck) in enumerate(deck_items, start=1):
                deck_fig = DeckRenderer.render_plotly(deck, panels)
                if not deck_fig.data:
                    continue

                deck_trace = deck_fig.data[0]
                fig.add_trace(deck_trace, row=1, col=col_idx)

                # Capture rows/cols used by this deck to derive tick ranges
                # (same logic as in DeckRenderer)
                layout = deck.layout
                rows = len(layout)
                cols = len(layout[0]) if rows > 0 else 0
                deck_axis_configs.append((rows, cols))

            # Now configure axes for each subplot so they match DeckRenderer
            for col_idx, (rows, cols) in enumerate(deck_axis_configs, start=1):
                # x ticks: A, B, C, ...
                x_tickvals = list(range(cols))
                x_ticktext = [chr(ord("A") + i) for i in range(cols)]

                # y ticks: 1..rows, reversed axis
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

            fig.update_layout(
                title_text=f"Screen Layout: {screen.name}",
                showlegend=False,
            )
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