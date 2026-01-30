# Configuration file for the Sphinx documentation builder.

import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.abspath('..'))


from sphinx_gallery.scrapers import matplotlib_scraper
from plotly.io._sg_scraper import plotly_sg_scraper

# -- Project information -----------------------------------------------------

project = 'geomet-screen'
copyright = '2026, Elphick Consulting'
author = 'Elphick Consulting'
release = '0.1.1'

# -- General configuration ---------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx_gallery.gen_gallery',
]

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------

html_theme = 'sphinx_book_theme'
html_static_path = ['_static']
html_logo = "_static/logo.png" # Top‑left logo
html_favicon = "_static/logo.png" # Browser tab icon (optional, Sphinx 1.8+)

html_theme_options = {
    "repository_url": "https://github.com/elphick-consulting/geomet-screen",
    "use_repository_button": True,
    "logo": {
        "image_light": "_static/logo.png",
        "image_dark": "_static/logo.png",
        "alt_text": "geomet-screen logo",
        "text": f"geomet-screen<br>({release})",  # shows version in the top-left

    },
}


# -- Sphinx Gallery configuration --------------------------------------------

sphinx_gallery_conf = {
    'examples_dirs': '../examples',   # path to example scripts
    'gallery_dirs': 'auto_examples',     # path to gallery generated output
    'filename_pattern': r'.*',  # run all examples
    'ignore_pattern': r'/__.*\.py$|/_.*\.py$|plot_deck_grid',  # Ignore files starting with _ or __
    'matplotlib_animations': False,
    'image_scrapers': (matplotlib_scraper, plotly_sg_scraper),
    'default_thumb_file': None,
    'capture_repr': ('_repr_html_',),  # Capture HTML representations (for plotly)
}
