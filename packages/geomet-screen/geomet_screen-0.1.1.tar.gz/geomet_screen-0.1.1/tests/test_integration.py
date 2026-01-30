import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from geomet.screen import plot_deck_grid
from geomet.screen.database import (
    DatabaseConnection,
    ExcelLoader,
)


@pytest.mark.skip(reason="Excel loader / DB schema out of sync with new YAML-based data model; will be re-enabled after YAML->DB path is stable.")
def test_complete_workflow():
    """Integration: Excel -> DB -> visualization (temporarily disabled)."""
    # Create sample data
    deck_data = np.array([
        [10.5, 12.3, 11.8],
        [9.8, 11.5, 10.2],
        [11.2, 10.8, 12.5],
    ])
    df = pd.DataFrame(deck_data)

    # Create temporary Excel file
    with tempfile.TemporaryDirectory() as tmpdir:
        workbook_path = Path(tmpdir) / "test_screen.xlsx"

        with pd.ExcelWriter(workbook_path, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Deck1", header=False, index=False)

        # Initialize database
        db = DatabaseConnection()
        db.create_tables()
        session = db.get_session()

        # Load deck from Excel
        loader = ExcelLoader(session)
        deck = loader.load_deck_from_excel(
            workbook_path=str(workbook_path),
            sheet_name="Deck1",
            screen_name="TestScreen",
            deck_name="TestDeck1",
        )

        # Verify deck was loaded
        assert deck is not None
        assert deck.screen_name == "TestScreen"
        assert deck.deck_name == "TestDeck1"
        assert len(deck.grid_cells) == 9

        # Extract deck data
        grid_df = loader.get_deck_data(deck.id)

        # Verify grid data
        assert grid_df.shape == (3, 3)
        assert not grid_df.empty

        # Create visualization
        fig = plot_deck_grid(
            grid_df,
            title="Test Screen Deck",
            colorscale="Viridis",
        )

        # Verify figure was created
        assert fig is not None
        assert fig.layout.title.text == "Test Screen Deck"
        assert len(fig.data) == 1
        assert fig.data[0].type == "heatmap"

        # Clean up
        session.close()
        db.close()


@pytest.mark.skip(reason="Excel multi-deck workflow depends on legacy schema; will be revisited once YAML-driven model is wired into DB.")
def test_multiple_decks_workflow():
    """Integration: multiple Excel decks -> DB (temporarily disabled)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workbook_path = Path(tmpdir) / "multi_deck_screen.xlsx"

        # Create workbook with two sheets
        deck1_data = pd.DataFrame(np.random.rand(3, 3))
        deck2_data = pd.DataFrame(np.random.rand(4, 4))

        with pd.ExcelWriter(workbook_path, engine="openpyxl") as writer:
            deck1_data.to_excel(writer, sheet_name="Deck1", header=False, index=False)
            deck2_data.to_excel(writer, sheet_name="Deck2", header=False, index=False)

        # Initialize database
        db = DatabaseConnection()
        db.create_tables()
        session = db.get_session()

        # Load all decks from workbook
        loader = ExcelLoader(session)
        decks = loader.load_screen_from_workbook(
            workbook_path=str(workbook_path),
            screen_name="MultiDeckScreen",
        )

        # Verify both decks were loaded
        assert len(decks) == 2
        assert all(deck.screen_name == "MultiDeckScreen" for deck in decks)

        # Verify different grid sizes
        grid1 = loader.get_deck_data(decks[0].id)
        grid2 = loader.get_deck_data(decks[1].id)

        assert grid1.shape == (3, 3)
        assert grid2.shape == (4, 4)

        # Clean up
        session.close()
        db.close()