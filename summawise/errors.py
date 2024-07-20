from typing import Any, Union, Tuple, Optional

class NotSupportedError(Exception):
    def __init__(self, append: str = ""):
        msg = "Failed to vectorize data. Your input is not yet supported"
        msg += (": " if append else ".") + append
        super().__init__(msg)

class ValueTypeError(Exception):
    def __init__(self, value: Any, type_or_types: Union[type, Tuple[type, ...]]):
        _type: Optional[type] = None
        types: Tuple[type, ...] = ()

        if isinstance(type_or_types, tuple):
            types = type_or_types
        elif isinstance(type_or_types, type):
            _type = type_or_types
        else:
            raise TypeError("ValueTypeError 'type_or_types' must be a type, or a tuple of types.")

        msg: str = ""
        if _type is not None:
            msg = f"Expected value to be of type '{_type.__name__}', "
        elif len(types) > 0:
            types_str = " | ".join([_type.__name__ for _type in types])
            msg = f"Expected value to be of one of the types '{types_str}', "
        else:
            raise ValueError("At least one type must be specified when raising ValueTypeError.")

        msg += f"but instead received value of type '{type(value).__name__}': {value}"
        super().__init__(msg)

class MultipleObjectsFoundError(Exception):
    def __init__(self, name: str, condition: str, value: str):
        super().__init__(f"Multiple objects ({name}) found. (Condition: '{condition}', Value: '{value}')")

class MissingSortKeyError(Exception):
    def __init__(self, append = ""):
        msg = "Missing required sort key" + (": " if len(append) else ".") + append
        super().__init__(msg)

