# from pathlib import Path
# from ezyml.deploy import (
#     generate_fastapi_app,
#     generate_dockerfile,
#     generate_openapi_spec,
#     generate_streamlit_app,
#     generate_k8s_manifests
# )

# def compile_project(
#     model,
#     pipeline,
#     schema,
#     image_name="ezyml-model",
#     replicas=1,
#     with_demo=True,
#     with_k8s=True,
#     build_dir="build"
# ):
#     """
#     One-command ML system compiler.
#     """

#     build_dir = Path(build_dir)
#     build_dir.mkdir(exist_ok=True)

#     # ---- Core artifacts ----
#     model_path = build_dir / "model.pkl"
#     pipeline_path = build_dir / "pipeline.pkl"

#     import pickle
#     pickle.dump(model, open(model_path, "wb"))
#     pickle.dump(pipeline, open(pipeline_path, "wb"))

#     # ---- API & Docs ----
#     generate_fastapi_app(model_path, schema, output_path=build_dir / "app.py")
#     generate_openapi_spec(schema, output_path=build_dir / "openapi.json")

#     # ---- Demo ----
#     if with_demo:
#         generate_streamlit_app(model_path, schema, output_path=build_dir / "demo_app.py")

#     # ---- Docker ----
#     generate_dockerfile(output_path=build_dir / "Dockerfile")

#     # ---- Kubernetes ----
#     if with_k8s:
#         generate_k8s_manifests(
#             app_name=image_name,
#             image=f"{image_name}:latest",
#             replicas=replicas,
#             output_prefix=build_dir / "k8s"
#         )

#     return {
#         "model": model_path,
#         "pipeline": pipeline_path,
#         "api": build_dir / "app.py",
#         "dockerfile": build_dir / "Dockerfile",
#         "openapi": build_dir / "openapi.json",
#         "k8s": build_dir / "k8s.yaml" if with_k8s else None
#     }
# ezyml/compiler/compile.py

from pathlib import Path
import pickle
import json

from ezyml.deploy import (
    generate_fastapi_app,
    generate_dockerfile,
    generate_openapi_spec,
    generate_streamlit_app,
    generate_k8s_manifests
)

def compile_project(
    trainer,
    schema,
    build_dir="build",
    api=False,
    demo=False,
    docker=False,
    k8s=False,
    plots=False
):
    build_dir = Path(build_dir)
    build_dir.mkdir(exist_ok=True)

    # --------------------------------------------------
    # ALWAYS GENERATED (MINIMUM CONTRACT)
    # --------------------------------------------------
    model_path = build_dir / "model.pkl"
    metrics_path = build_dir / "metrics.json"

    with open(model_path, "wb") as f:
        pickle.dump(trainer.pipeline, f)

    with open(metrics_path, "w") as f:
        json.dump(trainer.report, f, indent=2)

    # --------------------------------------------------
    # OPTIONAL OUTPUTS
    # --------------------------------------------------
    if api:
        generate_fastapi_app(
            model_path=model_path,
            schema=schema,
            output_path=build_dir / "app.py"
        )
        generate_openapi_spec(schema, output_path=build_dir / "openapi.json")

    if demo:
        generate_streamlit_app(
            model_path=model_path,
            schema=schema,
            output_path=build_dir / "demo_app.py"
        )

    if docker:
        generate_dockerfile(output_path=build_dir / "Dockerfile")

    if k8s:
        generate_k8s_manifests(
            app_name="ezyml-model",
            image="ezyml-model:latest",
            output_prefix=build_dir / "k8s"
        )

    return {
        "model": model_path,
        "metrics": metrics_path,
        "api": api,
        "demo": demo,
        "docker": docker,
        "k8s": k8s
    }
