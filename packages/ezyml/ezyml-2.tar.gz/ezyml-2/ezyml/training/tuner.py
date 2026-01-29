from sklearn.model_selection import GridSearchCV

def tune_model(model, param_grid, X, y):
    gs = GridSearchCV(model, param_grid, cv=3)
    gs.fit(X,y)
    return gs.best_estimator_
