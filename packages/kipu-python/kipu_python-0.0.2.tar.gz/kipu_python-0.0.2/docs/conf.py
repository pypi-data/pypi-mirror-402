# -- Path setup --------------------------------------------------------------

import os
import sys
sys.path.insert(0, os.path.abspath('..'))

# -- Project information -----------------------------------------------------

project = 'kipu-python'
copyright = '2025, Rahulkumar010'
author = 'Rahulkumar010'

# -- General configuration ---------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'sphinx_autodoc_typehints',
    'sphinx.ext.coverage',
    'sphinx.ext.todo',
    'sphinx.ext.githubpages',
    'myst_parser',  # Parse markdown files natively!
]

# Napoleon settings for Google/NumPy style docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = True

# Intersphinx: refer to the standard library and major dependencies
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'pandas': ('https://pandas.pydata.org/pandas-docs/stable/', None),
    'numpy': ('https://numpy.org/doc/stable/', None)
}

# Show TODOs in output
todo_include_todos = True

# Automatically document type hints
set_type_checking_flag = True

# If you want to mock heavy/optional imports for autodoc
autodoc_mock_imports = ["aiohttp", "pandas", "numpy", "tqdm"]

# Exclude auto-generated and build files
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------

html_theme = 'sphinx_rtd_theme'

# -- MyST settings (for Markdown support) ------------------------------------

myst_enable_extensions = [
    "deflist",
    "fieldlist",
    "html_admonition",
    "html_image",
    "smartquotes",
    "replacements",
    "linkify",
    "substitution",
    "tasklist",
]