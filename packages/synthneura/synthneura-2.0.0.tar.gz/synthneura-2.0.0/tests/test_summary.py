from synthneura.services.summary import summarize_trials


def test_summarize_trials() -> None:
    trials = [
        {
            "status": "COMPLETED",
            "phase": "PHASE2",
            "conditions": ["Condition A", "Condition B"],
            "sponsor": "Acme",
            "interventions": ["Drug X"],
        },
        {
            "status": "TERMINATED",
            "phase": "PHASE1",
            "conditions": ["Condition A"],
            "sponsor": "Acme",
            "interventions": ["Drug X", "Drug Y"],
        },
    ]

    summary = summarize_trials(trials)

    assert summary.total_trials == 2
    assert summary.status_counts == {"COMPLETED": 1, "TERMINATED": 1}
    assert summary.phase_counts == {"PHASE2": 1, "PHASE1": 1}
    assert summary.change_counts == {}
    assert summary.top_conditions[0].value == "Condition A"
    assert summary.top_conditions[0].count == 2
    assert summary.top_sponsors[0].value == "Acme"
    assert summary.top_sponsors[0].count == 2
    assert summary.top_interventions[0].value == "Drug X"
    assert summary.top_interventions[0].count == 2
