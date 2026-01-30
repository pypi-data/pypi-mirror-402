"""
Utility functions for formatting and displaying data.
"""

from typing import Any

def format_table(data: Any, indent: int = 0) -> str:
    """
    Format data into a readable table-like string.

    Args:
        data: The data to format (dict, list, or primitive)
        indent: Current indentation level

    Returns:
        Formatted string representation

    Example:
        >>> data = {'name': 'Flow1', 'id': '123'}
        >>> print(format_table(data))
        ├── name: Flow1
        └── id: 123
    """
    lines = []
    prefix = "│   " * indent

    if isinstance(data, dict):
        items = list(data.items())
        for i, (key, value) in enumerate(items):
            is_last = i == len(items) - 1
            connector = "└── " if is_last else "├── "
            
            if isinstance(value, (dict, list)):
                lines.append(f"{prefix}{connector}{key}:")
                lines.append(format_table(value, indent + 1))
            else:
                lines.append(f"{prefix}{connector}{key}: {value}")
                
    elif isinstance(data, list):
        for i, item in enumerate(data):
            is_last = i == len(data) - 1
            connector = "└── " if is_last else "├── "
            
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}{connector}[{i}]:")
                lines.append(format_table(item, indent + 1))
            else:
                lines.append(f"{prefix}{connector}{item}")
    else:
        lines.append(f"{prefix}{data}")

    return "\n".join(lines)


def print_table(data: Any) -> None:
    """
    Print data in a formatted table-like structure.

    Args:
        data: The data to print

    Example:
        >>> data = {'flows': [{'name': 'Flow1'}, {'name': 'Flow2'}]}
        >>> print_table(data)
        ├── flows:
        │   ├── [0]:
        │   │   └── name: Flow1
        │   └── [1]:
        │   │   └── name: Flow2
    """
    print(format_table(data))
