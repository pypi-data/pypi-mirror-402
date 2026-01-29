import json
import sqlite3
from pathlib import Path

from synthneura.core.schemas import ClinicalTrial
from synthneura.storage.sqlite_sink import SQLiteTrialSink


def test_store_trial_change_detection(tmp_path: Path) -> None:
    db_path = str(tmp_path / "trials.db")
    trial = ClinicalTrial(
        nct_id="NCT00000003",
        title="Test Trial",
        status="RECRUITING",
        phase="PHASE1",
        sponsor="Acme",
        conditions=["A"],
        interventions=["Drug X"],
        outcomes=["Outcome 1"],
    )

    sink = SQLiteTrialSink(db_path)
    result_new = sink.store_trials(
        [trial],
        [],
        {
            "run_id": "run-1",
            "ingested_at": "2026-01-01T00:00:00Z",
            "source": "clinicaltrials.gov",
            "query": "cancer",
        },
    )
    assert result_new.counts["new"] == 1

    result_same = sink.store_trials(
        [trial],
        [],
        {
            "run_id": "run-2",
            "ingested_at": "2026-01-01T01:00:00Z",
            "source": "clinicaltrials.gov",
            "query": "cancer",
        },
    )
    assert result_same.counts["unchanged"] == 1

    if hasattr(trial, "model_copy"):
        updated_trial = trial.model_copy(update={"status": "COMPLETED"})
    else:
        updated_trial = trial.copy(update={"status": "COMPLETED"})
    result_updated = sink.store_trials(
        [updated_trial],
        [],
        {
            "run_id": "run-3",
            "ingested_at": "2026-01-01T02:00:00Z",
            "source": "clinicaltrials.gov",
            "query": "cancer",
        },
    )
    assert result_updated.counts["updated"] == 1
    assert result_updated.changes
    assert result_updated.changes[0].before["status"] == "RECRUITING"
    assert result_updated.changes[0].after["status"] == "COMPLETED"

    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT nct_id, status, valid_from, valid_to
            FROM clinical_trials_history
            WHERE nct_id = ?
            """,
            (trial.nct_id,),
        )
        row = cursor.fetchone()
        cursor.execute(
            """
            SELECT nct_id, changed_fields, before_json, after_json
            FROM trial_diffs
            WHERE nct_id = ?
            """,
            (trial.nct_id,),
        )
        diff_row = cursor.fetchone()
    finally:
        conn.close()

    assert row is not None
    assert row[1] == "RECRUITING"
    assert row[2] == "2026-01-01T00:00:00Z"
    assert row[3] == "2026-01-01T02:00:00Z"
    assert diff_row is not None
    changed_fields = json.loads(diff_row[1])
    before = json.loads(diff_row[2])
    after = json.loads(diff_row[3])
    assert "status" in changed_fields
    assert before["status"] == "RECRUITING"
    assert after["status"] == "COMPLETED"

    previous_time = sink.fetch_previous_run_time("run-3")
    diffs = sink.fetch_diffs_between(previous_time, "2026-01-01T02:00:00Z")
    assert diffs
    assert diffs[0].before["status"] == "RECRUITING"
    assert diffs[0].after["status"] == "COMPLETED"
