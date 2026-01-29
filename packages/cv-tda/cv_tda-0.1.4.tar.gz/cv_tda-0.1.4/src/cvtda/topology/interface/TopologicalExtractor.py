import abc
import typing

import numpy
import gtda.diagrams

import cvtda.logging
import cvtda.dumping

from .. import utils
from .Extractor import Extractor
from ..DiagramVectorizer import DiagramVectorizer

class TopologicalExtractor(Extractor, abc.ABC):
    def __init__(
        self,
        enabled: bool,
        vectorizer_settings: DiagramVectorizer.Settings,
        supports_rgb: bool,
        n_jobs: int = -1,
        return_diagrams: bool = False,
        only_get_from_dump: bool = False,
        topo_only_get_from_dump: bool = False,
        **kwargs
    ):
        super().__init__(
            n_jobs = n_jobs,
            return_diagrams = return_diagrams,
            only_get_from_dump = False,
            topo_only_get_from_dump = (topo_only_get_from_dump or only_get_from_dump),
            **kwargs
        )

        self.topo_only_get_from_dump_ = (topo_only_get_from_dump or only_get_from_dump)
        self.return_diagrams_ = return_diagrams
        self.supports_rgb_ = supports_rgb

        self.enabled_ = enabled
        self.vectorizer_ = DiagramVectorizer(n_jobs = self.n_jobs_, settings = vectorizer_settings)
        self.scaler_ = gtda.diagrams.Scaler(n_jobs = self.n_jobs_, function = lambda x: numpy.max(x))


    def final_dump_name_(self, dump_name: typing.Optional[str] = None):
        # Disable taking the final dump in Extractor. We need to process reading from dump here (to apply Scaler, e.g.)!
        return None
    
    def diagrams_dump_(self, dump_name: typing.Optional[str]):
        return cvtda.dumping.dump_name_concat(dump_name, "diagrams")
    
    def force_numpy_(self):
        return not self.return_diagrams_
    
    def nothing_(self, num_objects: int):
        return [] if self.return_diagrams_ else numpy.empty((num_objects, 0))


    def process_rgb_(self, rgb_images: numpy.ndarray, do_fit: bool, dump_name: typing.Optional[str] = None):
        if not self.supports_rgb_:
            return self.nothing_(len(rgb_images))
        return self.do_work_(rgb_images, do_fit, dump_name)

    def feature_names_rgb_(self) -> typing.List[str]:
        if not self.supports_rgb_ or not self.enabled_:
            return []
        return self.vectorizer_.feature_names()

    def process_gray_(self, gray_images: numpy.ndarray, do_fit: bool, dump_name: typing.Optional[str] = None):
        return self.do_work_(gray_images, do_fit, dump_name)
    
    def feature_names_gray_(self) -> typing.List[str]:
        if not self.enabled_:
            return []
        return self.vectorizer_.feature_names()

    def do_work_(self, images: numpy.ndarray, do_fit: bool, dump_name: typing.Optional[str] = None):
        if not self.enabled_:
            return self.nothing_(len(images))

        if self.topo_only_get_from_dump_:
            if self.return_diagrams_:
                diagrams = cvtda.dumping.dumper().get_dump(self.diagrams_dump_(dump_name))
                cvtda.logging.logger().print("Applying Scaler to persistence diagrams.")
                return utils.process_iter(self.scaler_, diagrams, do_fit)
            else:
                return cvtda.dumping.dumper().get_dump(self.features_dump_(dump_name))

        diagrams = self.get_diagrams_(images, do_fit, dump_name)
        cvtda.logging.logger().print("Applying Scaler to persistence diagrams.")
        diagrams = numpy.nan_to_num(utils.process_iter(self.scaler_, diagrams, do_fit), 0)
        if self.return_diagrams_:
            return diagrams
        features = utils.process_iter_dump(self.vectorizer_, diagrams, do_fit, self.features_dump_(dump_name))
        assert features.shape == (len(images), len(self.vectorizer_.feature_names()))
        return features
    
    @abc.abstractmethod
    def get_diagrams_(self, images: numpy.ndarray, do_fit: bool, dump_name: typing.Optional[str] = None):
        pass
