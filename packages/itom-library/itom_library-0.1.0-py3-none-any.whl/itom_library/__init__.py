"""
ITOM Library - A Python client library for IT Operations Management tools.

This library provides a simple interface to interact with:
- OpenText Operations Orchestration (OO)
"""

from itom_library.oo_client import OOClient
from itom_library.utilities import format_table, print_table

__version__ = "0.1.0"

__all__ = ["OOClient", "format_table", "print_table", "__version__"]
