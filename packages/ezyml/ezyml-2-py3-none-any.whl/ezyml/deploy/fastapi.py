def generate_fastapi_app(model_path, schema, output_path="app.py"):
    """
    Generates a FastAPI inference server.
    Assumes sklearn-compatible model.
    """
    code = f'''
from fastapi import FastAPI
import pickle
import numpy as np

app = FastAPI()

with open("{model_path}", "rb") as f:
    model = pickle.load(f)

FEATURES = {list(schema.keys())}

@app.post("/predict")
def predict(payload: dict):
    try:
        X = np.array([[payload[f] for f in FEATURES]])
        pred = model.predict(X)[0]
        return {{"prediction": int(pred)}}
    except Exception as e:
        return {{"error": str(e)}}
'''
    with open(output_path, "w") as f:
        f.write(code)

    return output_path
