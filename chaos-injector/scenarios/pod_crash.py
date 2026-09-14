from kubernetes import client, config

def run(target_namespace: str, target_label_selector: str, **kwargs) -> dict:
    """
    Deletes the target pod to simulate an external kill / crash.
    Kubernetes will reschedule it via the Deployment controller.
    """
    config.load_kube_config()
    v1 = client.CoreV1Api()

    pods = v1.list_namespaced_pod(target_namespace, label_selector=target_label_selector)
    if not pods.items:
        raise RuntimeError(f"No pods found matching {target_label_selector} in {target_namespace}")

    pod_name = pods.items[0].metadata.name
    v1.delete_namespaced_pod(pod_name, target_namespace)

    return {"deleted_pod": pod_name, "mechanism": "forced pod deletion"}