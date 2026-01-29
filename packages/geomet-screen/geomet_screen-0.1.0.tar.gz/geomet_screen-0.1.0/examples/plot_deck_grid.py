"""
Screen Deck Grid Visualization
================================

This example demonstrates how to load a screen deck layout from an Excel workbook
and visualize it using Plotly.
"""

# %%
# Create Sample Data
# ------------------
# First, we'll create a sample Excel workbook with deck data for demonstration.

import numpy as np
import pandas as pd
import tempfile
import os
import matplotlib.pyplot as plt

from geomet.screen.database import DatabaseConnection, ExcelLoader
from geomet.screen.visualization import plot_deck_grid

# Create sample data for demonstration (5x5 grid)
deck_data = np.array([
    [10.5, 12.3, 11.8, 13.2, 10.9],
    [9.8, 11.5, 10.2, 12.7, 11.3],
    [11.2, 10.8, 12.5, 11.9, 10.5],
    [12.1, 11.7, 10.3, 11.4, 12.8],
    [10.7, 12.9, 11.1, 10.6, 11.8],
])
df = pd.DataFrame(deck_data)

# Create a temporary Excel file
with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
    workbook_path = tmp.name

with pd.ExcelWriter(workbook_path, engine='openpyxl') as writer:
    df.to_excel(writer, sheet_name='Deck1', header=False, index=False)

print(f"Created example workbook with {df.shape[0]}x{df.shape[1]} grid")

# %%
# Load Deck from Excel
# --------------------
# Initialize the database and load the deck layout from the Excel workbook.

# Initialize database (in-memory for this example)
db = DatabaseConnection()
db.create_tables()

# Load the deck from Excel
loader = ExcelLoader(db.get_session())
deck = loader.load_deck_from_excel(
    workbook_path=workbook_path,
    sheet_name='Deck1',
    screen_name='Screen_A',
    deck_name='Deck_1',
)

print(f"Loaded deck: {deck.screen_name} / {deck.deck_name}")
print(f"Number of grid cells: {len(deck.grid_cells)}")

# %%
# Query Deck Data
# ---------------
# Extract the deck data as a DataFrame for visualization.

# Get the deck data as a DataFrame
grid_df = loader.get_deck_data(deck.id)

print(f"Grid data shape: {grid_df.shape}")
print("\nGrid data:")
print(grid_df)

# %%
# Create Matplotlib Visualization
# --------------------------------
# Create a heatmap visualization using matplotlib for the gallery thumbnail.

fig, ax = plt.subplots(figsize=(8, 6))
im = ax.imshow(grid_df.values, cmap='viridis', aspect='auto')
ax.set_xlabel('Column')
ax.set_ylabel('Row')
ax.set_title('Screen Deck A - Deck 1 Layout')
cbar = plt.colorbar(im, ax=ax, label='Value')
plt.tight_layout()
plt.show()

# %%
# Create Plotly Visualization
# ----------------------------
# Create an interactive heatmap visualization with Plotly.

fig_plotly = plot_deck_grid(
    grid_df,
    title="Screen Deck A - Deck 1 Layout (Interactive)",
    colorscale="Viridis",
    width=700,
    height=600,
)

# Display the interactive figure
# This will show as interactive HTML in notebooks and documentation
fig_plotly.show()

# %%
# Export with Kaleido
# -------------------
# Save the plotly figure as a static image using kaleido.

fig_plotly.write_image("deck_grid_static.png", width=800, height=600)
print("Saved static image: deck_grid_static.png")

# %%
# Clean up temporary files

db.close()
if os.path.exists(workbook_path):
    os.unlink(workbook_path)
if os.path.exists("deck_grid_static.png"):
    os.unlink("deck_grid_static.png")
