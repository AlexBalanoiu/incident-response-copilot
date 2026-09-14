import subprocess
import time
import requests

_current_proc = None


def ensure_api_service_reachable(namespace: str = "incident-copilot", timeout: float = 15.0) -> None:
    """
    kubectl port-forward binds to whichever pod backs a service at the moment
    the forward starts - it does not follow the service to a new pod. Chaos
    scenarios that delete the api-service pod (e.g. pod_crash) kill any
    existing tunnel, so later scenarios needing http://localhost:5000 (e.g.
    memory_leak) can find it pointing at a pod that no longer exists.

    Call this right before any scenario run that needs live HTTP access to
    api-service - it's a no-op if the current tunnel is already healthy.
    """
    global _current_proc

    def _healthy() -> bool:
        try:
            resp = requests.get("http://localhost:5000/health", timeout=2)
            return resp.status_code == 200
        except requests.RequestException:
            return False

    if _healthy():
        return

    # existing tunnel is dead - kill it and start a fresh one
    if _current_proc is not None:
        _current_proc.terminate()
        _current_proc.wait(timeout=5)

    _current_proc = subprocess.Popen(
        ["kubectl", "port-forward", "-n", namespace, "svc/api-service", "5000:5000"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )

    start = time.monotonic()
    while time.monotonic() - start < timeout:
        if _healthy():
            return
        time.sleep(0.5)

    raise RuntimeError("api-service port-forward did not become healthy in time")
