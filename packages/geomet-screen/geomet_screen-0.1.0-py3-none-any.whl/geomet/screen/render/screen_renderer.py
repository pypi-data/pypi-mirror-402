
from pathlib import Path
from typing import Dict, List, Literal
from PIL import Image
import plotly.graph_objects as go
from geomet.screen.models.screen import ScreenSpec
from geomet.screen.models.deck import DeckSpec
from geomet.screen.models.panel import PanelSpec
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

        # Render each deck individually to temporary images
        deck_images: List[Image.Image] = []
        for deck_name, deck in screen.decks.items():
            temp_path = output_path.parent / f"{deck_name}_mosaic.png"
            DeckRenderer.render_pillow(deck, panels, temp_path)
            deck_images.append(Image.open(temp_path))

        # Combine deck images
        if layout == "horizontal":
            total_width = sum(img.width for img in deck_images)
            total_height = max(img.height for img in deck_images)
            combined = Image.new("RGBA", (total_width, total_height), color=(255, 255, 255, 255))
            x_offset = 0
            for img in deck_images:
                combined.paste(img, (x_offset, 0))
                x_offset += img.width
        else:  # vertical
            total_width = max(img.width for img in deck_images)
            total_height = sum(img.height for img in deck_images)
            combined = Image.new("RGBA", (total_width, total_height), color=(255, 255, 255, 255))
            y_offset = 0
            for img in deck_images:
                combined.paste(img, (0, y_offset))
                y_offset += img.height

        # Save combined image
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
        fig = go.Figure()

        # Add each deck as a subplot-like trace
        deck_names = list(screen.decks.keys())
        for idx, (deck_name, deck) in enumerate(screen.decks.items()):
            rows = len(deck.layout)
            cols = len(deck.layout[0])

            # Map panel IDs to numeric codes for colors
            panel_ids = sorted(panels.keys())
            color_map = {pid: i for i, pid in enumerate(panel_ids)}

            z = [[color_map[cell] for cell in row] for row in deck.layout]

            hover_text = [[
                f"Deck: {deck_name}<br>ID: {cell}<br>Name: {panels[cell].name}<br>"
                f"Aperture: {panels[cell].aperture_short} x {panels[cell].aperture_long}<br>"
                f"Material: {panels[cell].material}<br>Duro: {panels[cell].duro_hardness}"
                for cell in row
            ] for row in deck.layout]

            # Offset each deck in y-axis for visual separation
            y_offset = idx * (rows + 2)  # Add spacing between decks
            z_offset = [[val for val in row] for row in z]

            fig.add_trace(go.Heatmap(
                z=z_offset,
                text=hover_text,
                hoverinfo="text",
                colorscale="Viridis",
                showscale=False
            ))

        fig.update_layout(
            title=f"Screen Layout: {screen.name}",
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=False),
            height=800,
            width=1200
        )

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
