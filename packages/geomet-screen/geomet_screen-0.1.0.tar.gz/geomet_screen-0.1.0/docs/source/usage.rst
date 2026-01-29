Usage Guide
===========

Loading Screen Decks
---------------------

Screen decks are loaded from Excel workbooks where each sheet represents one deck.
A screen can have multiple decks.

Basic Usage
~~~~~~~~~~~

.. code-block:: python

   from geomet.screen import DatabaseConnection, ExcelLoader

   # Initialize database
   db = DatabaseConnection("screen_data.db")
   db.create_tables()

   # Create loader
   loader = ExcelLoader(db.get_session())

   # Load a single deck
   deck = loader.load_deck_from_excel(
       workbook_path="my_screen.xlsx",
       sheet_name="Deck1",
       screen_name="Screen_A",
       deck_name="Deck_1",
   )

Loading Multiple Decks
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Load all decks from a workbook
   decks = loader.load_screen_from_workbook(
       workbook_path="my_screen.xlsx",
       screen_name="Screen_A",
   )

Querying Deck Data
------------------

Extract grid data for visualization:

.. code-block:: python

   # Get deck data as DataFrame
   grid_df = loader.get_deck_data(deck.id)
   print(grid_df)

Visualization
-------------

Create plotly visualizations:

.. code-block:: python

   from geomet.screen import plot_deck_grid

   fig = plot_deck_grid(
       grid_df,
       title="My Screen Deck",
       colorscale="Viridis",
   )
   fig.show()

Save to file:

.. code-block:: python

   from geomet.screen import save_deck_plot

   save_deck_plot(
       grid_df,
       output_path="deck_plot.png",
       title="My Screen Deck",
   )
