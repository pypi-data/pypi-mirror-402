def explain_model_choice(model_name, profile):
    if profile["rows"] < 1000:
        return f"{model_name} chosen due to small dataset robustness."
    return f"{model_name} chosen for general performance."

def explain_metric(metric):
    explanations = {
        "accuracy":"Overall correctness of predictions.",
        "f1":"Balance between precision and recall.",
        "roc_auc":"Ability to separate classes."
    }
    return explanations.get(metric,"Standard evaluation metric.")
