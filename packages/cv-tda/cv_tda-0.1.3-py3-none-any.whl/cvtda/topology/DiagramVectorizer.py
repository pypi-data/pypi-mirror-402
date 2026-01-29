import math
import typing
import dataclasses

import numpy
import joblib
import sklearn.base
import gtda.diagrams

import cvtda.utils
import cvtda.logging


def determine_filtering_epsilon_(diagrams: numpy.ndarray, percentile: float) -> float:
    life = (diagrams[:, :, 1] - diagrams[:, :, 0]).flatten()
    if len(numpy.unique(life)) == 1:
        return 1e-8
    return numpy.percentile(life[life != 0], percentile)

class Vectorizer(cvtda.utils.FeatureExtractorBase):
    def __init__(self):
        self.feature_names_ = []
        self.fitted_ = False
    
    def fit(self, diagrams: numpy.ndarray):
        self.fitted_ = True
        self.homology_dimensions_ = numpy.unique(diagrams[:, :, 2])
        num_features = self.transform(diagrams[:32]).shape[1]
        self.feature_names_ = [ f"{i}" for i in range(num_features) ]
        return self

    def transform(self, diagrams: numpy.ndarray) -> numpy.ndarray:
        assert self.fitted_ is True, 'fit() must be called before feature_names()'

    def feature_names(self) -> typing.List[str]:
        assert self.fitted_ is True, 'fit() must be called before feature_names()'
        return self.feature_names_

class SequenceStats(Vectorizer):
    def __init__(
        self,
        impl: typing.List[sklearn.base.TransformerMixin],
        enabled: bool = True,
        reduced_stats: bool = True
    ):
        super().__init__()
        self.impl_ = impl if enabled else []
        self.reduced_stats_ = reduced_stats
    
    def fit(self, diagrams: numpy.ndarray):
        for item in self.impl_:
            item.fit(diagrams)
        return super().fit(diagrams)

    def transform(self, diagrams: numpy.ndarray) -> numpy.ndarray:
        super().transform(diagrams)
        if len(self.impl_) == 0:
            return numpy.empty((len(diagrams), 0))
        flat_shape = (len(diagrams), len(self.homology_dimensions_), -1)
        return numpy.hstack([
            self.calc_stats_(item.transform(diagrams).reshape(flat_shape))
            for item in self.impl_
        ])

    def calc_stats_(self, data: numpy.ndarray):
        return numpy.hstack([
            cvtda.utils.sequence2features(data[:, dim, :], reduced = self.reduced_stats_)
            for dim in range(data.shape[1])
        ])

class Proxy(Vectorizer):
    def __init__(self, impl: sklearn.base.TransformerMixin, enabled: bool = True):
        self.impl_ = impl if enabled else None

    def fit(self, diagrams: numpy.ndarray):
        if self.impl_ is not None:
            self.impl_.fit(diagrams)
        return super().fit(diagrams)

    def transform(self, diagrams: numpy.ndarray) -> numpy.ndarray:
        super().transform(diagrams)
        if self.impl_ is not None:
            return self.impl_.transform(diagrams)
        return numpy.empty((len(diagrams), 0))


class BettiCurve(SequenceStats):
    @dataclasses.dataclass(frozen = True)
    class Settings:
        enabled: bool = True
        n_bins: int = 64
        reduced_stats: bool = True

    PRESETS = cvtda.utils.FeatureExtractorBase.Presets(
        full = Settings(reduced_stats = False), reduced = Settings(), quick = Settings()
    )

    def __init__(self, settings = Settings()):
        super().__init__(
            [gtda.diagrams.BettiCurve(n_bins = settings.n_bins, n_jobs = 1)],
            settings.enabled,
            settings.reduced_stats
        )

class Landscape(SequenceStats):
    @dataclasses.dataclass(frozen = True)
    class Settings:
        enabled: bool = True
        n_bins: int = 64
        layers: int = 3
        reduced_stats: bool = True

    PRESETS = cvtda.utils.FeatureExtractorBase.Presets(
        full = Settings(reduced_stats = False), reduced = Settings(), quick = Settings()
    )
    
    def __init__(self, settings = Settings()):
        impl = gtda.diagrams.PersistenceLandscape(
            n_layers = settings.layers, n_bins = settings.n_bins, n_jobs = 1
        )
        super().__init__([impl], settings.enabled, settings.reduced_stats)

    def transform(self, diagrams: numpy.ndarray) -> numpy.ndarray:
        assert self.fitted_ is True, 'fit() must be called before feature_names()'
        if len(self.impl_) == 0:
            return numpy.empty((len(diagrams), 0))
        impl: gtda.diagrams.PersistenceLandscape = self.impl_[0]
        landscape = impl.transform(diagrams)
        return numpy.hstack([
            self.calc_stats_(landscape[:, layer::impl.n_layers, :])
            for layer in range(impl.n_layers)
        ])

class Silhouette(SequenceStats):
    @dataclasses.dataclass(frozen = True)
    class Settings:
        enabled: bool = True
        n_bins: int = 64
        powers: typing.List[int] = dataclasses.field(default_factory = lambda: [ 1, 2 ])
        reduced_stats: bool = True

    PRESETS = cvtda.utils.FeatureExtractorBase.Presets(
        full = Settings(reduced_stats = False), reduced = Settings(), quick = Settings()
    )
    
    def __init__(self, settings = Settings()):
        impl = [
            gtda.diagrams.Silhouette(power = power, n_bins = settings.n_bins, n_jobs = 1)
            for power in settings.powers
        ]
        super().__init__(impl, settings.enabled, settings.reduced_stats)

class HeatKernel(SequenceStats):
    @dataclasses.dataclass(frozen = True)
    class Settings:
        enabled: bool = True
        n_bins: int = 64
        sigmas: typing.List[float] = dataclasses.field(default_factory = lambda: [ 0.1, 1.0, numpy.pi ])
        reduced_stats: bool = True

    PRESETS = cvtda.utils.FeatureExtractorBase.Presets(
        full = Settings(reduced_stats = False), reduced = Settings(enabled = False), quick = Settings(enabled = False)
    )
    
    def __init__(self, settings = Settings()):
        impl = [
            gtda.diagrams.HeatKernel(sigma = sigma, n_bins = settings.n_bins, n_jobs = 1)
            for sigma in settings.sigmas
        ]
        super().__init__(impl, settings.enabled, settings.reduced_stats)

class PersistenceImage(SequenceStats):
    @dataclasses.dataclass(frozen = True)
    class Settings:
        enabled: bool = True
        n_bins: int = 64
        sigmas: typing.List[float] = dataclasses.field(default_factory = lambda: [ 0.1, 1.0, numpy.pi ])
        reduced_stats: bool = True

    PRESETS = cvtda.utils.FeatureExtractorBase.Presets(
        full = Settings(reduced_stats = False), reduced = Settings(enabled = False), quick = Settings(enabled = False)
    )
    
    def __init__(self, settings = Settings()):
        impl = [
            gtda.diagrams.PersistenceImage(sigma = sigma, n_bins = settings.n_bins, n_jobs = 1)
            for sigma in settings.sigmas
        ]
        super().__init__(impl, settings.enabled, settings.reduced_stats)

class Entropy(Proxy):
    @dataclasses.dataclass(frozen = True)
    class Settings:
        enabled: bool = True

    PRESETS = cvtda.utils.FeatureExtractorBase.Presets(full = Settings(), reduced = Settings(), quick = Settings())
     
    def __init__(self, settings = Settings()):
        super().__init__(
            gtda.diagrams.PersistenceEntropy(nan_fill_value = 0, n_jobs = 1),
            settings.enabled
        )

class NumberOfPoints(Proxy):
    @dataclasses.dataclass(frozen = True)
    class Settings:
        enabled: bool = True

    PRESETS = cvtda.utils.FeatureExtractorBase.Presets(full = Settings(), reduced = Settings(), quick = Settings())
    
    def __init__(self, settings = Settings()):
        super().__init__(gtda.diagrams.NumberOfPoints(n_jobs = 1), settings.enabled)

class Lifetime(SequenceStats):
    @dataclasses.dataclass(frozen = True)
    class Settings:
        enabled: bool = True
        reduced_stats: bool = True
        filtering_percentile: float = 10

    PRESETS = cvtda.utils.FeatureExtractorBase.Presets(
        full = Settings(reduced_stats = False), reduced = Settings(), quick = Settings()
    )
    
    def __init__(self, settings = Settings()):
        super().__init__([], settings.enabled, settings.reduced_stats)
        self.filtering_percentile_ = settings.filtering_percentile
        self.enabled_ = settings.enabled
    
    def fit(self, diagrams: numpy.ndarray):
        self.filtering_epsilon_ = determine_filtering_epsilon_(diagrams, self.filtering_percentile_)
        return super().fit(diagrams)

    def transform(self, diagrams: numpy.ndarray) -> numpy.ndarray:
        Vectorizer.transform(self, diagrams)
        if not self.enabled_:
            return numpy.empty((len(diagrams), 0))
        
        birth, death, dim = diagrams[:, :, 0], diagrams[:, :, 1], diagrams[:, :, 2]
        bd2, life = (birth + death) / 2.0, death - birth
        bd2_bulk, life_bulk = [ ], [ ]
        for d in self.homology_dimensions_:
            mask = (dim != d) | (life < self.filtering_epsilon_)
            bd2_bulk.append(numpy.ma.array(bd2, mask = mask))
            life_bulk.append(numpy.ma.array(life, mask = mask))
        return numpy.hstack([
            self.calc_stats_(numpy.ma.stack(bd2_bulk, axis = 1)),
            self.calc_stats_(numpy.ma.stack(life_bulk, axis = 1))
        ])

class DiagramVectorizer(cvtda.utils.FeatureExtractorBase):
    @dataclasses.dataclass(frozen = True)
    class Settings:
        filtering_percentile: float                     = 10
        betti_curve:          BettiCurve.Settings       = BettiCurve.Settings()
        landscape:            Landscape.Settings        = Landscape.Settings()
        silhouette:           Silhouette.Settings       = Silhouette.Settings()
        heat_kernel:          HeatKernel.Settings       = HeatKernel.Settings()
        persistence_image:    PersistenceImage.Settings = PersistenceImage.Settings()
        entropy:              Entropy.Settings          = Entropy.Settings()
        number_of_points:     NumberOfPoints.Settings   = NumberOfPoints.Settings()
        lifetime:             Lifetime.Settings         = Lifetime.Settings()

    PRESETS = cvtda.utils.FeatureExtractorBase.Presets(
        full = Settings(
            betti_curve       = BettiCurve.      PRESETS.full,
            landscape         = Landscape.       PRESETS.full,
            silhouette        = Silhouette.      PRESETS.full,
            heat_kernel       = HeatKernel.      PRESETS.full,
            persistence_image = PersistenceImage.PRESETS.full,
            entropy           = Entropy.         PRESETS.full,
            number_of_points  = NumberOfPoints.  PRESETS.full,
            lifetime          = Lifetime.        PRESETS.full
        ),
        reduced = Settings(
            betti_curve       = BettiCurve.      PRESETS.reduced,
            landscape         = Landscape.       PRESETS.reduced,
            silhouette        = Silhouette.      PRESETS.reduced,
            heat_kernel       = HeatKernel.      PRESETS.reduced,
            persistence_image = PersistenceImage.PRESETS.reduced,
            entropy           = Entropy.         PRESETS.reduced,
            number_of_points  = NumberOfPoints.  PRESETS.reduced,
            lifetime          = Lifetime.        PRESETS.reduced
        ),
        quick = Settings(
            betti_curve       = BettiCurve.      PRESETS.quick,
            landscape         = Landscape.       PRESETS.quick,
            silhouette        = Silhouette.      PRESETS.quick,
            heat_kernel       = HeatKernel.      PRESETS.quick,
            persistence_image = PersistenceImage.PRESETS.quick,
            entropy           = Entropy.         PRESETS.quick,
            number_of_points  = NumberOfPoints.  PRESETS.quick,
            lifetime          = Lifetime.        PRESETS.quick
        )
    )

    EXTRACTOR_NAMES = [ "betti", "landscape", "silhouette", "heat", "persistence_image", "entropy", "number_of_points", "lifetime" ]

    def __init__(self, n_jobs: int = -1, batch_size: int = None, settings: Settings = PRESETS.reduced):
        self.fitted_ = False
        self.n_jobs_ = n_jobs
        self.batch_size_ = batch_size

        self.filtering_percentile_ = settings.filtering_percentile
        self.extractors_: typing.List[cvtda.utils.FeatureExtractorBase] = [
            BettiCurve(settings.betti_curve),
            Landscape(settings.landscape),
            Silhouette(settings.silhouette),
            HeatKernel(settings.heat_kernel),
            PersistenceImage(settings.persistence_image),
            Entropy(settings.entropy),
            NumberOfPoints(settings.number_of_points),
            Lifetime(settings.lifetime)
        ]

    def feature_names(self) -> typing.List[str]:
        assert self.fitted_ is True, 'fit() must be called before feature_names()'
        feature_names = []
        for extractor, name in zip(self.extractors_, DiagramVectorizer.EXTRACTOR_NAMES):
            feature_names.extend(self.nest_feature_names(name, extractor.feature_names()))
        return feature_names

    def fit(self, diagrams: numpy.ndarray):
        self.filtering_epsilon_ = determine_filtering_epsilon_(diagrams, self.filtering_percentile_)
        self.filtering_ = gtda.diagrams.Filtering(epsilon = self.filtering_epsilon_).fit(diagrams)
        diagrams = self.filtering_.transform(diagrams)
        for extractor in self.extractors_:
            extractor.fit(diagrams)
        cvtda.logging.logger().print('DiagramVectorizer: fitting complete')
        self.fitted_ = True
        return self
    
    def transform(self, diagrams: numpy.ndarray) -> numpy.ndarray:
        assert self.fitted_ is True, 'fit() must be called before transform()'
        batch_size = self.get_batch_size_(len(diagrams))
        loop = list(range(0, len(diagrams), batch_size))
        
        def transform_batch(batch_start: numpy.ndarray) -> numpy.ndarray:
            return self.transform_batch_raw_(diagrams[batch_start:batch_start + batch_size])
        features = cvtda.utils.parallel(transform_batch, loop, return_as = 'generator', n_jobs = self.n_jobs_)
        collector = cvtda.logging.logger().pbar(features, total = len(loop), desc = 'DiagramVectorizer: batch')
        features = numpy.vstack(list(collector))
        assert features.shape == (len(diagrams), len(self.feature_names())), \
                f"{features.shape} != {(len(diagrams), len(self.feature_names()))}"
        return features

    def get_batch_size_(self, num_objects: int):
        if self.batch_size_ is not None:
            return self.batch_size_
        n_jobs = joblib.effective_n_jobs(self.n_jobs_)
        batch_size = math.ceil(num_objects / n_jobs)
        return math.ceil(batch_size / math.ceil(batch_size / 256))

    def transform_batch_raw_(self, batch: numpy.ndarray) -> numpy.ndarray:
        batch = self.filtering_.transform(batch)
        return numpy.hstack([ extractor.transform(batch) for extractor in self.extractors_ ])
