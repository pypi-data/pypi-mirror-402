from typing import override

class StrictlyStaticClass(type):
    """Metaclass that enforces strictly static.
    Any attempt to instantiate an object with a class using this metaclass will raise a `TypeError`.

    Examples:
        >>> class Constants(metaclass=StrictlyStaticClass):
        ...     PI = 3.14
        ...
        >>> Constants.PI
        3.14
        >>> Constants.PI = 3.14159
        TypeError: Class `Constants` is strictly static so it cannot be instantiated.
    """    


    @override
    def __call__(self):
        raise TypeError(
            f"Class `{self.__name__}` is strictly static so it cannot be instantiated."
        ) 
