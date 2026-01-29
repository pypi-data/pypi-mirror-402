from typing import override

class StrictlyStatic(type):
    @override
    def __call__(self):
        raise TypeError(
            f"Class `{self.__name__}` is strictly static so it cannot be instantiated."
        ) 
