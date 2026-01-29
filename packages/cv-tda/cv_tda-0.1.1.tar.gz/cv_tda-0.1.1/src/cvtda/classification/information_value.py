import numpy
import sklearn.base
import matplotlib.pyplot as plt

import cvtda.utils
import cvtda.logging


def calculate_binary_information_value(feature: numpy.ndarray, target: numpy.ndarray, bins: int) -> float:
    quantiles = numpy.linspace(0, 1, bins + 1)
    bins = numpy.unique(numpy.quantile(feature, quantiles))
    bins[0] -= 0.0001
    bins[-1] += 0.0001
    
    feature = numpy.digitize(feature, bins, right = True)
    n, events = [ ], [ ]
    for bin in range(1, len(bins)):
        mask = (feature == bin)
        n.append(mask.sum())
        events.append((target * mask).sum())
    n = numpy.array(n)
    events = numpy.array(events)

    non_events = n - events
    events_prc = numpy.maximum(events, 0.5) / events.sum()
    non_events_prc = numpy.maximum(non_events, 0.5) / non_events.sum()

    woe = numpy.log(events_prc / non_events_prc)
    iv = woe * (events_prc - non_events_prc)
    return iv.sum()


def calculate_information_value_one_feature(
    feature: numpy.ndarray,
    y_true: numpy.ndarray,
    bins: int
) -> dict:
    IVs = []
    for class_idx in range(numpy.max(y_true)):
        target = (y_true == class_idx).astype(int)
        IVs.append(calculate_binary_information_value(feature, target, bins))
    return numpy.mean(IVs)


def calculate_information_value(
    features: numpy.ndarray,
    y_true: numpy.ndarray,
    bins: int = 10,
    n_jobs: int = -1
) -> numpy.ndarray:
    params = [ (features[:, idx], y_true, bins) for idx in range(features.shape[1]) ]
    iv_generator = cvtda.utils.parallel(
        calculate_information_value_one_feature, params, return_as = 'generator', n_jobs = n_jobs
    )
    pbar = cvtda.logging.logger().pbar(iv_generator, total = features.shape[1], desc = 'information values')
    return numpy.array(list(pbar))


class InformationValueFeatureSelector(sklearn.base.TransformerMixin):
    def __init__(
        self,
        n_jobs: int = -1,
        verbose: bool = True,

        bins: int = 10,
        threshold: float = 0.5
    ):
        self.fitted_ = False
        self.n_jobs_ = n_jobs

        self.bins_ = bins
        self.threshold_ = threshold

    def fit(self, features: numpy.ndarray, target: numpy.ndarray):
        cvtda.logging.logger().print('Fitting the information value feature selector')
        self.IV_ = calculate_information_value(
            features,
            target,
            bins = self.bins_,
            n_jobs = self.n_jobs_
        )
        self.good_features_idx_ = numpy.where(self.IV_ > self.threshold_)[0]
        
        cvtda.logging.logger().print('Fitting complete')
        self.fitted_ = True
        return self
    
    def transform(self, features: numpy.ndarray) -> numpy.ndarray:
        assert self.fitted_ is True, 'fit() must be called before transform()'
        return features[:, self.good_features_idx_]

    def hist(self, bins: int = 50):
        assert self.fitted_ is True, 'fit() must be called before hist()'
        return plt.hist(self.IV_, bins = bins)
