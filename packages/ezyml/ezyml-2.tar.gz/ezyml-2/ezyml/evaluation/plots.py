import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, roc_curve, precision_recall_curve

def plot_confusion_matrix(y_true, y_pred, path):
    cm = confusion_matrix(y_true, y_pred)
    sns.heatmap(cm, annot=True, fmt="d")
    plt.savefig(path); plt.close()

def plot_roc_curve(y_true, y_prob, path):
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    plt.plot(fpr, tpr); plt.xlabel("FPR"); plt.ylabel("TPR")
    plt.savefig(path); plt.close()

def plot_pr_curve(y_true, y_prob, path):
    p, r, _ = precision_recall_curve(y_true, y_prob)
    plt.plot(r, p); plt.xlabel("Recall"); plt.ylabel("Precision")
    plt.savefig(path); plt.close()

def plot_pred_vs_actual(y_true, y_pred, path):
    plt.scatter(y_true, y_pred)
    plt.xlabel("Actual"); plt.ylabel("Predicted")
    plt.savefig(path); plt.close()
