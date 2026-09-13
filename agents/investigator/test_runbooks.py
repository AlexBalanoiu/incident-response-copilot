import re
from pathlib import Path

RUNBOOK_DIR = Path(__file__).parent.parent.parent / "knowledge_base" / "runbooks"
REQUIRED_SECTIONS = ["## Symptoms", "## Likely Causes", "## Diagnostic Steps", "## Remediation"]
EXPECTED_SCENARIOS = {
    "pod_crash", "cpu_spike", "memory_leak",
    "db_connection_exhaustion", "slow_query", "disk_pressure",
}


def test_all_expected_runbooks_exist():
    found = {f.stem for f in RUNBOOK_DIR.glob("*.md")}
    assert found == EXPECTED_SCENARIOS


def test_each_runbook_has_required_sections_and_frontmatter():
    for path in RUNBOOK_DIR.glob("*.md"):
        text = path.read_text()
        assert re.search(r"^---\nscenario: \w+\nservice_type: \w+\n---", text), f"{path.name} missing frontmatter"
        for section in REQUIRED_SECTIONS:
            assert section in text, f"{path.name} missing {section}"