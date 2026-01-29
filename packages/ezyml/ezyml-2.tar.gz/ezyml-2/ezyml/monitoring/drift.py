def detect_data_drift(base_df, new_df):
    drift = {}
    for c in base_df.columns:
        drift[c] = abs(base_df[c].mean() - new_df[c].mean())
    return drift

def detect_concept_drift(y_true, y_pred, threshold=0.7):
    acc = (y_true==y_pred).mean()
    return acc < threshold
