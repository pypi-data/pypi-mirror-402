def generate_dockerfile(output_path="Dockerfile"):
    """
    Generates a minimal Dockerfile for FastAPI deployment.
    """
    dockerfile = """
FROM python:3.10-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir fastapi uvicorn scikit-learn numpy

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
"""
    with open(output_path, "w") as f:
        f.write(dockerfile)

    return output_path
