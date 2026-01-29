geomet-screen Documentation
============================

Tools for screen deck layouts, wear monitoring and partition models.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   usage
   yaml_spec
   auto_examples/index
   api

Installation
------------

Install using pip or uv:

.. code-block:: bash

   pip install geomet-screen

Or with development dependencies:

.. code-block:: bash

   pip install geomet-screen[dev,docs]

Quick Start
-----------

Load a screen deck from an Excel workbook:

.. code-block:: python

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

Visualize the deck:

.. code-block:: python

   from geomet.screen import plot_deck_grid

   # Get deck data
   grid_df = loader.get_deck_data(deck.id)

   # Create plot
   fig = plot_deck_grid(grid_df, title="Screen Deck Layout")
   fig.show()

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
