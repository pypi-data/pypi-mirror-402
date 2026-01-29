import json
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from synthneura.core.logger import get_logger
from synthneura.core.schemas import ClinicalTrial
from synthneura.storage.base import ChangeRecord, RunMeta, StoreResult, TrialSink

logger = get_logger(__name__)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ensure_schema(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS clinical_trials (
            nct_id TEXT PRIMARY KEY,
            title TEXT,
            status TEXT,
            phase TEXT,
            sponsor TEXT,
            conditions TEXT,
            interventions TEXT,
            outcomes TEXT,
            raw_json TEXT,
            source TEXT,
            query TEXT,
            ingested_at TEXT,
            run_id TEXT
        )
        """
    )
    conn.commit()

    cursor.execute("PRAGMA table_info(clinical_trials)")
    existing = {row[1] for row in cursor.fetchall()}
    expected = {
        "raw_json",
        "source",
        "query",
        "ingested_at",
        "run_id",
    }
    missing = expected - existing
    for column in sorted(missing):
        cursor.execute(f"ALTER TABLE clinical_trials ADD COLUMN {column} TEXT")
    if missing:
        conn.commit()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS clinical_trials_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nct_id TEXT,
            title TEXT,
            status TEXT,
            phase TEXT,
            sponsor TEXT,
            conditions TEXT,
            interventions TEXT,
            outcomes TEXT,
            raw_json TEXT,
            source TEXT,
            query TEXT,
            ingested_at TEXT,
            run_id TEXT,
            valid_from TEXT,
            valid_to TEXT
        )
        """
    )
    conn.commit()

    cursor.execute("PRAGMA table_info(clinical_trials_history)")
    existing_history = {row[1] for row in cursor.fetchall()}
    expected_history = {
        "nct_id",
        "title",
        "status",
        "phase",
        "sponsor",
        "conditions",
        "interventions",
        "outcomes",
        "raw_json",
        "source",
        "query",
        "ingested_at",
        "run_id",
        "valid_from",
        "valid_to",
    }
    missing_history = expected_history - existing_history
    for column in sorted(missing_history):
        cursor.execute(f"ALTER TABLE clinical_trials_history ADD COLUMN {column} TEXT")
    if missing_history:
        conn.commit()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS runs (
            run_id TEXT PRIMARY KEY,
            ingested_at TEXT,
            source TEXT,
            query TEXT,
            total INTEGER,
            new_count INTEGER,
            updated_count INTEGER,
            unchanged_count INTEGER,
            failed_count INTEGER
        )
        """
    )
    conn.commit()

    cursor.execute("PRAGMA table_info(runs)")
    existing_runs = {row[1] for row in cursor.fetchall()}
    expected_runs = {
        "ingested_at",
        "source",
        "query",
        "total",
        "new_count",
        "updated_count",
        "unchanged_count",
        "failed_count",
    }
    missing_runs = expected_runs - existing_runs
    for column in sorted(missing_runs):
        column_type = "INTEGER"
        if column in {"ingested_at", "source", "query"}:
            column_type = "TEXT"
        cursor.execute(f"ALTER TABLE runs ADD COLUMN {column} {column_type}")
    if missing_runs:
        conn.commit()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS trial_diffs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nct_id TEXT,
            run_id TEXT,
            ingested_at TEXT,
            changed_fields TEXT,
            before_json TEXT,
            after_json TEXT
        )
        """
    )
    conn.commit()

    cursor.execute("PRAGMA table_info(trial_diffs)")
    existing_diffs = {row[1] for row in cursor.fetchall()}
    expected_diffs = {
        "nct_id",
        "run_id",
        "ingested_at",
        "changed_fields",
        "before_json",
        "after_json",
    }
    missing_diffs = expected_diffs - existing_diffs
    for column in sorted(missing_diffs):
        cursor.execute(f"ALTER TABLE trial_diffs ADD COLUMN {column} TEXT")
    if missing_diffs:
        conn.commit()

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_clinical_trials_nct_id
        ON clinical_trials(nct_id)
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_clinical_trials_history_nct_id_valid_from
        ON clinical_trials_history(nct_id, valid_from)
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_trial_diffs_nct_id_ingested_at
        ON trial_diffs(nct_id, ingested_at)
        """
    )
    conn.commit()


def _trial_core_values(trial: ClinicalTrial) -> Tuple[Optional[str], ...]:
    return (
        trial.title,
        trial.status,
        trial.phase,
        trial.sponsor,
        ",".join(trial.conditions or []),
        ",".join(trial.interventions or []),
        ",".join(trial.outcomes or []),
    )


def _core_to_dict(core: Tuple[Optional[str], ...]) -> Dict[str, Any]:
    return {
        "title": core[0],
        "status": core[1],
        "phase": core[2],
        "sponsor": core[3],
        "conditions": core[4],
        "interventions": core[5],
        "outcomes": core[6],
    }


def _changed_fields(
    existing: Tuple[Optional[str], ...], updated: Tuple[Optional[str], ...]
) -> List[str]:
    fields = [
        "title",
        "status",
        "phase",
        "sponsor",
        "conditions",
        "interventions",
        "outcomes",
    ]
    changed: List[str] = []
    for idx, field in enumerate(fields):
        existing_value = existing[idx] or ""
        updated_value = updated[idx] or ""
        if existing_value != updated_value:
            changed.append(field)
    return changed


def _raw_nct_id(raw_trial: Dict[str, Any]) -> Optional[str]:
    if "Study" in raw_trial:
        return (
            raw_trial.get("Study", {})
            .get("ProtocolSection", {})
            .get("IdentificationModule", {})
            .get("NCTId")
        )
    return (
        raw_trial.get("protocolSection", {})
        .get("identificationModule", {})
        .get("nctId")
    )


class SQLiteTrialSink(TrialSink):
    def __init__(self, db_path: str = "trials.db") -> None:
        self.db_path = db_path

    def fetch_previous_run_time(self, current_run_id: str) -> Optional[str]:
        conn = sqlite3.connect(self.db_path)
        try:
            _ensure_schema(conn)
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT ingested_at
                FROM runs
                WHERE run_id != ?
                ORDER BY ingested_at DESC
                LIMIT 1
                """,
                (current_run_id,),
            )
            row = cursor.fetchone()
        finally:
            conn.close()
        if row:
            return row[0]
        return None

    def fetch_diffs_between(
        self, start_time: Optional[str], end_time: Optional[str]
    ) -> List[ChangeRecord]:
        if not end_time:
            return []
        conn = sqlite3.connect(self.db_path)
        try:
            _ensure_schema(conn)
            cursor = conn.cursor()
            if start_time:
                cursor.execute(
                    """
                    SELECT nct_id, changed_fields, before_json, after_json
                    FROM trial_diffs
                    WHERE ingested_at > ? AND ingested_at <= ?
                    ORDER BY ingested_at DESC
                    """,
                    (start_time, end_time),
                )
            else:
                cursor.execute(
                    """
                    SELECT nct_id, changed_fields, before_json, after_json
                    FROM trial_diffs
                    WHERE ingested_at <= ?
                    ORDER BY ingested_at DESC
                    """,
                    (end_time,),
                )
            rows = cursor.fetchall()
        finally:
            conn.close()

        changes: List[ChangeRecord] = []
        for row in rows:
            nct_id, changed_fields_json, before_json, after_json = row
            changes.append(
                ChangeRecord(
                    nct_id=nct_id,
                    change_status="updated",
                    changed_fields=json.loads(changed_fields_json or "[]"),
                    before=json.loads(before_json or "{}"),
                    after=json.loads(after_json or "{}"),
                )
            )
        return changes

    def store_trials(
        self,
        trials: List[ClinicalTrial],
        raw_trials: List[Dict[str, Any]],
        run_meta: RunMeta,
    ) -> StoreResult:
        logger.debug("Storing %d trials in SQLite db=%s", len(trials), self.db_path)

        raw_by_id = {}
        for raw_trial in raw_trials:
            nct_id = _raw_nct_id(raw_trial)
            if nct_id:
                raw_by_id[nct_id] = raw_trial

        counts = {"new": 0, "updated": 0, "unchanged": 0, "failed": 0}
        changes: List[ChangeRecord] = []
        conn = sqlite3.connect(self.db_path)
        try:
            _ensure_schema(conn)
            cursor = conn.cursor()
            for trial in trials:
                cursor.execute(
                    """
                    SELECT
                        title,
                        status,
                        phase,
                        sponsor,
                        conditions,
                        interventions,
                        outcomes,
                        raw_json,
                        source,
                        query,
                        ingested_at,
                        run_id
                    FROM clinical_trials
                    WHERE nct_id = ?
                    """,
                    (trial.nct_id,),
                )
                existing = cursor.fetchone()
                existing_core = existing[:7] if existing else None
                existing_raw_json = existing[7] if existing else None
                existing_source = existing[8] if existing else None
                existing_query = existing[9] if existing else None
                existing_ingested_at = existing[10] if existing else None
                existing_run_id = existing[11] if existing else None
                new_core = _trial_core_values(trial)

                if existing is None:
                    change_status = "new"
                elif existing_core == new_core:
                    change_status = "unchanged"
                else:
                    change_status = "updated"

                ingested_at_value = run_meta.get("ingested_at") or _utc_now()
                if change_status == "unchanged" and existing_ingested_at:
                    ingested_at_value = existing_ingested_at
                raw_json = json.dumps(
                    raw_by_id.get(trial.nct_id, {}), ensure_ascii=True
                )
                if trial.nct_id not in raw_by_id and existing_raw_json is not None:
                    raw_json = existing_raw_json
                if change_status == "updated" and existing is not None:
                    changed_fields = _changed_fields(
                        existing_core or new_core, new_core
                    )
                    before = _core_to_dict(existing_core or new_core)
                    after = _core_to_dict(new_core)
                    changes.append(
                        ChangeRecord(
                            nct_id=trial.nct_id,
                            change_status=change_status,
                            changed_fields=changed_fields,
                            before=before,
                            after=after,
                        )
                    )
                    cursor.execute(
                        """
                        INSERT INTO trial_diffs
                        (
                            nct_id,
                            run_id,
                            ingested_at,
                            changed_fields,
                            before_json,
                            after_json
                        )
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            trial.nct_id,
                            run_meta.get("run_id"),
                            ingested_at_value,
                            json.dumps(changed_fields, ensure_ascii=True),
                            json.dumps(before, ensure_ascii=True),
                            json.dumps(after, ensure_ascii=True),
                        ),
                    )
                    (
                        existing_title,
                        existing_status,
                        existing_phase,
                        existing_sponsor,
                        existing_conditions,
                        existing_interventions,
                        existing_outcomes,
                    ) = (
                        existing_core or new_core
                    )
                    cursor.execute(
                        """
                        INSERT INTO clinical_trials_history
                        (
                            nct_id,
                            title,
                            status,
                            phase,
                            sponsor,
                            conditions,
                            interventions,
                            outcomes,
                            raw_json,
                            source,
                            query,
                            ingested_at,
                            run_id,
                            valid_from,
                            valid_to
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            trial.nct_id,
                            existing_title,
                            existing_status,
                            existing_phase,
                            existing_sponsor,
                            existing_conditions,
                            existing_interventions,
                            existing_outcomes,
                            existing_raw_json,
                            existing_source,
                            existing_query,
                            existing_ingested_at,
                            existing_run_id,
                            existing_ingested_at,
                            ingested_at_value,
                        ),
                    )
                if change_status != "unchanged":
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO clinical_trials
                        (
                            nct_id,
                            title,
                            status,
                            phase,
                            sponsor,
                            conditions,
                            interventions,
                            outcomes,
                            raw_json,
                            source,
                            query,
                            ingested_at,
                            run_id
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            trial.nct_id,
                            trial.title,
                            trial.status,
                            trial.phase,
                            trial.sponsor,
                            ",".join(trial.conditions or []),
                            ",".join(trial.interventions or []),
                            ",".join(trial.outcomes or []),
                            raw_json,
                            run_meta.get("source"),
                            run_meta.get("query"),
                            ingested_at_value,
                            run_meta.get("run_id"),
                        ),
                    )
                counts[change_status] += 1
            conn.commit()
            run_id = run_meta.get("run_id")
            if run_id:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO runs
                    (
                        run_id,
                        ingested_at,
                        source,
                        query,
                        total,
                        new_count,
                        updated_count,
                        unchanged_count,
                        failed_count
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        run_id,
                        run_meta.get("ingested_at"),
                        run_meta.get("source"),
                        run_meta.get("query"),
                        len(trials),
                        counts["new"],
                        counts["updated"],
                        counts["unchanged"],
                        counts["failed"],
                    ),
                )
                conn.commit()
        finally:
            conn.close()
        return StoreResult(counts=counts, changes=changes)
