from typing import Callable, Dict, Coroutine, Any
from malevich_app.export.secondary.collection.Collection import Collection


class ComputeCollection(Collection):
    def __init__(self, f: Callable[[Dict[str, str]], Coroutine[Any, Any, Collection]], is_optional: bool = False):
        self.__f = f
        self.__collection: Collection = None
        self.__is_optional = is_optional

    async def compute(self, collections: Dict[str, str]):
        self.__collection = await self.__f(collections)

    def get(self):
        if self.__is_optional:
            return self.__collection.get() if self.__collection is not None else None
        assert self.__collection is not None, "compute collection isn't ready"
        return self.__collection.get()

    def get_collection(self) -> Collection:
        assert self.__is_optional or self.__collection is not None, "compute collection isn't ready"
        return self.__collection

    def get_mode(self) -> str:
        return "not_check"
