"""Screen deck data models."""

from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship

from geomet.screen.database.connection import Base


class ScreenDeck(Base):
    """Model for screen deck information."""

    __tablename__ = "screen_decks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    screen_name = Column(String, nullable=False)
    deck_name = Column(String, nullable=False)
    workbook_path = Column(String, nullable=False)
    sheet_name = Column(String, nullable=False)

    # Relationship to grid cells
    grid_cells = relationship("DeckGrid", back_populates="deck", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ScreenDeck(screen={self.screen_name}, deck={self.deck_name})>"


class DeckGrid(Base):
    """Model for screen deck grid cells."""

    __tablename__ = "deck_grids"

    id = Column(Integer, primary_key=True, autoincrement=True)
    deck_id = Column(Integer, ForeignKey("screen_decks.id"), nullable=False)
    row = Column(Integer, nullable=False)
    col = Column(Integer, nullable=False)
    value = Column(Float, nullable=True)
    label = Column(String, nullable=True)

    # Relationship to deck
    deck = relationship("ScreenDeck", back_populates="grid_cells")

    def __repr__(self):
        return f"<DeckGrid(row={self.row}, col={self.col}, value={self.value})>"
