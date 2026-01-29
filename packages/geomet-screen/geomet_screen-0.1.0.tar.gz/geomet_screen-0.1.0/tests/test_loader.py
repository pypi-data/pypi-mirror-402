"""Tests for Excel loader."""

import pytest
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np

from geomet.screen.database import DatabaseConnection, ExcelLoader
from geomet.screen.models import ScreenDeck, DeckGrid


@pytest.fixture
def sample_workbook():
    """Create a sample Excel workbook for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workbook_path = Path(tmpdir) / "test_screen.xlsx"
        
        # Create sample data
        deck1_data = pd.DataFrame([
            [10.5, 12.3, 11.8],
            [9.8, 11.5, 10.2],
            [11.2, 10.8, 12.5],
        ])
        
        deck2_data = pd.DataFrame([
            [15.2, 16.8],
            [14.9, 15.7],
        ])
        
        # Write to Excel
        with pd.ExcelWriter(workbook_path, engine='openpyxl') as writer:
            deck1_data.to_excel(writer, sheet_name='Deck1', header=False, index=False)
            deck2_data.to_excel(writer, sheet_name='Deck2', header=False, index=False)
        
        yield str(workbook_path)


@pytest.fixture
def db_session():
    """Create a database session for testing."""
    db = DatabaseConnection()
    db.create_tables()
    session = db.get_session()
    yield session
    session.close()
    db.close()


def test_load_deck_from_excel(sample_workbook, db_session):
    """Test loading a single deck from Excel."""
    loader = ExcelLoader(db_session)
    
    deck = loader.load_deck_from_excel(
        workbook_path=sample_workbook,
        sheet_name='Deck1',
        screen_name='TestScreen',
        deck_name='TestDeck1',
    )
    
    assert deck is not None
    assert deck.screen_name == 'TestScreen'
    assert deck.deck_name == 'TestDeck1'
    assert deck.sheet_name == 'Deck1'
    assert len(deck.grid_cells) == 9  # 3x3 grid


def test_load_screen_from_workbook(sample_workbook, db_session):
    """Test loading all decks from a workbook."""
    loader = ExcelLoader(db_session)
    
    decks = loader.load_screen_from_workbook(
        workbook_path=sample_workbook,
        screen_name='TestScreen',
    )
    
    assert len(decks) == 2
    assert all(deck.screen_name == 'TestScreen' for deck in decks)


def test_get_deck_data(sample_workbook, db_session):
    """Test extracting deck data."""
    loader = ExcelLoader(db_session)
    
    deck = loader.load_deck_from_excel(
        workbook_path=sample_workbook,
        sheet_name='Deck1',
        screen_name='TestScreen',
        deck_name='TestDeck1',
    )
    
    grid_df = loader.get_deck_data(deck.id)
    
    assert grid_df is not None
    assert grid_df.shape == (3, 3)
    assert not grid_df.empty


def test_get_deck_data_empty(db_session):
    """Test extracting data for non-existent deck."""
    loader = ExcelLoader(db_session)
    
    grid_df = loader.get_deck_data(999)
    
    assert grid_df.empty


def test_load_specific_sheets(sample_workbook, db_session):
    """Test loading specific sheets from workbook."""
    loader = ExcelLoader(db_session)
    
    decks = loader.load_screen_from_workbook(
        workbook_path=sample_workbook,
        screen_name='TestScreen',
        sheet_names=['Deck1'],
    )
    
    assert len(decks) == 1
    assert decks[0].sheet_name == 'Deck1'
