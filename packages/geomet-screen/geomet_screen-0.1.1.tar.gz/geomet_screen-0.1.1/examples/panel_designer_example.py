
"""
Panel Design Examples
======================

This example demonstrates how to use the `PanelSpec` and `PanelTileGenerator`
classes to define a screen panel, compute its aperture grid layout, and
generate an image for visual validation.

We start with a simple panel specification and progressively add functionality.
"""

# %%
# Import required classes
import matplotlib.pyplot as plt

from geomet.screen import PanelLayoutCalculator
from geomet.screen.models.panel import PanelSpec
from geomet.screen.render.panel_renderer import PanelRenderer

# %%
# Simple panel spec
# -----------------

spec = PanelSpec(
    panel_width=300,
    panel_height=300,
    aperture_long=65,
    aperture_short=35,
    orientation="with-flow",  # ore flows top-to-bottom
    radius=5,              # rounded corners
    aperture_rgba=(0, 0, 0, 0)  # transparent apertures
)
print("PanelSpec created:", spec)

# %%
# Display the image
# -----------------

img = PanelRenderer.render_pillow(spec)

plt.figure(figsize=(6, 6))
plt.imshow(img)
plt.axis("off")
plt.title("Panel Layout Visualization")
plt.show()

# %%
# Compute open area
# -----------------

open_area = PanelLayoutCalculator.compute_open_area(spec)
print("Open area calculation:")
print(f" Aperture area (mm²): {open_area['aperture_area_mm2']:.2f}")
print(f" Total open area (mm²): {open_area['total_open_area_mm2']:.2f}")
print(f" Panel area (mm²): {open_area['panel_area_mm2']:.2f}")
print(f" Open area (%): {open_area['open_area_percent']:.2f}%")

# %%
# Another example
# ---------------
# Let's create another panel design with different specifications.

spec2 = PanelSpec(
    panel_width=600,
    panel_height=300,
    aperture_long=26,
    aperture_short=7.5,
    orientation="cross-flow",
    min_ligament=6.0,
    radius=3,
    panel_color_rgba=(0, 102, 204, 255)
)

img2 = PanelRenderer.render_pillow(spec2)
plt.figure(figsize=(8, 4))
plt.imshow(img2)
plt.axis("off")
plt.title("Second Panel Layout Visualization")
plt.show()
