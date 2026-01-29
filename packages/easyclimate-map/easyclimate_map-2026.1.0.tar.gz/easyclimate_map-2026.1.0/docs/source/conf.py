# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
import datetime
sys.path.insert(0, os.path.abspath("../../src"))
import easyclimate_map as eclmap

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'easyclimate-map'
copyright = f"2026-{datetime.datetime.now().year}, Shenyulu（深雨露） and easyclimate developers"
author = "shenyulu and easyclimate developers"
release = "v" + eclmap.__version__


# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx_gallery.gen_gallery",
    # Sphinx AutoAPI Method
    "autoapi.extension",
    # Links to documentation for other projects
    "sphinx.ext.intersphinx",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx_iconify",
    "sphinx_design",
    "sphinx_copybutton",
]

templates_path = ['_templates']
exclude_patterns = []

# -- Options for AutoAPI extension -------------------------------------------
autoapi_type = "python"
autoapi_dirs = ["../../src"]
autoapi_add_toctree_entry = False
autoapi_root = "technical/api"

# -- Options for autodoc/autosummary -----------------------------------------
autodoc_mock_imports = []
autosummary_generate = True

# -- Options for sphinx_iconify -----------------------------------------
iconify_script_url = ""

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'shibuya'
html_static_path = ['_static']
html_logo = "_static/easyclimate_map_logo_mini.png"

# settings for sphinx-gallery
sphinx_gallery_conf = {
    "examples_dirs": "./dynamic_docs",  # path to your example scripts
    "gallery_dirs": "./auto_gallery",  # path to where to save gallery generated output
    "image_scrapers": ("matplotlib",),
    "compress_images": (
        "images",
        "thumbnails",
    ),  # require install `optipng`, download from http://optipng.sourceforge.net/
    "line_numbers": False,  # Line number
    "promote_jupyter_magic": True,
    #  Controlling what output is captured
    "capture_repr": ("_repr_html_", "__repr__", "__str__"),
    "run_stale_examples": True,
    "min_reported_time": False,
    "download_all_examples": False,
    #  'show_memory': True,
    "show_signature": False,
    'remove_config_comments': True,
    # Modules for which function level galleries are created.  In
    # this case sphinx_gallery and numpy in a tuple of strings.
    "doc_module": "easyclimate_map",
    # Insert links to documentation of objects in the examples
    "reference_url": {"easyclimate_map": None},
    'parallel': 4,
    # mini-galleries
    ## directory where function/class granular galleries are stored
    'backreferences_dir'  : 'gen_modules/backreferences',
    ## Modules for which function/class level galleries are created. In
    ## this case sphinx_gallery and numpy in a tuple of strings.
    'doc_module'          : ('sphinx_gallery', 'easyclimate_map'),
    ## Regexes to match objects to exclude from implicit backreferences.
    ## The default option is an empty set, i.e. exclude nothing.
    ## To exclude everything, use: '.*'
    'exclude_implicit_doc': {r'pyplot\.show'},
}