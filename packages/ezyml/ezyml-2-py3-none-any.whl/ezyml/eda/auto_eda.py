import numpy as np
from scipy.stats import skew

def auto_eda(df, target=None):
    report = {}
    report["shape"] = df.shape
    report["missing"] = df.isnull().mean().to_dict()
    report["outliers"] = outliers_iqr(df)
    report["skewness"] = {c: float(skew(df[c].dropna()))
                          for c in df.select_dtypes(include=np.number)}
    if target:
        report["target_distribution"] = df[target].value_counts(normalize=True).to_dict()
    return report

def outliers_iqr(df):
    out = {}
    for c in df.select_dtypes(include=np.number):
        q1, q3 = df[c].quantile([0.25,0.75])
        iqr = q3-q1
        mask = (df[c]<q1-1.5*iqr)|(df[c]>q3+1.5*iqr)
        out[c] = float(mask.mean())
    return out
