
"""
Create screen panel icon
========================

Create an icon for gitlab @ 196x196 px showing a panel layout

"""

# %%
# Import required classes
import matplotlib.pyplot as plt

from geomet.screen.models.panel import PanelSpec, PanelTileGenerator

# %%
# Simple panel spec
# -----------------

spec = PanelSpec(
    px_per_mm=1,
    panel_width=196,
    panel_height=196,
    aperture_long=45,
    aperture_short=25,
    orientation="with-flow",  # ore flows top-to-bottom
    radius=4,              # rounded corners
    panel_color_rgba=(0, 102, 204, 255),
    aperture_rgba=(0, 0, 0, 0)  # transparent apertures
)
print("PanelSpec created:", spec)

# %%
# Compute grid layout
# -------------------

generator = PanelTileGenerator(spec)
grid = generator.compute_grid()
print("Computed grid layout:", grid)

# %%
# Display the image
# -----------------

img = generator.show()
img.save('panel_icon_196x196.png')# Opens in default image viewer

plt.figure(figsize=(6, 6))
plt.imshow(img)
plt.axis("off")
# plt.title("Panel Layout Visualization")
plt.show()
