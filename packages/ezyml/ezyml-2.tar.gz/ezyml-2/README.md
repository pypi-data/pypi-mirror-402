<div align="center">

# 📦 ezyml 🚀

### **Version 2.0**

**From raw data to a deployable ML system — in one command.**

<a href="https://github.com/Rktim/ezyml/blob/main/LICENSE">
  <img alt="License" src="https://img.shields.io/github/license/Rktim/ezyml?color=blue">
</a>
<img alt="Python Versions" src="https://img.shields.io/pypi/pyversions/ezyml?logo=python&logoColor=white">
<img alt="Version" src="https://img.shields.io/badge/version-2.0-success">

[![PyPI Downloads](https://static.pepy.tech/badge/ezyml)](https://pepy.tech/projects/ezyml)

</div>

---

## 🚀 What’s New in v2.0

**ezyml 2.0 is a major architectural upgrade.**
It is no longer just a trainer — it is a **machine‑learning compiler**.

### 🆕 Major Additions

* 🧠 **`ezyml compile`** – one command to generate models, metrics, APIs, demos, and infra
* 🧩 **Pipeline‑Driven Execution** – YAML‑based pipelines with visual DAGs
* 🎛 **User‑Controlled Artifacts** – generate *only* what you ask for
* 📊 **Auto‑EDA + Evaluator** – dataset profiling, metrics, plots
* 🧪 **Production‑Ready Demos** – high‑quality Streamlit UI generation
* 📦 **Deployment Tooling** – FastAPI, Docker, Kubernetes YAML
* 🔍 **Dataset Fingerprinting** – reproducibility by design

---

## 🌟 Why ezyml?

**ezyml** removes boilerplate across the *entire* ML lifecycle:

> dataset → training → evaluation → deployment → demo

All without forcing you into a framework lock‑in.

### Core Philosophy

* **Explicit over magic** – nothing is generated unless you ask
* **Beginner‑friendly, expert‑capable**
* **Composable, inspectable, debuggable**

---

## 📦 Installation

```bash
pip install ezyml==2.0.0
```

---

## 🚀 CLI Quickstart

Below are the **most common ways users interact with ezyml** — via the CLI or Python API.

---

### 🧠 Train a Model (CLI – v1 compatible)

```bash
ezyml train \
  --data data.csv \
  --target label \
  --model random_forest
```

This trains a model and prints evaluation metrics.

---

### 🧩 Compile an End-to-End ML System (CLI – v2.0)

**Minimal (no pipeline, no extras):**

```bash
ezyml compile \
  --data heart.csv \
  --target target
```

Generates:

```
build/
├── model.pkl
└── metrics.json
```

---

### 🎛 Compile With Explicit Outputs

```bash
ezyml compile \
  --data heart.csv \
  --target target \
  --api \
  --demo \
  --docker \
  --k8s
```

Each flag enables a specific artifact:

* `--api` → FastAPI inference app
* `--demo` → Interactive Streamlit demo
* `--docker` → Dockerfile
* `--k8s` → Kubernetes manifests

---

### 🧩 Compile Using a YAML Pipeline (Advanced)

```bash
ezyml compile \
  --pipeline pipeline.yaml \
  --data heart.csv \
  --target target \
  --all
```

---

### 🧩 Compile a Full ML System (v2.0)

```bash
ezyml compile \
  --pipeline pipeline.yaml \
  --data data.csv \
  --target label
```

**Default output (minimal):**

```
build/
├── model.pkl
└── metrics.json
```

---

### 🎛 User‑Controlled Outputs

```bash
ezyml compile \
  --pipeline pipeline.yaml \
  --data data.csv \
  --target label \
  --api \
  --demo \
  --docker \
  --k8s
```

---

## 🧪 Pipeline Example (YAML)

```yaml
steps:
  trainer:
    type: EZTrainer
    params:
      model: random_forest
      target: label
```

---

## 🧠 Python API (Still Supported)

You can use **ezyml programmatically** without the CLI.

### Basic Training

```python
from ezyml.core import EZTrainer

trainer = EZTrainer(
    data="heart.csv",
    target="target",
    model="random_forest"
)

trainer.train()
trainer.save_model("model.pkl")
trainer.save_report("metrics.json")
```

---

### Predictions in Python

```python
import pandas as pd
from ezyml.core import EZTrainer

trainer = EZTrainer(data="heart.csv", target="target")
trainer.train()

X_new = pd.read_csv("new_samples.csv")
preds = trainer.predict(X_new)
print(preds)
```

---

### Using ezyml as a Library Component

```python
from ezyml.compiler.compile import compile_project
from ezyml.core import EZTrainer

trainer = EZTrainer(data="heart.csv", target="target")
trainer.train()

compile_project(
    trainer=trainer,
    schema={"age": "number", "chol": "number"},
    api=True,
    demo=True
)
```

---

## 📊 Evaluation & Analytics

* Accuracy, F1, ROC‑AUC (classification)
* MAE, RMSE, R² (regression)
* Confusion matrix, ROC & PR curves
* Drift‑ready metric storage

---

## 📦 Deployment Targets

| Layer         | Supported  |
| ------------- | ---------- |
| API           | FastAPI    |
| Demo          | Streamlit  |
| Container     | Docker     |
| Orchestration | Kubernetes |

---

## 🧰 Supported Models

| Task           | Models                                                                                             |
| -------------- | -------------------------------------------------------------------------------------------------- |
| Classification | logistic_regression, random_forest, xgboost, svm, naive_bayes, gradient_boosting, extra_trees, knn |
| Regression     | linear_regression, ridge, lasso, elasticnet, random_forest, xgboost, svr, gradient_boosting        |
| Clustering     | kmeans, dbscan, agglo                                                                              |
| Dim Reduction  | pca, tsne                                                                                          |

---

## 🔮 Roadmap

* Learner Mode (explain decisions)
* SHAP‑based explainability
* Model comparison dashboards
* Presets (`--preset production`)
* CI/CD & MLOps integrations

---

## 📜 License

MIT License – [View License](https://github.com/Rktim/ezyml/blob/main/LICENSE)

---

## 👨‍💻 Author

Built with ❤️ by **Raktim Kalita**
GitHub: [https://github.com/Rktim](https://github.com/Rktim)
