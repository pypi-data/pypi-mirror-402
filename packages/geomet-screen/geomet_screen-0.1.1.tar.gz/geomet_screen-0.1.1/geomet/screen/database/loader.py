from pathlib import Path
from typing import List, Optional, Tuple, Any

import pandas as pd

from geomet.screen.models.deck import DeckSpec


class ExcelLoader:
    """Load screen deck layouts from Excel workbooks into DeckSpec models."""

    @staticmethod
    def _parse_cell_value(value: Any) -> Optional[str]:
        """Normalize a cell value into a panel ID string (or None for empty)."""
        if pd.isna(value):
            return None
        # Convert anything non\-NaN to string to use as a panel ID
        return str(value).strip() or None

    def load_deck_from_excel(
        self,
        workbook_path: str | Path,
        sheet_name: str,
        deck_name: str,
    ) -> DeckSpec:
        """Load a screen deck layout from an Excel sheet into a DeckSpec.

        Args:
            workbook_path: Path to the Excel workbook
            sheet_name: Name of the sheet containing the deck layout
            deck_name: Logical name for this deck

        Returns:
            DeckSpec instance with populated layout
        """
        workbook_path = Path(workbook_path)

        # Read the Excel sheet as raw grid (no header)
        df = pd.read_excel(workbook_path, sheet_name=sheet_name, header=None)

        # Build 2D layout of panel IDs (skip empty cells)
        layout: List[List[str]] = []
        for _, row in df.iterrows():
            row_ids: List[str] = []
            for _, raw_value in row.items():
                panel_id = self._parse_cell_value(raw_value)
                # Use empty string or skip entirely; here we keep explicit blanks
                row_ids.append(panel_id or "")
            layout.append(row_ids)

        rows = len(layout)
        cols = max((len(r) for r in layout), default=0)

        # Normalize rows to same length (pad with empty strings)
        normalized_layout: List[List[str]] = [
            r + ["" for _ in range(cols - len(r))] for r in layout
        ]

        deck_spec = DeckSpec(
            name=deck_name,
            rows=rows,
            cols=cols,
            layout=normalized_layout,
        )
        return deck_spec

    def load_screen_from_workbook(
        self,
        workbook_path: str | Path,
        screen_name: str,
        sheet_names: Optional[List[str]] = None,
    ) -> List[DeckSpec]:
        """Load all decks from a workbook (one sheet per deck) as DeckSpec objects."""
        workbook_path = Path(workbook_path)

        if sheet_names is None:
            excel_file = pd.ExcelFile(workbook_path)
            sheet_names = excel_file.sheet_names

        decks: List[DeckSpec] = []
        for index, sheet_name in enumerate(sheet_names, start=1):
            deck_name = f"{screen_name}_deck_{index}"
            deck = self.load_deck_from_excel(
                workbook_path=workbook_path,
                sheet_name=sheet_name,
                deck_name=deck_name,
            )
            decks.append(deck)

        return decks