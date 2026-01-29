"""
Utility script to create sample Excel workbook for testing.

This is a development utility and not included in the Sphinx gallery.
To run: python _create_sample_data.py
"""

import pandas as pd
import numpy as np
from pathlib import Path


def create_sample_workbook():
    """Create a sample Excel workbook with deck layouts."""
    output_dir = Path(__file__).parent
    output_file = output_dir / "sample_screen.xlsx"

    # Create sample data for Deck 1 (5x5 grid)
    deck1_data = np.array([
        [10.5, 12.3, 11.8, 13.2, 10.9],
        [9.8, 11.5, 10.2, 12.7, 11.3],
        [11.2, 10.8, 12.5, 11.9, 10.5],
        [12.1, 11.7, 10.3, 11.4, 12.8],
        [10.7, 12.9, 11.1, 10.6, 11.8],
    ])
    df1 = pd.DataFrame(deck1_data)

    # Create sample data for Deck 2 (6x4 grid)
    deck2_data = np.array([
        [15.2, 16.8, 14.5, 17.1],
        [14.9, 15.7, 16.3, 15.4],
        [16.1, 14.8, 15.9, 16.5],
        [15.5, 16.9, 14.7, 15.8],
        [16.4, 15.1, 16.7, 14.9],
        [14.6, 16.2, 15.3, 16.8],
    ])
    df2 = pd.DataFrame(deck2_data)

    # Write to Excel with multiple sheets
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        df1.to_excel(writer, sheet_name='Deck1', header=False, index=False)
        df2.to_excel(writer, sheet_name='Deck2', header=False, index=False)

    print(f"Created sample workbook: {output_file}")
    return output_file


if __name__ == "__main__":
    create_sample_workbook()
