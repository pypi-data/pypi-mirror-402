"""
textfsmgen.__init__
===================

Top-level module for the `textfsmgen` package.

This module initializes the package namespace and exposes the core
classes and utilities for generating and managing TextFSM templates.
It provides a unified entry point for pattern definitions, template
builders, and helper functions used in parsing structured text.

Notes
-----
Keeping all primary exports in `__init__.py` simplifies imports and
ensures a consistent public API for end-users.
"""

from textfsmgen.core import ParsedLine
from textfsmgen.core import TemplateBuilder
from textfsmgen.config import version
from textfsmgen.config import edition

__version__ = version
__edition__ = edition

__all__ = [
    'ParsedLine',
    'TemplateBuilder',
    'version',
    'edition',
]
