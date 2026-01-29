import os

def init_project(name):
    os.makedirs(name, exist_ok=True)
    for d in ["data","pipelines","models","artifacts"]:
        os.makedirs(f"{name}/{d}", exist_ok=True)
