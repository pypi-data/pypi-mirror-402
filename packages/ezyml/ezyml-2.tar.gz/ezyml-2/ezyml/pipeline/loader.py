# # ezyml/pipeline/loader.py

# import yaml
# from ezyml.core import EZTrainer
# from ezyml.pipeline.visualize import render_ascii_dag


# class Pipeline:
#     def __init__(self, steps, edges):
#         self.steps = steps
#         self.edges = edges
#         self.trainer = None

#     def run(self, data, target=None):
#         """
#         Execute the pipeline.
#         v1 assumption: last step is always EZTrainer.
#         """
#         if "trainer" not in self.steps:
#             raise ValueError("Pipeline must contain a 'trainer' step")

#         cfg = self.steps["trainer"]
#         params = cfg.get("params", {})

#         self.trainer = EZTrainer(
#             data=data,
#             target=target,
#             model=params.get("model"),
#             task="classification"
#         )

#         self.trainer.train()
#         return self.trainer


# def load_pipeline(path: str) -> Pipeline:
#     with open(path, "r") as f:
#         cfg = yaml.safe_load(f)

#     steps = cfg.get("steps", {})
#     edges = cfg.get("edges", [])

#     render_ascii_dag(steps.keys(), _edges_to_map(edges))
#     return Pipeline(steps=steps, edges=edges)


# def _edges_to_map(edges):
#     graph = {}
#     for src, dst in edges:
#         graph.setdefault(src, []).append(dst)
#     return graph

# ezyml/pipeline/loader.py

import yaml
from ezyml.core import EZTrainer
from ezyml.pipeline.visualize import render_ascii_dag


class Pipeline:
    def __init__(self, steps):
        self.steps = steps

    def run(self, data, target):
        cfg = self.steps["trainer"]
        params = cfg.get("params", {})

        trainer = EZTrainer(
            data=data,
            target=target,
            model=params.get("model", "random_forest"),
            task="classification"
        )
        trainer.train()
        return trainer


def load_pipeline(path):
    with open(path) as f:
        cfg = yaml.safe_load(f)

    steps = cfg.get("steps", {})
    render_ascii_dag(steps.keys(), {})
    return Pipeline(steps)
