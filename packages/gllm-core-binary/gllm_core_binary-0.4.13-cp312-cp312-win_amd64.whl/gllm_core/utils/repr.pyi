from _typeshed import Incomplete
from typing import Any, Generic, Iterable, TypeVar

MAX_PREVIEW_LENGTH: int
MAX_ITEMS_PREVIEW: int
T = TypeVar('T')

class _TruncatedIterable(Generic[T]):
    """Represents a truncated iterable with first and last elements visible.

    Attributes:
        items (Iterable[T]): The iterable to be truncated.
        max_items_preview (int): Maximum number of items to show before truncation.
    """
    items: Incomplete
    max_items_preview: Incomplete
    def __init__(self, items: Iterable[T], max_items_preview: int = ...) -> None:
        """Initialize a TruncatedIterable.

        Args:
            items (Iterable[T]): The iterable to be truncated.
            max_items_preview (int, optional): Maximum number of items to show before truncation.
                Defaults to MAX_ITEMS_PREVIEW.
        """

def get_value_repr(value: Any) -> Any:
    """Get the string representation of a value.

    Args:
        value (Any): The value to get the string representation of.

    Returns:
        Any: The string representation of the value.
    """
