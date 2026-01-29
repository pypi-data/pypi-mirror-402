# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys

sys.path.insert(0, os.path.abspath("../"))

project = "gmtorch_pse"
copyright = "2025, Maximilian Steinle, " "Robin Smolenski, Sebastian Roll, " "Michael Wollensak, Gero Paul Maier"
author = "Maximilian Steinle," "Robin Smolenski," "Sebastian Roll" "Michael Wollensak" "Gero Paul Maier"
release = "0.1.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["sphinx.ext.apidoc", "sphinx.ext.autodoc", "sphinx.ext.viewcode", "sphinx.ext.napoleon", "myst_parser"]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# autodoc_mock_imports = ['src._gaussian_mixture']
# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "pydata_sphinx_theme"
html_static_path = ["_static"]

html_theme_options = {
    "show_prev_next": True,
    "navigation_depth": 4,  # Wie tief die Navigation aufgeklappt werden kann
    "show_toc_level": 2,  # Zeigt Unterüberschriften in der rechten Leiste
    "collapse_navigation": False,
}

html_show_sourcelink = False

# Dies zwingt das Theme, die Navigation in der linken Sidebar anzuzeigen
html_sidebars = {"**": ["sidebar-nav-bs", "sidebar-ethical-ads"]}
