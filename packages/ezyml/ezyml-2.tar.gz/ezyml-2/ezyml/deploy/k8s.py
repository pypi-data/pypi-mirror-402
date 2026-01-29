import yaml

def generate_k8s_manifests(
    app_name,
    image,
    port=8000,
    replicas=1,
    namespace="default",
    output_prefix="k8s",
    with_ingress=False,
    ingress_host=None
):
    """
    Generates Kubernetes YAML manifests for ezyml models.
    """

    deployment = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": app_name,
            "namespace": namespace
        },
        "spec": {
            "replicas": replicas,
            "selector": {
                "matchLabels": {"app": app_name}
            },
            "template": {
                "metadata": {
                    "labels": {"app": app_name}
                },
                "spec": {
                    "containers": [{
                        "name": app_name,
                        "image": image,
                        "ports": [{"containerPort": port}],
                        "resources": {
                            "requests": {
                                "cpu": "250m",
                                "memory": "256Mi"
                            },
                            "limits": {
                                "cpu": "500m",
                                "memory": "512Mi"
                            }
                        }
                    }]
                }
            }
        }
    }

    service = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": f"{app_name}-svc",
            "namespace": namespace
        },
        "spec": {
            "selector": {"app": app_name},
            "ports": [{
                "protocol": "TCP",
                "port": 80,
                "targetPort": port
            }],
            "type": "ClusterIP"
        }
    }

    manifests = [deployment, service]

    if with_ingress:
        if not ingress_host:
            raise ValueError("ingress_host must be provided if with_ingress=True")

        ingress = {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "Ingress",
            "metadata": {
                "name": f"{app_name}-ingress",
                "namespace": namespace
            },
            "spec": {
                "rules": [{
                    "host": ingress_host,
                    "http": {
                        "paths": [{
                            "path": "/",
                            "pathType": "Prefix",
                            "backend": {
                                "service": {
                                    "name": f"{app_name}-svc",
                                    "port": {"number": 80}
                                }
                            }
                        }]
                    }
                }]
            }
        }
        manifests.append(ingress)

    # Write individual files
    with open(f"{output_prefix}_deployment.yaml", "w") as f:
        yaml.safe_dump(deployment, f)

    with open(f"{output_prefix}_service.yaml", "w") as f:
        yaml.safe_dump(service, f)

    # Write combined file
    with open(f"{output_prefix}.yaml", "w") as f:
        yaml.safe_dump_all(manifests, f)

    if with_ingress:
        with open(f"{output_prefix}_ingress.yaml", "w") as f:
            yaml.safe_dump(ingress, f)

    return {
        "deployment": f"{output_prefix}_deployment.yaml",
        "service": f"{output_prefix}_service.yaml",
        "combined": f"{output_prefix}.yaml",
        "ingress": f"{output_prefix}_ingress.yaml" if with_ingress else None
    }
