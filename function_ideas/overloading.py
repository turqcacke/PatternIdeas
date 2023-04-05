from functools import wraps
from typing import Callable, Any, Dict, Tuple, Optional


def overload_register(class_type: Optional[str] = None, **types):
    """
    Implemntation of java like overloading with kwargs support.
    Does not support composite types like List, Dict etc.

    Usage:

    In class method for class C:
    @overload_register("C", a=str, b=int)
    def f(self, a: str, b: int):
        ...

    With function:
    @overload_register(a=str, b=int)
    def f(self, a: str, b: int):
        ...

    Args:
        class_type (Optional[str], optional): Name of the class which used for identifying class name.
        Defaults to None.
    """

    def register(function: Callable[..., Any]):
        function_name = function.__name__
        wrapped_f = overload_register._arg_registry.get(function_name)

        arg_names = tuple(types.keys())
        arg_types = tuple(types.values())

        if wrapped_f is None:

            @wraps(function)
            def wrapper(*args, **kwargs):
                args = list(args)
                self = (
                    args.pop(0)
                    if args and args[0].__class__.__name__ == class_type
                    else None
                )

                args_len = len(kwargs) + len(args)

                picked_types: Tuple[Any, ...] = tuple(
                    filter(
                        lambda types: len(types) == args_len
                        and False
                        not in (
                            args[i].__class__ == types[i] for i in range(0, len(args))
                        ),
                        wrapper._arg_types_registry.keys(),
                    )
                )

                type_key: Optional[Tuple[Any, ...]] = None

                for type in picked_types:
                    linked_names: Tuple[str, ...] = wrapper._arg_names_registry[type]
                    suitable_types_counter = 0

                    for arg_name, arg_value in kwargs.items():
                        arg_type = arg_value.__class__
                        type_index = linked_names.index(arg_name)

                        if arg_type == type[type_index]:
                            suitable_types_counter += 1

                    if suitable_types_counter == len(kwargs) and args_len == len(type):
                        type_key = type
                        break

                f = wrapper._arg_types_registry.get(type_key)

                if type_key == None or f == None:
                    raise NotImplementedError(
                        f"Function with signature {args} {kwargs} is not implemented yet."
                    )

                return f(self, *args, **kwargs) if self else f(*args, **kwargs)

            wrapper._arg_types_registry: Dict[Tuple[Any, ...], Callable[..., Any]] = {}
            wrapper._arg_names_registry: Dict[Tuple[Any, ...], Tuple[str, ...]] = {}
            wrapped_f = overload_register._arg_registry[function_name] = wrapper

        if arg_types in wrapped_f._arg_types_registry:
            raise RuntimeError(
                f"Function with signature {types} is already registered."
            )

        wrapped_f._arg_types_registry[arg_types] = function
        wrapped_f._arg_names_registry[arg_types] = arg_names

        return wrapped_f

    return register


overload_register._arg_registry: Dict[tuple, Dict[tuple, Callable[..., Any]]] = {}
