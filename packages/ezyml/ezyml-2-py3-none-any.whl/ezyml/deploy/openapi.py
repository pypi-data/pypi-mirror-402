import json

def generate_openapi_spec(schema, output_path="openapi.json"):
    """
    Generates a minimal OpenAPI-style input schema.
    """
    spec = {
        "title": "ezyml-model-api",
        "type": "object",
        "properties": {
            k: {"type": "number"} for k in schema.keys()
        },
        "required": list(schema.keys())
    }

    with open(output_path, "w") as f:
        json.dump(spec, f, indent=2)

    return output_path
