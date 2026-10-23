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
    assert "load_saved_qualified" in source
    assert "Xác nhận không có Breach" in source
    assert 'mode="no_breach"' in source
    command_source = Path("Commands/user_commands_slash.py").read_text(encoding="utf-8")
    assert "BreachWaiverView(interaction.guild.id, members, qualified, mode=mode)" in command_source
    scheduler_source = Path("scheduler_jobs.py").read_text(encoding="utf-8")
    assert "get_breach_manual_waivers" in scheduler_source
    assert "paid_set | waived_set" in scheduler_source
    assert 'member.get("donations", 0)' in scheduler_source
    main_source = Path("main.py").read_text(encoding="utf-8")
    assert main_source.count("CronTrigger(day_of_week=1") >= 2
