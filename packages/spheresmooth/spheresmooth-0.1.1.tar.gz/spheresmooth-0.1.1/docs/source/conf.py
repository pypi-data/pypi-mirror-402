import os
import sys
sys.path.insert(0, os.path.abspath('../../'))

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'spheresmooth'
copyright = '2025, Lee Seyoung'
author = 'Lee Seyoung'
release = '0.1.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon', 
    'sphinx.ext.autosummary',
    "sphinx_gallery.gen_gallery",
]

autosummary_generate = True

templates_path = ['_templates']
exclude_patterns = []

language = 'python'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "pydata_sphinx_theme"
html_theme_options = {
    "show_prev_next": False,
    "navbar_end": ["theme-switcher", "navbar-icon-links"],
}
html_static_path = ['_static']
html_baseurl = "https://seyoung-230.github.io/spheresmooth-python/"

napoleon_numpy_docstring = True

sphinx_gallery_conf = {
    "examples_dirs": "gallery",          
    "gallery_dirs": "auto_examples",
    "filename_pattern": r".*",
    'run_stale_examples': True,
    "capture_repr": ("_repr_html_",),    
}