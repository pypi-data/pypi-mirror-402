"""
Utilities to help define/encode sorting options to pass @qnc/qnc_data_tables front-end
"""

from dataclasses import dataclass
from typing import Literal


@dataclass
class ColumnSort:
    column_key: str
    direction: Literal["forward", "reverse"]


@dataclass
class FunctionSort:
    function_key: str


def encode_sort(sort: ColumnSort | FunctionSort | None):
    """
    Intended to be used by your "render table manager" function if you are using @qnc/qnc_data_tables
    """
    if not sort:
        return None
    if isinstance(sort, ColumnSort):
        return dict(
            type="column",
            column_key=sort.column_key,
            direction=sort.direction,
        )
    return dict(
        type="function",
        function_key=sort.function_key,
    )
