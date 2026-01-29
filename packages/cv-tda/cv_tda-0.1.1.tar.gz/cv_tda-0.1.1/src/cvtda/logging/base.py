import abc
import typing

T = typing.TypeVar("T")

class BaseLogger(abc.ABC):
    current_logger = None
    
    def __enter__(self):
        self.__previous = BaseLogger.current_logger
        BaseLogger.current_logger = self
        return self

    def __exit__(self, *args):
        BaseLogger.current_logger = self.__previous

    @abc.abstractmethod
    def verbosity(self) -> int:
        pass

    @abc.abstractmethod
    def print(self, data: T, *args) -> None:
        pass

    @abc.abstractmethod
    def pbar(
        self,
        data: typing.Iterable[T],
        total: typing.Optional[int] = None,
        desc: typing.Optional[str] = None
    ) -> typing.Iterable[T]:
        pass

    @abc.abstractmethod
    def zip(
        self,
        *iterables, 
        desc: typing.Optional[str] = None
    ):
        pass

    @abc.abstractmethod
    def set_pbar_postfix(self, pbar: typing.Any, data: dict):
        pass
