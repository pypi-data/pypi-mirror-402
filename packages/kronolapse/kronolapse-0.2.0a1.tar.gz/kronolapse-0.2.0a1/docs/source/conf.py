# -*- mode: python -*-
# -*- coding: utf-8 -*-
#
# conf.py
#
# Configuration file for the Sphinx documentation builder.

import os
import sys
import tomllib
# import sphinx_rtd_theme

from datetime import datetime
from sphinx_pyproject import SphinxConfig

sys.path.insert(0, os.path.abspath('../../'))

config = SphinxConfig('../../pyproject.toml', globalns=globals())

with open('../../pyproject.toml', 'rb') as f:
    pyproject_data = tomllib.load(f)

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = config.name.capitalize()
author = config.author
release = version = config.version
description = config.description
description_es = 'Gestiona la exhibición de imágenes en un monitor de acuerdo a un cronograma y lapsos de tiempo'  # noqa
date_rls = datetime.now().timetuple()[0]
copyright = '2025-{}, {}'.format(date_rls, author)
authors = pyproject_data.get("project", {}).get("authors", [])
author_email = '{} <{}>'.format(authors[0]["name"], authors[0]["email"])

# Define substitutions to be available in all rst files
rst_epilog = """
.. |copyright_note| replace:: {copyright}
""".format(copyright=copyright)

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx_rtd_theme',
    'sphinx_copybutton',
    'myst_parser'
]

source_suffix = ['.rst', '.md']

suppress_warnings = ['myst.header']

templates_path = ['_templates']

language = 'es'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_static_path = ['_static']
html_theme = 'breeze'
html_title = 'Documentación de Kronolapse - {}'.format(version)
html_short_title = 'kronolapse'
html_logo = '_static/kronolapse-logo.svg'
html_favicon = '_static/favicon.ico'
html_last_updated_fmt = '%d %b %Y'
html_theme_options = {
    'header_tabs': False,
}
html_context = {
    'github_user': 'mikemolina',
    'github_repo': 'kronolapse',
    'github_version': 'main'
}
html_show_sphinx = True
html_show_copyright = True

# -- Options for LaTeX output --------------------------------------------

latex_elements = {
    'papersize': 'letterpaper',
    'pointsize': '11pt',
    'printindex': '\\begin{flushleft}\n\\printindex\n\\end{flushleft}',
    'tableofcontents': '\\pdfbookmark[0]{\\contentsname}{toc}\\sphinxtableofcontents',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass [howto|manual|own class]).
latex_documents = [(
    'index',
    'kronolapse.tex',
    project,
    author,
    'manual'
)]

# -- Options for manual page output ---------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    ('manpage',
     'kronolapse',
     description,
     [author_email],
     1),
    ('manpage_es',
     'kronolapse-es',
     description_es,
     [author_email],
     1)
]

# -- Options for Texinfo output -------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author, dir menu entry, description, category)
# texinfo_documents = [(
#     'readme',
#     'kronolapse',
#     project,
#     author,
#     'kronolapse',
#     description,
#     'Miscellaneous'
# )]
