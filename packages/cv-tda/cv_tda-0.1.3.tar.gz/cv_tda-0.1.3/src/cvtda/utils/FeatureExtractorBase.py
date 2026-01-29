import abc
import typing
import inspect
import dataclasses

import sklearn.base

class FeatureExtractorBase(sklearn.base.TransformerMixin, abc.ABC):
    @dataclasses.dataclass(frozen = True)
    class Presets:
        full: object
        reduced: object
        quick: object

    PRESETS: Presets = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if 'settings' not in inspect.signature(cls.__init__).parameters.keys():
            return
        if cls.PRESETS is None:
            raise TypeError(f"{cls.__name__} must define PRESETS")
        if not isinstance(cls.PRESETS, FeatureExtractorBase.Presets):
            raise TypeError(f"{cls.__name__} must be an instance of Presets")


    def nest_feature_names(self, prefix: str, names: typing.List[str]) -> typing.List[str]:
        return [ f"{prefix} -> {name}" for name in names ]

    @abc.abstractmethod
    def feature_names(self) -> typing.List[str]:
        pass
