import typing
import dataclasses

import numpy
import skimage.measure
import skimage.feature

import cvtda.utils
import cvtda.logging

from . import utils
from .interface import Extractor


class GrayGeometryExtractor(cvtda.utils.FeatureExtractorBase):
    @dataclasses.dataclass(frozen = True)
    class Settings:
        reduced_stats: bool = True

        daisy: bool = True
        sift: bool = True
        orb: bool = True
        hog: bool = True
        basic: bool = True
        blur_effect: bool = True
        centroid: bool = True
        inertia_tensor_eigvals: bool = True
        moments: bool = True
        moments_central: bool = True
        moments_hu: bool = True
        shannon_entropy: bool = True
        curvature: bool = True

    PRESETS = cvtda.utils.FeatureExtractorBase.Presets(
        full = Settings(reduced_stats = False), reduced = Settings(), quick = Settings(curvature = False)
    )

    FEATURE_NAMES = [
        "daisy", "sift", "orb", "hog", "basic", "blur_effect", "centroid", "inertia_tensor_eigvals",
        "moments", "moments_central", "moments_hu", "shannon_entropy", "curvature"
    ]
    
    def __init__(self, n_jobs: int = -1, settings = Settings()):
        self.fitted_ = False
        self.n_jobs_ = n_jobs
        self.feature_names_ = []
        self.reduced_stats_ = settings.reduced_stats
        self.features_mask = [
            settings.daisy, settings.sift, settings.orb, settings.hog, settings.basic,
            settings.blur_effect, settings.centroid, settings.inertia_tensor_eigvals,
            settings.moments, settings.moments_central, settings.moments_hu,
            settings.shannon_entropy, settings.curvature
        ]
        

    def feature_names(self) -> typing.List[str]:
        assert self.fitted_ is True, 'fit() must be called before feature_names()'
        return self.feature_names_

    def fit(self, gray_images: numpy.ndarray):
        self.feature_names_ = []
        for is_needed, calc, name in zip(self.features_mask, GrayGeometryExtractor.FEATURE_CALCULATORS, GrayGeometryExtractor.FEATURE_NAMES):
            if is_needed:
                self.feature_names_.extend([ f"{name}-{i}" for i in range(len(calc(self, gray_images[0]))) ])
        self.fitted_ = True
        return self

    def transform(self, gray_images: numpy.ndarray) -> numpy.ndarray:
        assert self.fitted_ is True, 'fit() must be called before transform()'
        
        def process_one_(gray_image: numpy.ndarray) -> numpy.ndarray:
            return numpy.nan_to_num(numpy.concatenate(self.calc_raw_(gray_image)), 0)
        pbar = cvtda.logging.logger().pbar(gray_images, desc = 'GrayGeometryExtractor')
        features = numpy.stack(cvtda.utils.parallel(process_one_, pbar, n_jobs = self.n_jobs_))
        assert features.shape == (len(gray_images), len(self.feature_names()))
        return features

    def calc_raw_(self, gray_image: numpy.ndarray) -> typing.List[numpy.ndarray]:
        return [
            calc(self, gray_image)
            for is_needed, calc in zip(self.features_mask, GrayGeometryExtractor.FEATURE_CALCULATORS)
            if is_needed
        ]
    
    def calc_daisy_(self, gray_image: numpy.ndarray) -> numpy.ndarray:
        image_shape = max(*gray_image.shape)
        return skimage.feature.daisy(
            gray_image,
            step = (6 * image_shape // 32),
            radius = (12 * image_shape // 32),
            rings = 5,
            histograms = 5,
            orientations = 8
        ).flatten()

    def calc_sift_(self, gray_image: numpy.ndarray) -> numpy.ndarray:
        sift = skimage.feature.SIFT()
        try:
            sift.detect_and_extract(gray_image)
            sift_descriptors = sift.descriptors.transpose()
            if sift_descriptors.shape[1] == 0:
                raise 'How is this possible?'
        except:
            sift_descriptors = numpy.zeros((128,1))
        return cvtda.utils.sequence2features(numpy.ma.array(sift_descriptors), reduced = self.reduced_stats_).flatten()

    def calc_orb_(self, gray_image: numpy.ndarray) -> numpy.ndarray:
        orb = skimage.feature.ORB()
        try:
            orb.detect_and_extract(gray_image)
            orb_descriptors = orb.descriptors.transpose()
            if orb_descriptors.shape[1] == 0:
                raise 'How is this possible?'
        except:
            orb_descriptors = numpy.zeros((256,1))
        return cvtda.utils.sequence2features(numpy.ma.array(orb_descriptors), reduced = self.reduced_stats_).flatten()

    def calc_hog_(self, gray_image: numpy.ndarray) -> numpy.ndarray:
        return skimage.feature.hog(gray_image, pixels_per_cell = (gray_image.shape[0] // 4, gray_image.shape[1] // 4))
    
    def calc_basic_(self, gray_image: numpy.ndarray) -> numpy.ndarray:
        basic_features = skimage.feature.multiscale_basic_features(gray_image).reshape((-1, 24))
        return cvtda.utils.sequence2features(
            numpy.ma.array(basic_features.transpose()), reduced = self.reduced_stats_
        ).flatten()
            
    def calc_blur_effect_(self, gray_image: numpy.ndarray) -> numpy.ndarray:
        return numpy.array([ skimage.measure.blur_effect(gray_image) ])
    
    def calc_centroid_(self, gray_image: numpy.ndarray) -> numpy.ndarray:
        return skimage.measure.centroid(gray_image)
    
    def calc_inertia_tensor_eigvals_(self, gray_image: numpy.ndarray) -> numpy.ndarray:
        try:
            return numpy.array(skimage.measure.inertia_tensor_eigvals(gray_image))
        except:
            return numpy.zeros((2))
    
    def calc_moments_(self, gray_image: numpy.ndarray) -> numpy.ndarray:
        return skimage.measure.moments(gray_image, order = 9).flatten()
    
    def calc_moments_central_(self, gray_image: numpy.ndarray) -> numpy.ndarray:
        return skimage.measure.moments_central(gray_image, order = 9).flatten()
    
    def calc_moments_hu_(self, gray_image: numpy.ndarray) -> numpy.ndarray:
        moments_central = skimage.measure.moments_central(gray_image, order = 9)
        moments_normalized = skimage.measure.moments_normalized(moments_central)
        return skimage.measure.moments_hu(moments_normalized).flatten()
    
    def calc_shannon_entropy_(self, gray_image: numpy.ndarray):
        return numpy.array([ skimage.measure.shannon_entropy(gray_image) ])
        
    def calc_curvature_(self, gray_image: numpy.ndarray) -> numpy.ndarray:
        min_, max_= gray_image.min(), gray_image.max()
        assert (min_ >= 0) and (max_ <= 1), f'Bad image format: should be [0, 1]; received [{min_}, {max_}]'

        euler_numbers, area, perimeter = [], [], []
        for threshold in range(256):
            bin = (gray_image > threshold / 255.)
            euler_numbers.append(skimage.measure.euler_number(bin))
            area.append(bin.sum())
            perimeter.append(skimage.measure.perimeter(bin))
        series = numpy.array([ euler_numbers, area, perimeter ])
        series_diff = numpy.array([ numpy.diff(euler_numbers), numpy.diff(area), numpy.diff(perimeter) ])

        return numpy.concatenate([
            cvtda.utils.sequence2features(series, reduced = self.reduced_stats_).flatten(),
            cvtda.utils.sequence2features(series_diff, reduced = self.reduced_stats_).flatten(),
        ])

    FEATURE_CALCULATORS = [
        calc_daisy_, calc_sift_, calc_orb_, calc_hog_, calc_basic_,
        calc_blur_effect_, calc_centroid_, calc_inertia_tensor_eigvals_,
        calc_moments_, calc_moments_central_, calc_moments_hu_,
        calc_shannon_entropy_, calc_curvature_
    ]


class RGBGeometryExtractor(cvtda.utils.FeatureExtractorBase):
    @dataclasses.dataclass(frozen = True)
    class Settings:
        reduced_stats: bool = True

        hog: bool = True
        centroid: bool = True
        inertia_tensor_eigvals: bool = True
        moments: bool = True
        moments_central: bool = True
        corr_coef: bool = True

    PRESETS = cvtda.utils.FeatureExtractorBase.Presets(
        full = Settings(reduced_stats = False), reduced = Settings(), quick = Settings()
    )

    FEATURE_NAMES = [ "hog", "centroid", "inertia_tensor_eigvals", "moments", "moments_central", "corr_coef" ]
    
    def __init__(self, n_jobs: int = -1, settings = Settings()):
        self.fitted_ = False
        self.n_jobs_ = n_jobs
        self.feature_names_ = []
        self.reduced_stats_ = settings.reduced_stats
        self.features_mask = [
            settings.hog, settings.centroid, settings.inertia_tensor_eigvals,
            settings.moments, settings.moments_central, settings.corr_coef
        ]

    def feature_names(self) -> typing.List[str]:
        assert self.fitted_ is True, 'fit() must be called before feature_names()'
        return self.feature_names_

    def fit(self, rgb_images: numpy.ndarray):
        self.feature_names_ = []
        for is_needed, calc, name in zip(self.features_mask, RGBGeometryExtractor.FEATURE_CALCULATORS, RGBGeometryExtractor.FEATURE_NAMES):
            if is_needed:
                self.feature_names_.extend([ f"{name}-{i}" for i in range(len(calc(self, rgb_images[0]))) ])
        self.fitted_ = True
        return self

    def transform(self, rgb_images: numpy.ndarray) -> numpy.ndarray:
        assert self.fitted_ is True, 'fit() must be called before transform()'

        def process_one_(rgb_image: numpy.ndarray) -> numpy.ndarray:
            return numpy.nan_to_num(numpy.concatenate(self.calc_raw_(rgb_image)), 0)
        pbar = cvtda.logging.logger().pbar(rgb_images, desc = 'RGBGeometryExtractor')
        features = numpy.stack(cvtda.utils.parallel(process_one_, pbar, n_jobs = self.n_jobs_))
        assert features.shape == (len(rgb_images), len(self.feature_names()))
        return features
    
    def calc_raw_(self, rgb_image: numpy.ndarray) -> typing.List[numpy.ndarray]:
        return [
            calc(self, rgb_image)
            for is_needed, calc in zip(self.features_mask, RGBGeometryExtractor.FEATURE_CALCULATORS)
            if is_needed
        ]
    
    def calc_hog_(self, rgb_image: numpy.ndarray) -> numpy.ndarray:
        return skimage.feature.hog(rgb_image, channel_axis = 2)
    
    def calc_centroid_(self, rgb_image: numpy.ndarray) -> numpy.ndarray:
        return skimage.measure.centroid(rgb_image)
    
    def calc_inertia_tensor_eigvals_(self, rgb_image: numpy.ndarray) -> numpy.ndarray:
        try:
            return numpy.array(skimage.measure.inertia_tensor_eigvals(rgb_image))
        except:
            return numpy.zeros((3))
    
    def calc_moments_(self, rgb_image: numpy.ndarray) -> numpy.ndarray:
        return skimage.measure.moments(rgb_image, order = 6).flatten()
    
    def calc_moments_central_(self, rgb_image: numpy.ndarray) -> numpy.ndarray:
        return skimage.measure.moments_central(rgb_image, order = 6).flatten()
    
    def calc_corr_coef_(self, rgb_image: numpy.ndarray) -> numpy.ndarray:
        return numpy.array([
            skimage.measure.pearson_corr_coeff(rgb_image[:, :, 0], rgb_image[:, :, 1])[0],
            skimage.measure.pearson_corr_coeff(rgb_image[:, :, 0], rgb_image[:, :, 2])[0],
            skimage.measure.pearson_corr_coeff(rgb_image[:, :, 1], rgb_image[:, :, 2])[0],
        ])
    
    FEATURE_CALCULATORS = [
        calc_hog_, calc_centroid_, calc_inertia_tensor_eigvals_,
        calc_moments_, calc_moments_central_, calc_corr_coef_
    ]


class MultidimensionalGeometryExtractor(cvtda.utils.FeatureExtractorBase):
    @dataclasses.dataclass(frozen = True)
    class Settings:
        reduced_stats: bool = True

        basic: bool = True
        blur_effect: bool = True
        centroid: bool = True
        inertia_tensor_eigvals: bool = True
        moments: bool = True
        moments_central: bool = True

    PRESETS = cvtda.utils.FeatureExtractorBase.Presets(
        full = Settings(reduced_stats = False), reduced = Settings(), quick = Settings()
    )

    FEATURE_NAMES = [ "basic", "blur_effect", "centroid", "inertia_tensor_eigvals", "moments", "moments_central" ]
    
    def __init__(self, n_jobs: int = -1, settings = Settings()):
        self.fitted_ = False
        self.n_jobs_ = n_jobs
        self.feature_names_ = []
        self.reduced_stats_ = settings.reduced_stats
        self.features_mask = [
            settings.basic, settings.blur_effect, settings.centroid,
            settings.inertia_tensor_eigvals, settings.moments, settings.moments_central
        ]
    
    def feature_names(self) -> typing.List[str]:
        assert self.fitted_ is True, 'fit() must be called before feature_names()'
        return self.feature_names_

    def fit(self, nd_images: numpy.ndarray):
        self.feature_names_ = []
        for is_needed, calc, name in zip(self.features_mask, MultidimensionalGeometryExtractor.FEATURE_CALCULATORS, MultidimensionalGeometryExtractor.FEATURE_NAMES):
            if is_needed:
                self.feature_names_.extend([ f"{name}-{i}" for i in range(len(calc(self, nd_images[0]))) ])
        self.fitted_ = True
        return self

    def transform(self, nd_images: numpy.ndarray) -> numpy.ndarray:
        assert self.fitted_ is True, 'fit() must be called before transform()'
        
        def process_one_(nd_image: numpy.ndarray) -> numpy.ndarray:
            return numpy.nan_to_num(numpy.concatenate(self.calc_raw_(nd_image)), 0)
        pbar = cvtda.logging.logger().pbar(nd_images, desc = 'MultidimensionalGeometryExtractor')
        features = numpy.stack(cvtda.utils.parallel(process_one_, pbar, n_jobs = self.n_jobs_))
        assert features.shape == (len(nd_images), len(self.feature_names()))
        return features
    
    def calc_raw_(self, nd_image: numpy.ndarray) -> typing.List[numpy.ndarray]:
        return [
            calc(self, nd_image)
            for is_needed, calc in zip(self.features_mask, MultidimensionalGeometryExtractor.FEATURE_CALCULATORS)
            if is_needed
        ]
    
    def calc_basic_(self, nd_image: numpy.ndarray) -> typing.Optional[numpy.ndarray]:
        basic_features = skimage.feature.multiscale_basic_features(nd_image)
        basic_features = basic_features.reshape((-1, basic_features.shape[-1]))
        return cvtda.utils.sequence2features(
            numpy.ma.array(basic_features.transpose()), reduced = self.reduced_stats_
        ).flatten()
    
    def calc_blur_effect_(self, nd_image: numpy.ndarray) -> typing.Optional[numpy.ndarray]:
        return numpy.array([ skimage.measure.blur_effect(nd_image) ])
    
    def calc_centroid_(self, nd_image: numpy.ndarray) -> typing.Optional[numpy.ndarray]:
        return skimage.measure.centroid(nd_image)
    
    def calc_inertia_tensor_eigvals_(self, nd_image: numpy.ndarray) -> typing.Optional[numpy.ndarray]:
        try:
            return numpy.array(skimage.measure.inertia_tensor_eigvals(nd_image))
        except:
            return numpy.zeros((len(nd_image.shape)))
    
    def calc_moments_(self, nd_image: numpy.ndarray) -> typing.Optional[numpy.ndarray]:
        return skimage.measure.moments(nd_image, order = 9).flatten()
    
    def calc_moments_central_(self, nd_image: numpy.ndarray) -> typing.Optional[numpy.ndarray]:
        return skimage.measure.moments_central(nd_image, order = 9).flatten()
    
    FEATURE_CALCULATORS = [
        calc_basic_, calc_blur_effect_, calc_centroid_,
        calc_inertia_tensor_eigvals_, calc_moments_, calc_moments_central_
    ]

class GeometryExtractor(Extractor):
    @dataclasses.dataclass(frozen = True)
    class Settings:
        rgb: RGBGeometryExtractor.Settings = RGBGeometryExtractor.Settings()
        gray: GrayGeometryExtractor.Settings = GrayGeometryExtractor.Settings()
        multidimensional: MultidimensionalGeometryExtractor.Settings = MultidimensionalGeometryExtractor.Settings()

    PRESETS = cvtda.utils.FeatureExtractorBase.Presets(
        full = Settings(
            rgb = RGBGeometryExtractor.PRESETS.full,
            gray = GrayGeometryExtractor.PRESETS.full,
            multidimensional = MultidimensionalGeometryExtractor.PRESETS.full
        ),
        reduced = Settings(
            rgb = RGBGeometryExtractor.PRESETS.reduced,
            gray = GrayGeometryExtractor.PRESETS.reduced,
            multidimensional = MultidimensionalGeometryExtractor.PRESETS.reduced
        ),
        quick = Settings(
            rgb = RGBGeometryExtractor.PRESETS.quick,
            gray = GrayGeometryExtractor.PRESETS.quick,
            multidimensional = MultidimensionalGeometryExtractor.PRESETS.quick
        )
    )

    def __init__(self, n_jobs: int = -1, settings = Settings(), only_get_from_dump: bool = False):
        super().__init__(n_jobs = n_jobs, settings = settings, only_get_from_dump = only_get_from_dump)

        self.rgb_extractor_ = RGBGeometryExtractor(n_jobs = self.n_jobs_, settings = settings.rgb)
        self.gray_extractor_ = GrayGeometryExtractor(n_jobs = self.n_jobs_, settings = settings.gray)
        self.multidimensional_extractor_ = MultidimensionalGeometryExtractor(n_jobs = self.n_jobs_, settings = settings.multidimensional)


    def process_rgb_(self, rgb_images: numpy.ndarray, do_fit: bool, dump_name: typing.Optional[str] = None) -> numpy.ndarray:
        return utils.process_iter_dump(self.rgb_extractor_, rgb_images, do_fit, self.features_dump_(dump_name))
    
    def feature_names_rgb_(self) -> typing.List[str]:
        return self.rgb_extractor_.feature_names()

    def process_gray_(self, gray_images: numpy.ndarray, do_fit: bool, dump_name: typing.Optional[str] = None) -> numpy.ndarray:
        if len(gray_images.shape) == 3:
            return utils.process_iter_dump(self.gray_extractor_, gray_images, do_fit, self.features_dump_(dump_name))
        else:
            return utils.process_iter_dump(self.multidimensional_extractor_, gray_images, do_fit, self.features_dump_(dump_name))

    def feature_names_gray_(self) -> typing.List[str]:
        if len(self.fit_dimensions_) == 2:
            return self.gray_extractor_.feature_names()
        else:
            return self.multidimensional_extractor_.feature_names()
