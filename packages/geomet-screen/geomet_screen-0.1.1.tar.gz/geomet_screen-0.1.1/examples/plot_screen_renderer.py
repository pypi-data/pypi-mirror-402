"""
Screen Rendering Example
=========================

This example demonstrates how to:

- Load a screen configuration from a YAML file.
- Parse it into `ScreenSpec`, `DeckSpec`, and `PanelSpec` objects.
- Render the screen using both Pillow (static image) and Plotly (interactive visualization).

"""

# sphinx_gallery_thumbnail_number = -1

# %%
# Imports
# -------
from pathlib import Path

import numpy as np
import plotly
import yaml
from geomet.screen.models.screen import ScreenSpec
from geomet.screen.models.deck import DeckSpec
from geomet.screen.models.panel import PanelSpec
from geomet.screen.render.deck_renderer import DeckRenderer
from geomet.screen.render.panel_renderer import PanelRenderer
from geomet.screen.render.screen_renderer import ScreenRenderer
from geomet.screen.utils.mpl_tools import pil_to_figure

# %%
# Load Configuration
# ------------------
# The configuration file defines panels and screens with decks.
# We assume the file is located in `assets/config/example_screen.yaml`.

current_dir = Path(__file__).parent if '__file__' in globals() else Path.cwd()
config_path = current_dir.parent / "assets/example_screen.yaml"

with config_path.open("r") as f:
    config = yaml.safe_load(f)

# %%
# Parse Panels
# ------------
# Convert panel definitions into `PanelSpec` objects.

panels = {}
for panel_id, panel_data in config["panels"].items():
    panels[panel_id] = PanelSpec(
        name=panel_data["name"],
        panel_width=panel_data["width"],
        panel_height=panel_data["height"],
        aperture_short=panel_data["aperture_short"],
        aperture_long=panel_data["aperture_long"],
        radius=panel_data["radius"],
        min_border=panel_data["min_border"],
        orientation=panel_data["orientation"],
        material=panel_data["material"],
        duro_hardness=panel_data["duro_hardness"],
    )

# %%
# Display panel images
# --------------------

img0 = PanelRenderer.get_or_create_image(panels["P000"])
pil_to_figure(img0, figsize=(8, 4), title="Panel P000 Layout Visualization")

# %%
img1 = PanelRenderer.get_or_create_image(panels["P001"])
pil_to_figure(img1, figsize=(8, 4), title="Panel P001 Layout Visualization")

# %%
img2 = PanelRenderer.get_or_create_image(panels["P002"])
pil_to_figure(img2, figsize=(8, 4), title="Panel P002 Layout Visualization")

# %%
# Parse Screen and Decks
# -----------------------
# Convert screen definition into `ScreenSpec` and its decks into `DeckSpec`.

screen_data = config["screens"]["SC001"]
decks = {}
for deck_name, deck_info in screen_data["decks"].items():
    decks[deck_name] = DeckSpec(
        name=deck_name,
        rows=deck_info["rows"],
        cols=deck_info["cols"],
        layout=deck_info["layout"]
    )

screen = ScreenSpec(
    name="SC001",
    metadata=screen_data["metadata"],
    decks=decks
)

# %%
# Render with Pillow
# -------------------
# Generate a static image of the full screen (two decks side by side).

output_path = Path("assets/output/screen_mosaic.png")
ScreenRenderer.render(screen, panels, mode="pillow", output_path=output_path, layout="horizontal")
print(f"Static image saved to: {output_path}")

# %%
# Display the generated image

from PIL import Image

img = Image.open(output_path)
pil_to_figure(img, figsize=(8, 12), title="Screen Layout Visualization")

# %%
# Render with Plotly
# -------------------
# Generate an interactive visualization of the screen.
#
# We could render a single deck like this:
# fig = DeckRenderer.render(decks["TD"], panels, mode="plotly")

output_path = Path("assets/output/screen_layout.html")

fig = ScreenRenderer.render(screen, panels, mode="plotly")
fig.write_html(output_path)

plotly.io.show(fig)
