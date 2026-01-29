#!/usr/bin/env python3
# coding: utf-8

import os
import re
import sys

from sphinx.ext import autodoc

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))

# Read version from pyproject.toml
_pyproject_path = os.path.join(os.path.dirname(__file__), os.pardir, 'pyproject.toml')
_version = None

try:
    # Try using tomllib (Python 3.11+)
    import tomllib
    with open(_pyproject_path, 'rb') as f:
        _pyproject_data = tomllib.load(f)
        _version = _pyproject_data['project']['version']
except ModuleNotFoundError:
    # Fallback to regex parsing for Python < 3.11
    pass
except (FileNotFoundError, KeyError):
    # File doesn't exist or version key missing, try regex fallback
    pass

# Use regex fallback if tomllib is not available or failed
if _version is None:
    try:
        with open(_pyproject_path, 'r', encoding='utf-8') as f:
            content = f.read()
            match = re.search(r'^version\s*=\s*["\']([^"\'\n\r]+)["\']', content, re.MULTILINE)
            if match:
                _version = match.group(1)
            else:
                raise RuntimeError("Could not extract version from pyproject.toml using regex")
    except FileNotFoundError:
        raise RuntimeError(f"pyproject.toml not found at {_pyproject_path}. Ensure you are running from the docs directory.")

# Final safety check
if _version is None:
    raise RuntimeError("Failed to extract version from pyproject.toml")

extensions = [
    'sphinx.ext.autodoc',
]

# Mock imports for dependencies not needed for documentation
autodoc_mock_imports = [
    'cairocffi',
    'flask',
    'pyparsing',
    'structlog',
    'tzlocal',
    'werkzeug',
    'yaml',
    'packaging',
]

templates_path = ['_templates']

source_suffix = {
    '.rst': 'restructuredtext',
}

root_doc = 'index'

project = 'Graphite-Render'
copyright = u'2014, Bruno Renié'

version = _version
release = _version

exclude_patterns = ['_build']

pygments_style = 'sphinx'

html_theme = 'alabaster'

htmlhelp_basename = 'Graphite-Renderdoc'

latex_elements = {
}

latex_documents = [
    ('index', 'Graphite-Render.tex', 'Graphite-Render Documentation',
     'Bruno Renié', 'manual'),
]

man_pages = [
    ('index', 'graphite-render', 'Graphite-Render Documentation',
     ['Bruno Renié'], 1)
]

texinfo_documents = [
    ('index', 'Graphite-Render', 'Graphite-Render Documentation',
     'Bruno Renié', 'Graphite-Render', 'One line description of project.',
     'Miscellaneous'),
]


class RenderFunctionDocumenter(autodoc.FunctionDocumenter):
    priority = 10

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        return autodoc.FunctionDocumenter.can_document_member(
            member, membername, isattr, parent
        ) and parent.name == 'graphite_render.functions'

    def format_args(self):
        args = super(RenderFunctionDocumenter, self).format_args()
        if args is not None:
            return re.sub('requestContext, ', '', args)


suppress_warnings = ['app.add_directive', 'autodoc.import_object']


def setup(app):
    app.add_autodocumenter(RenderFunctionDocumenter)


add_module_names = False
