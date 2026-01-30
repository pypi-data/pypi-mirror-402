from .static import StrictlyStaticClass 
from .immutable import ( 
    ImmutableClass,
    ImmutableInstance
)

class Combine(type):
    """A container to combine classes. Make it easy to use metaclasses

    Example:
        ```python
        class Foo(metaclass=Combine[ImmutableClass, ImmutableInstance]):
            pass
        ```
    """
    @classmethod
    def __class_getitem__(cls, bases: type | tuple[type, ...]):
        if not isinstance(bases, tuple):
            bases = (bases,)

        name = "Combine[" + ", ".join(b.__name__ for b in bases) + "]"
        return type(name, bases, {})

__all__ = [
    "StrictlyStaticClass",
    "ImmutableClass",
    "ImmutableInstance",
    "Combine"
]
