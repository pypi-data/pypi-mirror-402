# geomet-screen

Tools for screen deck layouts, wear monitoring and partition models.

## Features

- **SQLAlchemy Database Integration**: SQLite-based database connection for managing screen deck layouts
- **Excel Data Loading**: Load screen deck layouts from Excel workbooks (one sheet per deck)
- **Data Models**: SQLAlchemy ORM models for screen decks and grid cells
- **Plotly Visualization**: Create interactive heatmap visualizations of deck grids
- **Kaleido Integration**: Export plots to static images (PNG, JPEG, SVG)
- **Sphinx Documentation**: Comprehensive documentation with Sphinx Book Theme
- **Sphinx Gallery**: Executable examples with automatic thumbnail generation
- **Comprehensive Tests**: Full test coverage using pytest

## Installation

```bash
pip install geomet-screen
```

For development:
```bash
git clone https://github.com/elphick-consulting/geomet-screen.git
cd geomet-screen
pip install -e ".[dev,docs]"
```

## Quick Start

### Load a Screen Deck from Excel

```python
from geomet.screen import DatabaseConnection, ExcelLoader

# Initialize database
db = DatabaseConnection("screen_data.db")
db.create_tables()

# Load deck from Excel
loader = ExcelLoader(db.get_session())
deck = loader.load_deck_from_excel(
    workbook_path="screen.xlsx",
    sheet_name="Deck1",
    screen_name="Screen_A",
    deck_name="Deck_1",
)
```

### Visualize the Deck

```python
from geomet.screen import plot_deck_grid

# Get deck data
grid_df = loader.get_deck_data(deck.id)

# Create plot
fig = plot_deck_grid(grid_df, title="Screen Deck Layout")
fig.show()
```

## Running Tests

```bash
pytest tests/
```

## Building Documentation

```bash
cd docs
make html
```

The documentation will be built in `docs/build/html/`.

## Project Structure

```
geomet-screen/
├── geomet_screen/          # Main package
│   ├── database/           # Database connection and Excel loader
│   ├── models/             # SQLAlchemy models
│   └── visualization.py    # Plotly visualization functions
├── tests/                  # Test suite
├── examples/               # Sphinx Gallery examples
├── docs/                   # Sphinx documentation
│   ├── source/             # Documentation source files
│   └── build/              # Generated documentation
└── pyproject.toml          # Project configuration
```

## Technologies Used

- **uv**: Modern Python package manager
- **SQLAlchemy**: SQL toolkit and ORM
- **pandas**: Data manipulation and analysis
- **openpyxl**: Excel file reading/writing
- **plotly**: Interactive plotting library
- **kaleido**: Static image export for plotly
- **Sphinx**: Documentation generator
- **sphinx-book-theme**: Beautiful book-style theme
- **sphinx-gallery**: Gallery of examples with thumbnails
- **pytest**: Testing framework

## License

See LICENSE file for details.
