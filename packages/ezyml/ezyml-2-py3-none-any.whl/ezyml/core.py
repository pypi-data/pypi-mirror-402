# # # ezyml/ezyml.py

# # import pandas as pd
# # import numpy as np
# # import pickle
# # import json

# # # Preprocessing
# # from sklearn.model_selection import train_test_split
# # from sklearn.preprocessing import StandardScaler, OneHotEncoder
# # from sklearn.compose import ColumnTransformer
# # from sklearn.pipeline import Pipeline
# # from sklearn.impute import SimpleImputer

# # # Models
# # from sklearn.linear_model import LogisticRegression, LinearRegression, Ridge, Lasso, ElasticNet
# # from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingClassifier, GradientBoostingRegressor, ExtraTreesClassifier
# # from sklearn.svm import SVC, SVR
# # from sklearn.neighbors import KNeighborsClassifier
# # from sklearn.naive_bayes import GaussianNB
# # from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
# # from sklearn.decomposition import PCA
# # from sklearn.manifold import TSNE
# # import xgboost as xgb

# # # Metrics
# # from sklearn.metrics import (
# #     accuracy_score, f1_score, roc_auc_score, confusion_matrix,
# #     mean_absolute_error, mean_squared_error, r2_score,
# #     silhouette_score
# # )

# # # --- Model Dictionaries ---
# # CLASSIFICATION_MODELS = {
# #     "logistic_regression": LogisticRegression,
# #     "random_forest": RandomForestClassifier,
# #     "xgboost": xgb.XGBClassifier,
# #     "svm": SVC,
# #     "naive_bayes": GaussianNB,
# #     "gradient_boosting": GradientBoostingClassifier,
# #     "extra_trees": ExtraTreesClassifier,
# #     "knn": KNeighborsClassifier,
# # }

# # REGRESSION_MODELS = {
# #     "linear_regression": LinearRegression,
# #     "ridge": Ridge,
# #     "lasso": Lasso,
# #     "elasticnet": ElasticNet,
# #     "random_forest": RandomForestRegressor,
# #     "xgboost": xgb.XGBRegressor,
# #     "svr": SVR,
# #     "gradient_boosting": GradientBoostingRegressor,
# # }

# # CLUSTERING_MODELS = {
# #     "kmeans": KMeans,
# #     "dbscan": DBSCAN,
# #     "agglo": AgglomerativeClustering,
# # }

# # DIM_REDUCTION_MODELS = {
# #     "pca": PCA,
# #     "tsne": TSNE,
# # }


# # class EZTrainer:
# #     """A class to easily train, evaluate, and export ML models."""

# #     def __init__(self, data, target=None, model="random_forest", task="auto",
# #                  test_size=0.2, scale=True, n_components=None, random_state=42):
# #         """
# #         Initializes the EZTrainer.

# #         Args:
# #             data (str or pd.DataFrame): Path to CSV or a pandas DataFrame.
# #             target (str, optional): Name of the target column. Defaults to None.
# #             model (str, optional): Model to use. Defaults to "random_forest".
# #             task (str, optional): Type of task. Can be 'auto', 'classification', 
# #                                   'regression', 'clustering', 'dim_reduction'. Defaults to "auto".
# #             test_size (float, optional): Proportion of data for the test set. Defaults to 0.2.
# #             scale (bool, optional): Whether to scale numerical features. Defaults to True.
# #             n_components (int, optional): Number of components for dimensionality reduction. Defaults to None.
# #             random_state (int, optional): Random state for reproducibility. Defaults to 42.
# #         """
# #         self.target = target
# #         self.model_name = model
# #         self.task = task
# #         self.test_size = test_size
# #         self.scale = scale
# #         self.n_components = n_components
# #         self.random_state = random_state

# #         self.df = self._load_data(data)
# #         self._auto_detect_task()

# #         self.X = None
# #         self.y = None
# #         self.X_train, self.X_test, self.y_train, self.y_test = [None] * 4
        
# #         self.pipeline = None
# #         self.report = {}
# #         self.transformed_data = None

# #     def _load_data(self, data):
# #         """Loads data from path or uses the provided DataFrame."""
# #         if isinstance(data, str):
# #             print(f"Loading data from {data}...")
# #             return pd.read_csv(data)
# #         elif isinstance(data, pd.DataFrame):
# #             print("Using provided DataFrame.")
# #             return data.copy()
# #         else:
# #             raise TypeError("Data must be a file path (str) or a pandas DataFrame.")

# #     def _auto_detect_task(self):
# #         """Automatically detects the ML task based on data and parameters."""
# #         if self.task != "auto":
# #             print(f"Task specified as: {self.task}")
# #             return

# #         if self.target:
# #             if self.target not in self.df.columns:
# #                 raise ValueError(f"Target column '{self.target}' not found in data.")
            
# #             target_dtype = self.df[self.target].dtype
# #             unique_values = self.df[self.target].nunique()

# #             # Heuristic for classification vs. regression
# #             if pd.api.types.is_numeric_dtype(target_dtype) and unique_values > 20:
# #                 self.task = "regression"
# #             else:
# #                 self.task = "classification"
# #         elif self.model_name in CLUSTERING_MODELS:
# #             self.task = "clustering"
# #         elif self.model_name in DIM_REDUCTION_MODELS:
# #             self.task = "dim_reduction"
# #         else:
# #             raise ValueError("Could not auto-detect task. Please specify the 'task' parameter.")
        
# #         print(f"Auto-detected task as: {self.task}")

# #     def _get_preprocessor(self):
# #         """Builds a preprocessor pipeline for numerical and categorical features."""
# #         numerical_features = self.X.select_dtypes(include=np.number).columns.tolist()
# #         categorical_features = self.X.select_dtypes(include=['object', 'category']).columns.tolist()

# #         print(f"Identified {len(numerical_features)} numerical features: {numerical_features}")
# #         print(f"Identified {len(categorical_features)} categorical features: {categorical_features}")

# #         num_steps = [('imputer', SimpleImputer(strategy='median'))]
# #         if self.scale:
# #             num_steps.append(('scaler', StandardScaler()))
        
# #         numerical_transformer = Pipeline(steps=num_steps)
# #         categorical_transformer = Pipeline(steps=[
# #             ('imputer', SimpleImputer(strategy='most_frequent')),
# #             ('onehot', OneHotEncoder(handle_unknown='ignore'))
# #         ])

# #         return ColumnTransformer(transformers=[
# #             ('num', numerical_transformer, numerical_features),
# #             ('cat', categorical_transformer, categorical_features)
# #         ], remainder='passthrough')

# #     def _calculate_metrics(self):
# #         """Calculates and stores performance metrics based on the task."""
# #         print("Calculating metrics...")
# #         if self.task == "classification":
# #             preds = self.pipeline.predict(self.X_test)
# #             self.report = {
# #                 "accuracy": accuracy_score(self.y_test, preds),
# #                 "f1_score": f1_score(self.y_test, preds, average='weighted'),
# #                 "confusion_matrix": confusion_matrix(self.y_test, preds).tolist(),
# #             }
# #             # ROC AUC for binary and multi-class (if applicable)
# #             try:
# #                 if hasattr(self.pipeline, "predict_proba"):
# #                     probs = self.pipeline.predict_proba(self.X_test)
# #                     if probs.shape[1] == 2: # Binary
# #                         self.report["roc_auc"] = roc_auc_score(self.y_test, probs[:, 1])
# #                     else: # Multi-class
# #                         self.report["roc_auc"] = roc_auc_score(self.y_test, probs, multi_class='ovr')
# #             except Exception as e:
# #                 print(f"Could not calculate ROC AUC score: {e}")

# #         elif self.task == "regression":
# #             preds = self.pipeline.predict(self.X_test)
# #             self.report = {
# #                 "r2_score": r2_score(self.y_test, preds),
# #                 "mae": mean_absolute_error(self.y_test, preds),
# #                 "mse": mean_squared_error(self.y_test, preds),
# #                 "rmse": np.sqrt(mean_squared_error(self.y_test, preds)),
# #             }
        
# #         elif self.task == "clustering":
# #             labels = self.pipeline.named_steps['model'].labels_
# #             if len(set(labels)) > 1: # Silhouette score requires at least 2 clusters
# #                 self.report = {
# #                     "silhouette_score": silhouette_score(self.X, labels),
# #                     "n_clusters": len(set(labels))
# #                 }
# #             else:
# #                 self.report = {"n_clusters": len(set(labels)), "silhouette_score": None}

# #         print("Metrics report:")
# #         print(json.dumps(self.report, indent=4))

# #     def train(self):
# #         """Trains the specified model."""
# #         print(f"\n--- Starting Training for Task: {self.task.upper()} ---")
        
# #         if self.task in ["classification", "regression"]:
# #             self.X = self.df.drop(columns=[self.target])
# #             self.y = self.df[self.target]
            
# #             self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
# #                 self.X, self.y, test_size=self.test_size, random_state=self.random_state
# #             )

# #             preprocessor = self._get_preprocessor()
# #             model_map = CLASSIFICATION_MODELS if self.task == "classification" else REGRESSION_MODELS
            
# #             if self.model_name not in model_map:
# #                 raise ValueError(f"Model '{self.model_name}' not supported for {self.task}.")
            
# #             model_instance = model_map[self.model_name](random_state=self.random_state) if 'random_state' in model_map[self.model_name]().get_params() else model_map[self.model_name]()

# #             self.pipeline = Pipeline(steps=[
# #                 ('preprocessor', preprocessor),
# #                 ('model', model_instance)
# #             ])
            
# #             print(f"Training {self.model_name} model...")
# #             self.pipeline.fit(self.X_train, self.y_train)
# #             self._calculate_metrics()

# #         elif self.task == "clustering":
# #             self.X = self.df.copy()
# #             preprocessor = self._get_preprocessor()
            
# #             if self.model_name not in CLUSTERING_MODELS:
# #                 raise ValueError(f"Model '{self.model_name}' not supported for clustering.")
            
# #             model_instance = CLUSTERING_MODELS[self.model_name]()
            
# #             self.pipeline = Pipeline(steps=[
# #                 ('preprocessor', preprocessor),
# #                 ('model', model_instance)
# #             ])
            
# #             print(f"Fitting {self.model_name} model...")
# #             self.pipeline.fit(self.X)
# #             self._calculate_metrics()

# #         elif self.task == "dim_reduction":
# #             self.X = self.df.copy()
# #             preprocessor = self._get_preprocessor()

# #             if self.model_name not in DIM_REDUCTION_MODELS:
# #                 raise ValueError(f"Model '{self.model_name}' not supported for dimensionality reduction.")
            
# #             model_instance = DIM_REDUCTION_MODELS[self.model_name](n_components=self.n_components, random_state=self.random_state) if self.n_components else DIM_REDUCTION_MODELS[self.model_name](random_state=self.random_state)

# #             self.pipeline = Pipeline(steps=[
# #                 ('preprocessor', preprocessor),
# #                 ('model', model_instance)
# #             ])

# #             print(f"Transforming data with {self.model_name}...")
# #             self.transformed_data = self.pipeline.fit_transform(self.X)
# #             print(f"Data transformed into {self.transformed_data.shape[1]} dimensions.")

# #         else:
# #             raise ValueError(f"Task '{self.task}' is not supported.")
        
# #         print("--- Training Complete ---")

# #     def predict(self, X_new):
# #         """Makes predictions on new data."""
# #         if not self.pipeline:
# #             raise RuntimeError("Model has not been trained yet. Call .train() first.")
# #         if self.task not in ["classification", "regression"]:
# #             raise RuntimeError(f"Predict is not available for task '{self.task}'.")
        
# #         if isinstance(X_new, str):
# #             X_new = pd.read_csv(X_new)

# #         return self.pipeline.predict(X_new)

# #     def save_model(self, path="model.pkl"):
# #         """Saves the trained pipeline to a .pkl file."""
# #         if not self.pipeline:
# #             raise RuntimeError("No model to save. Call .train() first.")
        
# #         with open(path, 'wb') as f:
# #             pickle.dump(self.pipeline, f)
# #         print(f"Model saved successfully to {path}")

# #     def save_report(self, path="report.json"):
# #         """Saves the metrics report to a .json file."""
# #         if not self.report:
# #             raise RuntimeError("No report to save. Call .train() and ensure metrics were calculated.")
        
# #         with open(path, 'w') as f:
# #             json.dump(self.report, f, indent=4)
# #         print(f"Report saved successfully to {path}")

# #     def save_transformed(self, path="transformed_data.csv"):
# #         """Saves the transformed data from PCA/t-SNE to a .csv file."""
# #         if self.transformed_data is None:
# #             raise RuntimeError("No transformed data to save. Run a 'dim_reduction' task first.")
        
# #         pd.DataFrame(self.transformed_data).to_csv(path, index=False)
# #         print(f"Transformed data saved successfully to {path}")


# # ezyml/core.py

# import pandas as pd
# import numpy as np
# import pickle
# import json

# # Preprocessing
# from sklearn.model_selection import train_test_split
# from sklearn.preprocessing import StandardScaler, OneHotEncoder
# from sklearn.compose import ColumnTransformer
# from sklearn.pipeline import Pipeline
# from sklearn.impute import SimpleImputer

# # Models
# from sklearn.linear_model import LogisticRegression, LinearRegression, Ridge, Lasso, ElasticNet
# from sklearn.ensemble import (
#     RandomForestClassifier, RandomForestRegressor,
#     GradientBoostingClassifier, GradientBoostingRegressor,
#     ExtraTreesClassifier
# )
# from sklearn.svm import SVC, SVR
# from sklearn.neighbors import KNeighborsClassifier
# from sklearn.naive_bayes import GaussianNB
# from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
# from sklearn.decomposition import PCA
# from sklearn.manifold import TSNE
# import xgboost as xgb

# # Metrics
# from sklearn.metrics import (
#     accuracy_score, f1_score, roc_auc_score, confusion_matrix,
#     mean_absolute_error, mean_squared_error, r2_score,
#     silhouette_score
# )

# # ------------------------------------------------------------------
# # MODEL REGISTRIES
# # ------------------------------------------------------------------

# CLASSIFICATION_MODELS = {
#     "logistic_regression": LogisticRegression,
#     "random_forest": RandomForestClassifier,
#     "xgboost": xgb.XGBClassifier,
#     "svm": SVC,
#     "naive_bayes": GaussianNB,
#     "gradient_boosting": GradientBoostingClassifier,
#     "extra_trees": ExtraTreesClassifier,
#     "knn": KNeighborsClassifier,
# }

# REGRESSION_MODELS = {
#     "linear_regression": LinearRegression,
#     "ridge": Ridge,
#     "lasso": Lasso,
#     "elasticnet": ElasticNet,
#     "random_forest": RandomForestRegressor,
#     "xgboost": xgb.XGBRegressor,
#     "svr": SVR,
#     "gradient_boosting": GradientBoostingRegressor,
# }

# CLUSTERING_MODELS = {
#     "kmeans": KMeans,
#     "dbscan": DBSCAN,
#     "agglo": AgglomerativeClustering,
# }

# DIM_REDUCTION_MODELS = {
#     "pca": PCA,
#     "tsne": TSNE,
# }


# # ------------------------------------------------------------------
# # EZTRAINER
# # ------------------------------------------------------------------

# class EZTrainer:
#     """
#     Train, evaluate, and export ML models.
#     """

#     def __init__(
#         self,
#         data,
#         target=None,
#         model="random_forest",
#         task="auto",
#         test_size=0.2,
#         scale=True,
#         n_components=None,
#         random_state=42
#     ):
#         self.target = target
#         self.model_name = model
#         self.task = task
#         self.test_size = test_size
#         self.scale = scale
#         self.n_components = n_components
#         self.random_state = random_state

#         self.df = self._load_data(data)
#         self._auto_detect_task()

#         # Core data
#         self.X = None
#         self.y = None
#         self.X_train = None
#         self.X_test = None
#         self.y_train = None
#         self.y_test = None

#         # Artifacts REQUIRED by compiler
#         self.y_pred = None
#         self.y_prob = None

#         self.pipeline = None
#         self.report = {}
#         self.transformed_data = None

#     # ------------------------------------------------------------------

#     def _load_data(self, data):
#         if isinstance(data, str):
#             print(f"Loading data from {data}...")
#             return pd.read_csv(data)
#         elif isinstance(data, pd.DataFrame):
#             print("Using provided DataFrame.")
#             return data.copy()
#         else:
#             raise TypeError("Data must be a CSV path or a pandas DataFrame.")

#     # ------------------------------------------------------------------

#     def _auto_detect_task(self):
#         if self.task != "auto":
#             print(f"Task specified as: {self.task}")
#             return

#         if self.target:
#             if self.target not in self.df.columns:
#                 raise ValueError(f"Target column '{self.target}' not found.")

#             dtype = self.df[self.target].dtype
#             uniq = self.df[self.target].nunique()

#             if pd.api.types.is_numeric_dtype(dtype) and uniq > 20:
#                 self.task = "regression"
#             else:
#                 self.task = "classification"

#         elif self.model_name in CLUSTERING_MODELS:
#             self.task = "clustering"
#         elif self.model_name in DIM_REDUCTION_MODELS:
#             self.task = "dim_reduction"
#         else:
#             raise ValueError("Could not auto-detect task.")

#         print(f"Auto-detected task as: {self.task}")

#     # ------------------------------------------------------------------

#     def _get_preprocessor(self):
#         numerical = self.X.select_dtypes(include=np.number).columns.tolist()
#         categorical = self.X.select_dtypes(include=["object", "category"]).columns.tolist()

#         print(f"Identified {len(numerical)} numerical features: {numerical}")
#         print(f"Identified {len(categorical)} categorical features: {categorical}")

#         num_steps = [("imputer", SimpleImputer(strategy="median"))]
#         if self.scale:
#             num_steps.append(("scaler", StandardScaler()))

#         num_pipe = Pipeline(num_steps)
#         cat_pipe = Pipeline([
#             ("imputer", SimpleImputer(strategy="most_frequent")),
#             ("onehot", OneHotEncoder(handle_unknown="ignore"))
#         ])

#         return ColumnTransformer([
#             ("num", num_pipe, numerical),
#             ("cat", cat_pipe, categorical)
#         ])

#     # ------------------------------------------------------------------

#     def _calculate_metrics(self):
#         print("Calculating metrics...")

#         if self.task == "classification":
#             self.report = {
#                 "accuracy": accuracy_score(self.y_test, self.y_pred),
#                 "f1_score": f1_score(self.y_test, self.y_pred, average="weighted"),
#                 "confusion_matrix": confusion_matrix(self.y_test, self.y_pred).tolist(),
#             }

#             if self.y_prob is not None:
#                 try:
#                     if self.y_prob.ndim == 1:
#                         self.report["roc_auc"] = roc_auc_score(self.y_test, self.y_prob)
#                     else:
#                         self.report["roc_auc"] = roc_auc_score(
#                             self.y_test, self.y_prob, multi_class="ovr"
#                         )
#                 except Exception:
#                     self.report["roc_auc"] = None

#         elif self.task == "regression":
#             self.report = {
#                 "r2": r2_score(self.y_test, self.y_pred),
#                 "mae": mean_absolute_error(self.y_test, self.y_pred),
#                 "rmse": np.sqrt(mean_squared_error(self.y_test, self.y_pred)),
#             }

#         elif self.task == "clustering":
#             labels = self.pipeline.named_steps["model"].labels_
#             self.report = {
#                 "n_clusters": len(set(labels)),
#                 "silhouette_score": silhouette_score(self.X, labels)
#                 if len(set(labels)) > 1 else None
#             }

#         print("Metrics report:")
#         print(json.dumps(self.report, indent=4))

#     # ------------------------------------------------------------------

#     def train(self):
#         print(f"\n--- Starting Training for Task: {self.task.upper()} ---")

#         if self.task in ["classification", "regression"]:
#             self.X = self.df.drop(columns=[self.target])
#             self.y = self.df[self.target]

#             self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
#                 self.X, self.y,
#                 test_size=self.test_size,
#                 random_state=self.random_state
#             )

#             preprocessor = self._get_preprocessor()
#             model_map = CLASSIFICATION_MODELS if self.task == "classification" else REGRESSION_MODELS

#             if self.model_name not in model_map:
#                 raise ValueError(f"Model '{self.model_name}' not supported.")

#             Model = model_map[self.model_name]
#             model = Model(random_state=self.random_state) if "random_state" in Model().get_params() else Model()

#             self.pipeline = Pipeline([
#                 ("preprocessor", preprocessor),
#                 ("model", model)
#             ])

#             print(f"Training {self.model_name} model...")
#             self.pipeline.fit(self.X_train, self.y_train)

#             # REQUIRED FOR COMPILER
#             self.y_pred = self.pipeline.predict(self.X_test)

#             if hasattr(self.pipeline.named_steps["model"], "predict_proba"):
#                 probs = self.pipeline.predict_proba(self.X_test)
#                 self.y_prob = probs[:, 1] if probs.shape[1] == 2 else probs
#             else:
#                 self.y_prob = None

#             self._calculate_metrics()

#         elif self.task == "clustering":
#             self.X = self.df.copy()
#             preprocessor = self._get_preprocessor()
#             model = CLUSTERING_MODELS[self.model_name]()

#             self.pipeline = Pipeline([
#                 ("preprocessor", preprocessor),
#                 ("model", model)
#             ])

#             self.pipeline.fit(self.X)
#             self._calculate_metrics()

#         elif self.task == "dim_reduction":
#             self.X = self.df.copy()
#             preprocessor = self._get_preprocessor()
#             Model = DIM_REDUCTION_MODELS[self.model_name]

#             model = Model(
#                 n_components=self.n_components,
#                 random_state=self.random_state
#             ) if self.n_components else Model(random_state=self.random_state)

#             self.pipeline = Pipeline([
#                 ("preprocessor", preprocessor),
#                 ("model", model)
#             ])

#             self.transformed_data = self.pipeline.fit_transform(self.X)
#             print(f"Data transformed into {self.transformed_data.shape[1]} dimensions.")

#         else:
#             raise ValueError(f"Task '{self.task}' not supported.")

#         print("--- Training Complete ---")
#         return self

#     # ------------------------------------------------------------------

#     def predict(self, X_new):
#         if not self.pipeline:
#             raise RuntimeError("Model not trained.")

#         if isinstance(X_new, str):
#             X_new = pd.read_csv(X_new)

#         return self.pipeline.predict(X_new)

#     # ------------------------------------------------------------------

#     def save_model(self, path="model.pkl"):
#         with open(path, "wb") as f:
#             pickle.dump(self.pipeline, f)
#         print(f"Model saved successfully to {path}")

#     # ------------------------------------------------------------------

#     def save_report(self, path="report.json"):
#         with open(path, "w") as f:
#             json.dump(self.report, f, indent=4)
#         print(f"Report saved successfully to {path}")

#     # ------------------------------------------------------------------

#     def save_transformed(self, path="transformed_data.csv"):
#         if self.transformed_data is None:
#             raise RuntimeError("No transformed data.")
#         pd.DataFrame(self.transformed_data).to_csv(path, index=False)
#         print(f"Transformed data saved to {path}")


# ezyml/core.py

import pandas as pd
import numpy as np
import pickle
import json

# ======================================================
# PREPROCESSING
# ======================================================
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer

# ======================================================
# MODELS
# ======================================================
from sklearn.linear_model import LogisticRegression, LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.ensemble import (
    RandomForestClassifier,
    RandomForestRegressor,
    GradientBoostingClassifier,
    GradientBoostingRegressor,
    ExtraTreesClassifier
)
from sklearn.svm import SVC, SVR
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import xgboost as xgb

# ======================================================
# METRICS
# ======================================================
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    silhouette_score
)

# ======================================================
# MODEL REGISTRIES
# ======================================================
CLASSIFICATION_MODELS = {
    "logistic_regression": LogisticRegression,
    "random_forest": RandomForestClassifier,
    "xgboost": xgb.XGBClassifier,
    "svm": SVC,
    "naive_bayes": GaussianNB,
    "gradient_boosting": GradientBoostingClassifier,
    "extra_trees": ExtraTreesClassifier,
    "knn": KNeighborsClassifier,
}

REGRESSION_MODELS = {
    "linear_regression": LinearRegression,
    "ridge": Ridge,
    "lasso": Lasso,
    "elasticnet": ElasticNet,
    "random_forest": RandomForestRegressor,
    "xgboost": xgb.XGBRegressor,
    "svr": SVR,
    "gradient_boosting": GradientBoostingRegressor,
}

CLUSTERING_MODELS = {
    "kmeans": KMeans,
    "dbscan": DBSCAN,
    "agglo": AgglomerativeClustering,
}

DIM_REDUCTION_MODELS = {
    "pca": PCA,
    "tsne": TSNE,
}

# ======================================================
# EZTRAINER
# ======================================================
class EZTrainer:
    """
    Core trainer class used by:
    - CLI (train / reduce)
    - Pipeline
    - Compiler (compile)
    """

    def __init__(
        self,
        data,
        target=None,
        model="random_forest",
        task="auto",
        test_size=0.2,
        scale=True,
        n_components=None,
        random_state=42
    ):
        self.target = target
        self.model_name = model
        self.task = task
        self.test_size = test_size
        self.scale = scale
        self.n_components = n_components
        self.random_state = random_state

        # Load data
        self.df = self._load_data(data)
        self._auto_detect_task()

        # Data containers
        self.X = None
        self.y = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None

        # ===== REQUIRED CONTRACT ATTRIBUTES =====
        self.pipeline = None        # full sklearn pipeline
        self.model = None           # trained estimator only
        self.y_pred = None          # predictions
        self.y_prob = None          # probabilities (if any)
        self.report = {}            # metrics
        self.transformed_data = None

    # ==================================================
    # INTERNAL HELPERS
    # ==================================================
    def _load_data(self, data):
        if isinstance(data, str):
            print(f"Loading data from {data}...")
            return pd.read_csv(data)
        elif isinstance(data, pd.DataFrame):
            print("Using provided DataFrame.")
            return data.copy()
        else:
            raise TypeError("Data must be a CSV path or pandas DataFrame.")

    def _auto_detect_task(self):
        if self.task != "auto":
            print(f"Task specified as: {self.task}")
            return

        if self.target:
            if self.target not in self.df.columns:
                raise ValueError(f"Target column '{self.target}' not found.")

            dtype = self.df[self.target].dtype
            uniq = self.df[self.target].nunique()

            if pd.api.types.is_numeric_dtype(dtype) and uniq > 20:
                self.task = "regression"
            else:
                self.task = "classification"

        elif self.model_name in CLUSTERING_MODELS:
            self.task = "clustering"
        elif self.model_name in DIM_REDUCTION_MODELS:
            self.task = "dim_reduction"
        else:
            raise ValueError("Could not auto-detect task.")

        print(f"Task specified as: {self.task}")

    def _get_preprocessor(self):
        numerical = self.X.select_dtypes(include=np.number).columns.tolist()
        categorical = self.X.select_dtypes(include=["object", "category"]).columns.tolist()

        print(f"Identified {len(numerical)} numerical features: {numerical}")
        print(f"Identified {len(categorical)} categorical features: {categorical}")

        num_steps = [("imputer", SimpleImputer(strategy="median"))]
        if self.scale:
            num_steps.append(("scaler", StandardScaler()))

        num_pipe = Pipeline(num_steps)
        cat_pipe = Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore"))
        ])

        return ColumnTransformer([
            ("num", num_pipe, numerical),
            ("cat", cat_pipe, categorical)
        ])

    # ==================================================
    # METRICS
    # ==================================================
    def _calculate_metrics(self):
        print("Calculating metrics...")

        if self.task == "classification":
            self.report = {
                "accuracy": accuracy_score(self.y_test, self.y_pred),
                "f1_score": f1_score(self.y_test, self.y_pred, average="weighted"),
                "confusion_matrix": confusion_matrix(self.y_test, self.y_pred).tolist()
            }

            if self.y_prob is not None:
                try:
                    if self.y_prob.ndim == 1:
                        self.report["roc_auc"] = roc_auc_score(self.y_test, self.y_prob)
                    else:
                        self.report["roc_auc"] = roc_auc_score(
                            self.y_test, self.y_prob, multi_class="ovr"
                        )
                except Exception:
                    self.report["roc_auc"] = None

        elif self.task == "regression":
            self.report = {
                "r2": r2_score(self.y_test, self.y_pred),
                "mae": mean_absolute_error(self.y_test, self.y_pred),
                "rmse": np.sqrt(mean_squared_error(self.y_test, self.y_pred))
            }

        elif self.task == "clustering":
            labels = self.pipeline.named_steps["model"].labels_
            self.report = {
                "n_clusters": len(set(labels)),
                "silhouette_score": silhouette_score(self.X, labels)
                if len(set(labels)) > 1 else None
            }

        print("Metrics report:")
        print(json.dumps(self.report, indent=4))

    # ==================================================
    # TRAIN
    # ==================================================
    def train(self):
        print(f"\n--- Starting Training for Task: {self.task.upper()} ---")

        if self.task in ["classification", "regression"]:
            self.X = self.df.drop(columns=[self.target])
            self.y = self.df[self.target]

            self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
                self.X,
                self.y,
                test_size=self.test_size,
                random_state=self.random_state
            )

            preprocessor = self._get_preprocessor()
            model_map = CLASSIFICATION_MODELS if self.task == "classification" else REGRESSION_MODELS

            ModelCls = model_map[self.model_name]
            model = (
                ModelCls(random_state=self.random_state)
                if "random_state" in ModelCls().get_params()
                else ModelCls()
            )

            self.pipeline = Pipeline([
                ("preprocessor", preprocessor),
                ("model", model)
            ])

            print(f"Training {self.model_name} model...")
            self.pipeline.fit(self.X_train, self.y_train)

            # ===== REQUIRED EXPORTS =====
            self.model = self.pipeline.named_steps["model"]
            self.y_pred = self.pipeline.predict(self.X_test)

            if hasattr(self.model, "predict_proba"):
                probs = self.pipeline.predict_proba(self.X_test)
                self.y_prob = probs[:, 1] if probs.shape[1] == 2 else probs
            else:
                self.y_prob = None

            self._calculate_metrics()

        elif self.task == "clustering":
            self.X = self.df.copy()
            preprocessor = self._get_preprocessor()
            model = CLUSTERING_MODELS[self.model_name]()

            self.pipeline = Pipeline([
                ("preprocessor", preprocessor),
                ("model", model)
            ])

            self.pipeline.fit(self.X)
            self.model = model
            self._calculate_metrics()

        elif self.task == "dim_reduction":
            self.X = self.df.copy()
            preprocessor = self._get_preprocessor()
            ModelCls = DIM_REDUCTION_MODELS[self.model_name]

            model = (
                ModelCls(n_components=self.n_components, random_state=self.random_state)
                if self.n_components else ModelCls(random_state=self.random_state)
            )

            self.pipeline = Pipeline([
                ("preprocessor", preprocessor),
                ("model", model)
            ])

            self.transformed_data = self.pipeline.fit_transform(self.X)
            self.model = model
            print(f"Data transformed into {self.transformed_data.shape[1]} dimensions.")

        else:
            raise ValueError(f"Task '{self.task}' not supported.")

        print("--- Training Complete ---")
        return self

    # ==================================================
    # UTILITIES
    # ==================================================
    def predict(self, X_new):
        if isinstance(X_new, str):
            X_new = pd.read_csv(X_new)
        return self.pipeline.predict(X_new)

    def save_model(self, path="model.pkl"):
        with open(path, "wb") as f:
            pickle.dump(self.pipeline, f)
        print(f"Model saved successfully to {path}")

    def save_report(self, path="report.json"):
        with open(path, "w") as f:
            json.dump(self.report, f, indent=4)
        print(f"Report saved successfully to {path}")

    def save_transformed(self, path="transformed_data.csv"):
        if self.transformed_data is None:
            raise RuntimeError("No transformed data available.")
        pd.DataFrame(self.transformed_data).to_csv(path, index=False)
        print(f"Transformed data saved to {path}")
