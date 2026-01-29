import numpy
import sklearn.metrics

def estimate_quality(pred_proba: numpy.ndarray, masks: numpy.ndarray) -> dict:
    # Segmentation is basically just per-pixel classification
    scores = pred_proba.flatten()
    preds = (scores >= 0.5).astype(numpy.int8)
    targets = masks.flatten().astype(numpy.int8)
    return {
        'Accuracy':      sklearn.metrics.accuracy_score (targets, preds),
        'AUC-ROC':       sklearn.metrics.roc_auc_score  (targets, scores),
        'Precision':     sklearn.metrics.precision_score(targets, preds, zero_division = 0),
        'Recall':        sklearn.metrics.recall_score   (targets, preds, zero_division = 0),
        'F1-score':      sklearn.metrics.f1_score       (targets, preds, zero_division = 0),
        'Jaccard score': sklearn.metrics.jaccard_score  (targets, preds, zero_division = 0)
    }
