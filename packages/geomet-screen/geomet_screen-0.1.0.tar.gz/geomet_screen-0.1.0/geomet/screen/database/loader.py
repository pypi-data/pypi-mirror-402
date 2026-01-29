"""Excel workbook loader for screen deck layouts."""

from pathlib import Path
from typing import List, Optional

import pandas as pd
from sqlalchemy.orm import Session

from geomet.screen.models import ScreenDeck, DeckGrid


class ExcelLoader:
    """Load screen deck layouts from Excel workbooks."""

    def __init__(self, session: Session):
        """
        Initialize the Excel loader.

        Args:
            session: SQLAlchemy database session
        """
        self.session = session

    def load_deck_from_excel(
        self,
        workbook_path: str,
        sheet_name: str,
        screen_name: str,
        deck_name: str,
    ) -> ScreenDeck:
        """
        Load a screen deck layout from an Excel sheet.

        Args:
            workbook_path: Path to the Excel workbook
            sheet_name: Name of the sheet containing the deck layout
            screen_name: Name of the screen
            deck_name: Name of the deck

        Returns:
            ScreenDeck instance with loaded grid data
        """
        # Read the Excel sheet
        df = pd.read_excel(workbook_path, sheet_name=sheet_name, header=None)

        # Create the ScreenDeck record
        deck = ScreenDeck(
            screen_name=screen_name,
            deck_name=deck_name,
            workbook_path=str(workbook_path),
            sheet_name=sheet_name,
        )
        self.session.add(deck)
        self.session.flush()  # Get the deck.id

        # Load grid cells
        for row_idx, row in df.iterrows():
            for col_idx, value in enumerate(row):
                if pd.notna(value):
                    grid_cell = DeckGrid(
                        deck_id=deck.id,
                        row=int(row_idx),
                        col=int(col_idx),
                        value=float(value) if isinstance(value, (int, float)) else None,
                        label=str(value) if not isinstance(value, (int, float)) else None,
                    )
                    self.session.add(grid_cell)

        self.session.commit()
        return deck

    def load_screen_from_workbook(
        self,
        workbook_path: str,
        screen_name: str,
        sheet_names: Optional[List[str]] = None,
    ) -> List[ScreenDeck]:
        """
        Load all decks from a workbook (one sheet per deck).

        Args:
            workbook_path: Path to the Excel workbook
            screen_name: Name of the screen
            sheet_names: List of sheet names to load. If None, loads all sheets.

        Returns:
            List of ScreenDeck instances
        """
        # Get all sheet names if not specified
        if sheet_names is None:
            excel_file = pd.ExcelFile(workbook_path)
            sheet_names = excel_file.sheet_names

        decks = []
        for sheet_name in sheet_names:
            deck_name = f"{screen_name}_deck_{len(decks) + 1}"
            deck = self.load_deck_from_excel(
                workbook_path=workbook_path,
                sheet_name=sheet_name,
                screen_name=screen_name,
                deck_name=deck_name,
            )
            decks.append(deck)

        return decks

    def get_deck_data(self, deck_id: int) -> pd.DataFrame:
        """
        Extract grid data for a specific deck.

        Args:
            deck_id: ID of the deck to extract

        Returns:
            DataFrame with grid data
        """
        # Query all grid cells for the deck
        grid_cells = (
            self.session.query(DeckGrid)
            .filter(DeckGrid.deck_id == deck_id)
            .order_by(DeckGrid.row, DeckGrid.col)
            .all()
        )

        if not grid_cells:
            return pd.DataFrame()

        # Convert to DataFrame
        data = []
        for cell in grid_cells:
            data.append({
                "row": cell.row,
                "col": cell.col,
                "value": cell.value if cell.value is not None else cell.label,
            })

        df = pd.DataFrame(data)

        # Pivot to grid format
        if not df.empty:
            grid_df = df.pivot(index="row", columns="col", values="value")
            return grid_df
        return df
