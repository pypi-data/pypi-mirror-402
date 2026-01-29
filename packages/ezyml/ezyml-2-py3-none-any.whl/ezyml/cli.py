# ezyml/cli.py

import argparse
import pandas as pd

from ezyml.core import EZTrainer
from ezyml.compiler.compile import compile_project
from ezyml.eda.auto_eda import auto_eda
from ezyml.monitoring.fingerprint import dataset_fingerprint


def compile_cli(args):
    print("\n--- EZYML :: COMPILE ---")

    df = pd.read_csv(args.data)

    if not args.no_eda:
        auto_eda(df, target=args.target)
        print("[EDA] Completed")

    # --------------------------------------------------
    # PIPELINE (OPTIONAL) OR FALLBACK TRAINER
    # --------------------------------------------------
    if args.pipeline:
        try:
            from ezyml.pipeline.loader import load_pipeline
        except ImportError:
            raise RuntimeError(
                "Pipeline support is not available in this installation.\n"
                "Either install ezyml with pipeline support or run without --pipeline."
            )

        pipeline = load_pipeline(args.pipeline)
        trainer = pipeline.run(df, target=args.target)

    else:
        print("[INFO] No pipeline provided. Using implicit EZTrainer.")
        trainer = EZTrainer(
            data=df,
            target=args.target,
            model=args.model,
            task="classification"
        )
        trainer.train()

    fingerprint = dataset_fingerprint(df)
    print(f"[FINGERPRINT] {fingerprint}")

    schema = {c: "number" for c in df.drop(columns=[args.target]).columns}

    # --all overrides everything
    api = args.api or args.all
    demo = args.demo or args.all
    docker = args.docker or args.all
    k8s = args.k8s or args.all

    compile_project(
        trainer=trainer,
        schema=schema,
        api=api,
        demo=demo,
        docker=docker,
        k8s=k8s
    )

    print("\n[SUCCESS] Compilation complete.")
    print("Generated:")
    print("  model.pkl")
    print("  metrics.json")
    if api: print("  app.py + openapi.json")
    if demo: print("  demo_app.py")
    if docker: print("  Dockerfile")
    if k8s: print("  k8s.yaml")


def main():
    parser = argparse.ArgumentParser("ezyml")
    sub = parser.add_subparsers(dest="command", required=True)

    compile_cmd = sub.add_parser("compile")
    compile_cmd.add_argument("--data", required=True)
    compile_cmd.add_argument("--target", required=True)

    # OPTIONAL
    compile_cmd.add_argument("--pipeline", required=False)
    compile_cmd.add_argument("--model", default="random_forest")

    compile_cmd.add_argument("--api", action="store_true")
    compile_cmd.add_argument("--demo", action="store_true")
    compile_cmd.add_argument("--docker", action="store_true")
    compile_cmd.add_argument("--k8s", action="store_true")
    compile_cmd.add_argument("--all", action="store_true")

    compile_cmd.add_argument("--no-eda", action="store_true")
    compile_cmd.set_defaults(func=compile_cli)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
