import abc
import typing

import numpy

import cvtda.utils
import cvtda.dumping
import cvtda.logging

from .. import utils

class Extractor(cvtda.utils.FeatureExtractorBase, abc.ABC):
    def __init__(self, n_jobs: int = -1, only_get_from_dump: bool = False, **kwargs):
        self.n_jobs_ = n_jobs
        self.only_get_from_dump_ = only_get_from_dump

        self.kwargs_ = kwargs
        self.kwargs_['n_jobs'] = n_jobs
        self.kwargs_['only_get_from_dump'] = only_get_from_dump

        self.fitted_ = False
        self.fit_dimensions_ = None
    

    def final_dump_name_(self, dump_name: typing.Optional[str] = None):
        return self.features_dump_(dump_name)
    
    def features_dump_(self, dump_name: typing.Optional[str]):
        return cvtda.dumping.dump_name_concat(dump_name, "features")
    
    def force_numpy_(self):
        return True
    

    def feature_names(self) -> typing.List[str]:
        if self.is_rgb_(self.fit_dimensions_):
            return [
                *self.nest_feature_names("rgb", self.feature_names_rgb_()),
                *self.nest_feature_names("gray", self.gray_extractor_.feature_names()),
                *self.nest_feature_names("red", self.red_extractor_.feature_names()),
                *self.nest_feature_names("green", self.green_extractor_.feature_names()),
                *self.nest_feature_names("blue", self.blue_extractor_.feature_names())
            ]
        else:
            return self.feature_names_gray_()

    def fit(self, images: numpy.ndarray, dump_name: typing.Optional[str] = None):
        self.fit_transform(images, dump_name)
        return self
    
    def transform(self, images: numpy.ndarray, dump_name: typing.Optional[str] = None):
        assert self.fitted_ is True, 'fit() must be called before transform()'
        return self.process_(images, do_fit = False, dump_name = dump_name)
    
    def fit_transform(self, images: numpy.ndarray, dump_name: typing.Optional[str] = None):
        result = self.process_(images, do_fit = True, dump_name = dump_name)
        self.fitted_ = True
        return result


    def is_rgb_(self, shape):
        return (len(shape) == 3) and (shape[2] == 3)

    def process_(self, images: numpy.ndarray, do_fit: bool, dump_name: typing.Optional[str] = None):
        if self.fit_dimensions_ is not None:
            assert self.fit_dimensions_ == images.shape[1:], \
                    f"The pipeline is fit for {self.fit_dimensions_}. Cannot use it with {images.shape}."
        self.fit_dimensions_ = images.shape[1:]

        final_dump = self.final_dump_name_(dump_name)
        if self.only_get_from_dump_ and not self.is_rgb_(self.fit_dimensions_):
            return cvtda.dumping.dumper().get_dump(final_dump)
        if not do_fit and cvtda.dumping.dumper().has_dump(final_dump):
            return cvtda.dumping.dumper().get_dump(final_dump)
        
        if self.is_rgb_(self.fit_dimensions_):
            cvtda.logging.logger().print("RGB images received. Transforming to grayscale.")

            rgb_dump = cvtda.dumping.dump_name_concat(dump_name, "rgb")
            gray_dump = cvtda.dumping.dump_name_concat(dump_name, "gray")
            red_dump = cvtda.dumping.dump_name_concat(dump_name, "red")
            green_dump = cvtda.dumping.dump_name_concat(dump_name, "green")
            blue_dump = cvtda.dumping.dump_name_concat(dump_name, "blue")

            if do_fit:
                self.gray_extractor_ = self.__class__(**self.kwargs_)
                self.red_extractor_ = self.__class__(**self.kwargs_)
                self.green_extractor_ = self.__class__(**self.kwargs_)
                self.blue_extractor_ = self.__class__(**self.kwargs_)

            if self.only_get_from_dump_:
                rgb_data = cvtda.dumping.dumper().get_dump(self.final_dump_name_(rgb_dump))
            else:
                rgb_data = self.process_rgb_(images, do_fit, rgb_dump)

            gray_images = cvtda.utils.rgb2gray(images, self.n_jobs_)
            result = [
                rgb_data,
                utils.process_iter(self.gray_extractor_, gray_images, do_fit, gray_dump),
                utils.process_iter(self.red_extractor_, images[:, :, :, 0], do_fit, red_dump),
                utils.process_iter(self.green_extractor_, images[:, :, :, 1], do_fit, green_dump),
                utils.process_iter(self.blue_extractor_, images[:, :, :, 2], do_fit, blue_dump),
            ]
        else:
            result = [ self.process_gray_(images, do_fit, dump_name) ]
        return utils.hstack(result, self.force_numpy_())

    @abc.abstractmethod
    def process_rgb_(self, rgb_images: numpy.ndarray, do_fit: bool, dump_name: typing.Optional[str] = None):
        pass
    
    @abc.abstractmethod
    def feature_names_rgb_(self) -> typing.List[str]:
        pass
    
    @abc.abstractmethod
    def process_gray_(self, gray_images: numpy.ndarray, do_fit: bool, dump_name: typing.Optional[str] = None):
        pass

    @abc.abstractmethod
    def feature_names_gray_(self) -> typing.List[str]:
        pass