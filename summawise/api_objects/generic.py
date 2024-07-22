from dataclasses import dataclass, asdict
from typing import  List, Set, Tuple, Iterable, Optional, Callable, TypeVar, ClassVar, Generic, Protocol
from datetime import datetime
from .. import utils
from ..errors import MultipleObjectsFoundError, MissingSortKeyError

@dataclass
class BaseApiObj:
    def to_dict(self) -> dict:
        obj = asdict(self)
        return utils.convert_datetimes(obj, converter = utils.converter_ts_int)

class ApiObjItem(Protocol):
    id: str
    name: str
    created_at: datetime

    def to_dict(self) -> dict:
        ...

AOT = TypeVar("AOT", bound = ApiObjItem)
T = TypeVar("T")

class ApiObjList(List[AOT], Generic[AOT]):

    API_OBJ_PREFIXES: ClassVar[Set[str]] = {"asst", "thread"}

    def __init__(
        self, 
        items: Iterable[AOT] = [], 
        sort: bool = False,
        key: Optional[Callable[[AOT], T]] = None,
        reverse: bool = False,
        cls: Optional[Callable[..., AOT]] = None,
    ):  
        self._cls = cls

        if not sort:
            # sort by "created_at" by default
            items = sorted(items, key=lambda item: item.created_at)  # type: ignore
            super().__init__(items) # type: ignore
            return

        if not key or not callable(key):
            raise MissingSortKeyError(f"Can't initialize '{self.class_name}' in sorted order without callable key.")

        sorted_items = sorted(items, key=key, reverse=reverse)  # type: ignore
        super().__init__(sorted_items)

    def to_dict_list(self) -> List[dict]:
        return [item.to_dict() for item in self]  # type: ignore

    @staticmethod
    def from_dict_list(objects: List[dict], cls: Callable[..., AOT], **kwargs) -> "ApiObjList[AOT]":
        items = [cls(**obj) for obj in objects]
        return ApiObjList(items, cls = cls, **kwargs)

    def list_by_name(self, name: str, case_sensitive: bool = False) -> List[T]:
        t = lambda s: s if case_sensitive else s.lower()  # transform func
        return [item for item in self if t(item.name) == t(name)]  # type: ignore

    def get_by_name(self, name: str, default: Optional[T] = None, case_sensitive: bool = False) -> Optional[T]:
        items = self.list_by_name(name, case_sensitive=case_sensitive)
        if len(items) == 0:
            return default
        if len(items) > 1:
            assert self._cls
            raise MultipleObjectsFoundError(self.class_name, "name", name)
        return items[0]

    def get_by_id(self, id: str) -> Tuple[Optional[AOT], int]:
        for idx, item in enumerate(self):
            if item.id == id:  # type: ignore
                return item, idx
        return None, -1
    
    def get(self, identifier: str) -> Tuple[Optional[AOT], int]:
        """
        Get an API object from an identifier.

        This method retrieves an item object based on the provided identifier. The identifier can be one of the following:
        - API ID: If the identifier string seems to be an API ID, it is treated as such and the item is retrieved using this ID.
        - Item name: If the identifier is a valid item name, the item is retrieved based on the name.
        - Menu ID: If the identifier is numeric, it retrieves the item associated with that number in the 'list' command. (index + 1)

        Parameters:
            identifier (str): The identifier used to retrieve the item.

        Returns:
            Tuple[Optional[AOT], int]: A tuple containing the retrieved API object representation and its index in the list of items. Returns (None, -1) if not found.
        """
        idx = -1

        if any(identifier.startswith(f"{p}_") for p in ApiObjList.API_OBJ_PREFIXES):
            _, idx = self.get_by_id(identifier)
            if idx == -1:
                return None, -1

        if idx == -1:
            item = self.get_by_name(identifier)
            if item:
                _, idx = self.get_by_id(item.id)  # type: ignore

        if idx == -1:
            idx = utils.try_parse_int(identifier)
            idx = -1 if idx is None else idx - 1

        if idx < 0 or idx > len(self) - 1:
            return None, -1

        item = self[idx]
        return item, idx
    
    @property
    def class_name(self):
        return self._cls.__name__ if self._cls else "Unknown"
