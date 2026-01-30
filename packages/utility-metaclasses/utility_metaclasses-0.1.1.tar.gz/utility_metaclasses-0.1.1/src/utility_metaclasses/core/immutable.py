from typing import Any, override

class ImmutableClass(type):
    """Metaclass that enforces immutability at the class level.
    Any attempt to assign or modify attributes on a class using this
    metaclass will raise a `TypeError`.

    Examples:
        >>> class Constants(metaclass=ImmutableClass):
        ...     PI = 3.14
        ...
        >>> Constants.PI
        3.14
        >>> Constants.PI = 3.14159
        TypeError: Class `Constants` is immutable so members cannot be modified.
    """    

    @override
    def __setattr__(self, key: str, value: Any):
        """Disallow setting or modifying class attributes.

        Args:
            key: The name of the attribute being assigned.
            value: The value being assigned to the attribute.

        Raises:
            TypeError: Always raised to indicate that the class is immutable.
        """
        raise TypeError(
            f"Class `{self.__name__}` is immutable so members cannot be modified."
        )


class ImmutableInstance(type):
    """Metaclass that enforces immutability at the instance level.

    Any attempt to override the `__setattr__` method on the class,  
    assign or modify attributes on a instance using this metaclass 
    will raise a `TypeError`.
     
    Examples:
        >>> class Config(metaclass=ImmutableInstance):
        ...     def __init__(self, ip: str, port: int):
        ...         self.ip = ip 
        ...         self.port = port
        ...
        >>> conf = Config("local", 4242) 
        >>>
        >>> f"{conf.ip}:{conf.port}" 
        'local:4242'
        >>> conf.port = 6000
        TypeError: Instances of `Config` are immutable so members cannot
        be modified after instantation
    """
    @override
    def __new__(
        metacls: type[ImmutableInstance],
        name: str,
        bases: tuple[type, ...],
        namespaces: dict[str, Any]
    ) -> ImmutableInstance:
        """Overrides the creations process of a class
        
        It enforces the followings when use the metaclass:
            - If the class has `__setattr__`, it raises `TypeError`
            - If the class's instances try to use modify members, it raises `TypeError` 
        """
        if "__setattr__" in namespaces:
            raise TypeError(
                f"Instances of `{name}` are immutable so {name}.__setattr__() method cannot be overriden."
            )

        original_init = namespaces.get("__init__")
        def __new_init__(self: object, *args: Any, **kwargs: Any):
            """
            A wrapper around the original `__init__` method that introduces an
            internal flag, `__allow_setattr`, used to control attribute assignment
            during instance initialization.

            Explanation:
                In Python, attribute assignments inside `__init__` are performed
                via `__setattr__`. However, `__setattr__` has no intrinsic way
                to distinguish whether it is being invoked during object
                initialization or via a direct assignment after construction
                (e.g. `obj.x = 20`).

                If `__setattr__` were overridden to unconditionally raise
                `TypeError`, instance construction itself would fail because
                `__init__` relies on `__setattr__` to initialize attributes.

                To address this, the special flag `__allow_setattr` is temporarily
                set to `True` while `__init__` is executing. When `__setattr__`
                is called:
                    - If `__allow_setattr` is `True`, attribute assignment is
                      permitted, indicating that the call originates from
                      `__init__`.
                    - If `__allow_setattr` is `False`, attribute assignment is
                      disallowed, and `TypeError` is raised, indicating a mutation
                      attempt after initialization.
            """
            self._allow_setattr_ = True  # pyright: ignore[reportAttributeAccessIssue] 

            if original_init is not None:
                original_init(self, *args, **kwargs)
            else:
                # Respect MRO if no __init__ is defined
                super(type(self), self).__init__(*args, **kwargs)
            
            self._allow_setattr_ = False # pyright: ignore[reportAttributeAccessIssue]

        ALLOW_SETATTR_KEY_NAME = "_allow_setattr_"
        
        original_setattr = namespaces.get("__setattr__")
        def use_original_setattr(self: object, key: str, value: Any):
            """Helper function to make sure MRO is respected"""
            if original_setattr is not None:
                original_setattr(self, key, value)
            else: 
                super(type(self), self).__setattr__(key, value)
            
        def __new__setattr__(self: object, key: str, value: Any):
            """
            A guarded replacement for `__setattr__` that enforces instance immutability
            after object initialization.

            This method allows attribute assignment only under the following
            conditions:
                1. The attribute being assigned is the internal control flag
                   `__allow_setattr` itself.
                2. The internal flag `__allow_setattr` is set to `True`, indicating
                   that the assignment occurs during `__init__`.

            In all other cases, attribute mutation is disallowed and a `TypeError`
            is raised, preventing modification of instance state after
            initialization.
            """

            # If __setattr__ is called to set the internal flag 
            # or is called to set attributes inside __init__ (the flag is True)
            if (
                key == ALLOW_SETATTR_KEY_NAME
                or getattr(self, ALLOW_SETATTR_KEY_NAME)
            ):
                use_original_setattr(self, key, value)
                return 
            
            # Other cases
            raise TypeError(
                f"Instances of `{name}` are immutable so members cannot be modified after instantation"
            )
        
        # Add the internal flag to the slots so it works for slots 
        if "__slots__" in namespaces:
            namespaces["__slots__"].append(ALLOW_SETATTR_KEY_NAME) 

        namespaces["__init__"] = __new_init__ 
        namespaces["__setattr__"] = __new__setattr__

        return type.__new__(metacls, name, bases, namespaces)
