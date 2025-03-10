"""Type compatibility module for Python 3.8 support."""

from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Set, Tuple, TypeVar

# Type aliases for better readability and consistency
GenericList = List
GenericDict = Dict
GenericSet = Set
GenericTuple = Tuple
GenericCallable = Callable


def _is_generic_alias(obj: Any) -> bool:
    """Check if an object is a generic alias type."""
    return hasattr(obj, "__origin__") and hasattr(obj, "__args__")


T = TypeVar("T")
PathGenerator = Generator[Path, None, None]
