from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, mean_squared_error, mean_absolute_error, r2_score
)

def accuracy(y_true, y_pred): return accuracy_score(y_true, y_pred)
def precision(y_true, y_pred): return precision_score(y_true, y_pred, zero_division=0)
def recall(y_true, y_pred): return recall_score(y_true, y_pred, zero_division=0)
def f1(y_true, y_pred): return f1_score(y_true, y_pred, zero_division=0)
def roc_auc(y_true, y_prob): return roc_auc_score(y_true, y_prob)

def rmse(y_true, y_pred): return mean_squared_error(y_true, y_pred, squared=False)
def mae(y_true, y_pred): return mean_absolute_error(y_true, y_pred)
def r2(y_true, y_pred): return r2_score(y_true, y_pred)

METRIC_REGISTRY = {
    "accuracy": accuracy,
    "precision": precision,
    "recall": recall,
    "f1": f1,
    "roc_auc": roc_auc,
    "rmse": rmse,
    "mae": mae,
    "r2": r2
}
