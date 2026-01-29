from .static import StrictlyStatic
from .immutable import ( 
    ImmutableClass,
    ImmutableInstance
)

def Combine(*bases: type) -> type:
    """A function to combine classes. Make it easy to use metaclasses

    Example:
        ```python
        class MetaA(type):
            pass

        class MetaB(type):
            pass

        class Foo(metaclass=Combine(MetaA, MetaB)):
            pass
        ```
    """
    class _Combined(*bases): # pyright: ignore[reportUntypedBaseClass]
        pass

    _Combined.__name__ = (
        "Combine[" + ", ".join(base.__name__ for base in bases) + "]"
    )

    return _Combined

__all__ = [
    "StrictlyStatic",
    "ImmutableClass",
    "ImmutableInstance",
    "Combine"
]
