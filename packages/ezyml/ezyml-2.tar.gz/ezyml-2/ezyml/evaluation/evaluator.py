import os, json
from .metrics import METRIC_REGISTRY
from .plots import *

class Evaluator:
    DEFAULT_METRICS = {
        "classification": ["accuracy", "precision", "recall", "f1", "roc_auc"],
        "regression": ["rmse", "mae", "r2"]
    }

    DEFAULT_PLOTS = {
        "classification": ["confusion_matrix", "roc_curve", "pr_curve"],
        "regression": ["pred_vs_actual"]
    }

    def __init__(self, task, extra_metrics=None, extra_plots=None):
        self.task = task
        self.metrics = self.DEFAULT_METRICS[task] + (extra_metrics or [])
        self.plots = self.DEFAULT_PLOTS[task] + (extra_plots or [])

    def evaluate(self, y_true, y_pred, y_prob=None):
        results = {}
        for m in self.metrics:
            fn = METRIC_REGISTRY[m]
            results[m] = fn(y_true, y_prob if m=="roc_auc" else y_pred)
        return results

    def save(self, results, out_dir):
        os.makedirs(out_dir, exist_ok=True)
        with open(f"{out_dir}/metrics.json","w") as f:
            json.dump(results, f, indent=2)

    def visualize(self, y_true, y_pred, y_prob, out_dir):
        os.makedirs(out_dir, exist_ok=True)
        for p in self.plots:
            if p=="confusion_matrix":
                plot_confusion_matrix(y_true,y_pred,f"{out_dir}/confusion.png")
            elif p=="roc_curve":
                plot_roc_curve(y_true,y_prob,f"{out_dir}/roc.png")
            elif p=="pr_curve":
                plot_pr_curve(y_true,y_prob,f"{out_dir}/pr.png")
            elif p=="pred_vs_actual":
                plot_pred_vs_actual(y_true,y_pred,f"{out_dir}/pred_vs_actual.png")
