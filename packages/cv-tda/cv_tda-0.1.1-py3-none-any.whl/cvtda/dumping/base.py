import abc
import typing

T = typing.TypeVar("T")

class BaseDumper(abc.ABC, typing.Generic[T]):
    current_dumper = None
    
    def __enter__(self):
        self.__previous = BaseDumper.current_dumper
        BaseDumper.current_dumper = self
        return self

    def __exit__(self, *args):
        BaseDumper.current_dumper = self.__previous

    @abc.abstractmethod
    def execute(self, function: typing.Callable[[typing.Any], T], name: str, *function_args) -> T:
        pass

    @abc.abstractmethod
    def save_dump(self, data: T, name: str):
        pass

    @abc.abstractmethod
    def has_dump(self, name: str) -> bool:
        pass

    def get_dump(self, name: str) -> T:
        assert self.has_dump(name), f"There is no dump at {name}"
        return self.get_dump_impl_(name)
    
    @abc.abstractmethod
    def get_dump_impl_(self, name: str) -> T:
        pass
