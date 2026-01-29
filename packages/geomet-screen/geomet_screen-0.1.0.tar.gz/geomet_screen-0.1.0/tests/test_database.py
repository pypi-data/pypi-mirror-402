"""Tests for database module."""

import pytest
import tempfile
from pathlib import Path

from geomet.screen.database import DatabaseConnection
from geomet.screen.models import ScreenDeck, DeckGrid


def test_database_connection_memory():
    """Test in-memory database connection."""
    db = DatabaseConnection()
    db.create_tables()
    
    session = db.get_session()
    assert session is not None
    
    session.close()
    db.close()


def test_database_connection_file():
    """Test file-based database connection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = DatabaseConnection(str(db_path))
        db.create_tables()
        
        assert db_path.exists()
        
        session = db.get_session()
        assert session is not None
        
        session.close()
        db.close()


def test_create_screen_deck():
    """Test creating a ScreenDeck record."""
    db = DatabaseConnection()
    db.create_tables()
    session = db.get_session()
    
    deck = ScreenDeck(
        screen_name="TestScreen",
        deck_name="TestDeck",
        workbook_path="test.xlsx",
        sheet_name="Sheet1",
    )
    session.add(deck)
    session.commit()
    
    # Query back
    result = session.query(ScreenDeck).first()
    assert result is not None
    assert result.screen_name == "TestScreen"
    assert result.deck_name == "TestDeck"
    
    session.close()
    db.close()


def test_create_deck_grid():
    """Test creating DeckGrid records."""
    db = DatabaseConnection()
    db.create_tables()
    session = db.get_session()
    
    # Create deck
    deck = ScreenDeck(
        screen_name="TestScreen",
        deck_name="TestDeck",
        workbook_path="test.xlsx",
        sheet_name="Sheet1",
    )
    session.add(deck)
    session.commit()
    
    # Create grid cells
    for i in range(3):
        for j in range(3):
            cell = DeckGrid(
                deck_id=deck.id,
                row=i,
                col=j,
                value=float(i * 3 + j),
            )
            session.add(cell)
    session.commit()
    
    # Query back
    cells = session.query(DeckGrid).filter(DeckGrid.deck_id == deck.id).all()
    assert len(cells) == 9
    
    session.close()
    db.close()


def test_relationship():
    """Test relationship between ScreenDeck and DeckGrid."""
    db = DatabaseConnection()
    db.create_tables()
    session = db.get_session()
    
    deck = ScreenDeck(
        screen_name="TestScreen",
        deck_name="TestDeck",
        workbook_path="test.xlsx",
        sheet_name="Sheet1",
    )
    session.add(deck)
    session.commit()
    
    # Add grid cells
    for i in range(2):
        cell = DeckGrid(deck_id=deck.id, row=i, col=0, value=float(i))
        session.add(cell)
    session.commit()
    
    # Access via relationship
    deck_from_db = session.query(ScreenDeck).first()
    assert len(deck_from_db.grid_cells) == 2
    
    session.close()
    db.close()
