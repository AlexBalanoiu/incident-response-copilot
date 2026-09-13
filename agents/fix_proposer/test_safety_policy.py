from safety_policy import validate_fix_safety


def test_safe_rollout_restart_passes():
    result = validate_fix_safety("kubectl rollout restart deployment/api-service --dry-run=client")
    assert result["status"] == "safe"
    assert result["violations"] == []


def test_delete_namespace_blocked():
    result = validate_fix_safety("kubectl delete namespace incident-copilot")
    assert result["status"] == "unsafe"
    assert any("namespace" in v["reason"] for v in result["violations"])


def test_force_delete_blocked():
    result = validate_fix_safety("kubectl delete pod my-pod --force --grace-period=0")
    assert result["status"] == "unsafe"


def test_pvc_delete_blocked():
    result = validate_fix_safety("kubectl delete pvc mysql-data")
    assert result["status"] == "unsafe"


def test_drop_table_blocked():
    result = validate_fix_safety("Run: DROP TABLE incidents;")
    assert result["status"] == "unsafe"


def test_yaml_scale_manifest_passes():
    yaml_fix = """
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: api-service
    spec:
      replicas: 3
    """
    result = validate_fix_safety(yaml_fix)
    assert result["status"] == "safe"