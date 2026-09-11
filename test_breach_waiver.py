import ast
from pathlib import Path


def test_manual_breach_defaults_to_qualified_and_limits_access():
    source = Path("Commands/breach_waiver_view.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    values = {
        node.targets[0].id: ast.literal_eval(node.value)
        for node in tree.body
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "AUTHORIZED_BREACH_REVIEWERS"
    }
    assert values["AUTHORIZED_BREACH_REVIEWERS"] == {
        703335523925753903, 634761405299556352, 798523920747724800
    }
    assert "set(range(len(members)))" in source
    assert "set_breach_manual_waivers" in source
    assert "week_start + 604800" in source
    scheduler_source = Path("scheduler_jobs.py").read_text(encoding="utf-8")
    assert "get_breach_manual_waivers" in scheduler_source
