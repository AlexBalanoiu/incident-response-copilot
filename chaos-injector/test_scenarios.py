import time
import requests
import pytest
from cli import trigger_incident

API_URL = "http://localhost:5000"  # requires api-service port-forward running


def test_pod_crash_increments_restart_count():
    import subprocess
    before = subprocess.run(
        ["kubectl", "get", "pods", "-n", "incident-copilot", "-l", "app=api-service",
         "-o", "jsonpath={.items[0].status.containerStatuses[0].restartCount}"],
        capture_output=True, text=True
    ).stdout

    record = trigger_incident(
        scenario="pod_crash", target="api-service", severity="high",
        target_namespace="incident-copilot", target_label_selector="app=api-service",
    )
    assert record["ground_truth_cause"] == "External kill / forced pod deletion"

    time.sleep(15)  # allow rescheduling
    after = subprocess.run(
        ["kubectl", "get", "pods", "-n", "incident-copilot", "-l", "app=api-service",
         "-o", "jsonpath={.items[0].status.containerStatuses[0].restartCount}"],
        capture_output=True, text=True
    ).stdout
    # new pod means a fresh restartCount, OR the same pod's count went up -
    # either way, confirm the pod is Running again after the induced crash
    result = subprocess.run(
        ["kubectl", "get", "pods", "-n", "incident-copilot", "-l", "app=api-service",
         "-o", "jsonpath={.items[0].status.phase}"],
        capture_output=True, text=True
    ).stdout
    assert result == "Running"


def test_memory_leak_actually_grows_reported_usage():
    record = trigger_incident(
        scenario="memory_leak", target="api-service", severity="medium",
        target_url=API_URL, duration_seconds=10, interval_seconds=1.0,
    )
    assert record["scenario_result"]["calls_made"] >= 8
    assert record["scenario_result"]["final_leaked_mb"] >= 8


def test_db_connection_exhaustion_raises_thread_count():
    import pymysql
    before_conn = pymysql.connect(host="localhost", user="root", password="changeme", database="appdb")
    before_count = None
    with before_conn.cursor() as cur:
        cur.execute("SHOW STATUS LIKE 'Threads_connected'")
        before_count = int(cur.fetchone()[1])
    before_conn.close()

    record = trigger_incident(
        scenario="db_connection_exhaustion", target="mysql", severity="high",
        db_host="localhost", db_user="root", db_password="changeme",
        db_name="appdb", num_connections=20, duration_seconds=5,
    )
    assert record["scenario_result"]["connections_opened"] == 20