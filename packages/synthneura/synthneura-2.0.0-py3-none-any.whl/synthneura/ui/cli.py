import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

import click

from synthneura.core.config import get_settings
from synthneura.core.logger import get_logger, set_log_level
from synthneura.ingestion.clinical_trials import fetch_trials
from synthneura.services.pipeline import normalize_trial
from synthneura.services.summary import summarize_trials
from synthneura.storage.sqlite_sink import SQLiteTrialSink

logger = get_logger(__name__)


def _trial_to_dict(trial: Any) -> Dict[str, Any]:
    if hasattr(trial, "model_dump"):
        return trial.model_dump()
    if hasattr(trial, "dict"):
        return trial.dict()
    return dict(trial)


def _write_json(path: Path, trials: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(trials, f, indent=2, ensure_ascii=True)


def _write_json_payload(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=True)


def _write_csv(path: Path, trials: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not trials:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = sorted({key for trial in trials for key in trial.keys()})
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(trials)


def _change_to_dict(change: Any) -> Dict[str, Any]:
    return {
        "nct_id": change.nct_id,
        "change_status": change.change_status,
        "changed_fields": change.changed_fields,
        "before": change.before,
        "after": change.after,
    }


@click.command()
@click.option("--query", required=True, help="Search query for clinical trials.")
@click.option(
    "--db-path",
    default=get_settings().db_path,
    show_default=True,
    help="Path to the SQLite database.",
)
@click.option(
    "--sink",
    default=get_settings().sink,
    show_default=True,
    type=click.Choice(["sqlite"], case_sensitive=False),
    help="Storage backend for persisted trials.",
)
@click.option(
    "--log-level",
    default=get_settings().log_level,
    show_default=True,
    type=click.Choice(
        ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], case_sensitive=False
    ),
    help="Logging verbosity.",
)
@click.option(
    "--max-results",
    default=get_settings().max_results,
    show_default=True,
    type=int,
    help="Maximum number of trials to fetch.",
)
@click.option(
    "--output-path",
    default=get_settings().output_path,
    help="Optional path to write results (JSON or CSV).",
)
@click.option(
    "--output-format",
    default=get_settings().output_format,
    show_default=True,
    type=click.Choice(["json", "csv"], case_sensitive=False),
    help="Output format when --output-path is provided.",
)
@click.option(
    "--summary-path",
    default=get_settings().summary_path,
    help="Optional path to write summary (JSON).",
)
@click.option(
    "--changes-path",
    default=get_settings().changes_path,
    help="Optional path to write change summary (JSON).",
)
@click.option(
    "--since-last-run",
    is_flag=True,
    help="When set, change summary uses diffs since the previous run.",
)
def run(
    query: str,
    db_path: str,
    sink: str,
    log_level: str,
    max_results: int,
    output_path: Optional[str],
    output_format: str,
    summary_path: Optional[str],
    changes_path: Optional[str],
    since_last_run: bool,
) -> None:
    """
    Run the SynthNeura pipeline to fetch, normalize, and store clinical trials.
    """
    # Set runtime log level for this run
    set_log_level(log_level)
    logger.info("Starting SynthNeura CLI run")
    logger.info(
        "query=%s sink=%s log_level=%s",
        query,
        sink.lower(),
        log_level.upper(),
    )

    click.echo(f"Fetching trials for query: {query}")

    try:
        raw_trials = fetch_trials(query, max_results=max_results)

        if not raw_trials:
            logger.warning("No trials returned from fetch_trials for query=%s", query)
            click.echo(
                f"No trials found for the query: {query}."
                f"Try a broader or different query."
            )
            return

        click.echo(f"Fetched {len(raw_trials)} trials.")
        logger.info("Fetched %d raw trials", len(raw_trials))

        stored = 0
        run_id = uuid4().hex
        ingested_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        run_meta = {
            "run_id": run_id,
            "ingested_at": ingested_at,
            "source": "clinicaltrials.gov",
            "query": query,
        }
        normalized_trials: List[Dict[str, Any]] = []
        trial_models = []
        for raw_trial in raw_trials:
            trial = normalize_trial(raw_trial)
            trial_models.append(trial)
            normalized_trials.append(_trial_to_dict(trial))

            # User-friendly output
            click.echo(
                f"- {trial.nct_id} | "
                f"{trial.status or 'UNKNOWN'} | "
                f"{trial.phase or 'NA'} | "
                f"{(trial.title or '')[:80]}"
            )

        if sink.lower() == "sqlite":
            sink_impl = SQLiteTrialSink(db_path)
        else:
            raise ValueError(f"Unsupported sink: {sink}")

        store_result = sink_impl.store_trials(trial_models, raw_trials, run_meta)
        change_counts = store_result.counts
        stored = len(trial_models)

        logger.info(
            "Completed run. stored=%d new=%d updated=%d unchanged=%d",
            stored,
            change_counts["new"],
            change_counts["updated"],
            change_counts["unchanged"],
        )
        click.echo("Pipeline completed successfully.")

        summary = summarize_trials(
            normalized_trials, run_meta=run_meta, change_counts=change_counts
        )
        summary_dict = _trial_to_dict(summary)

        click.echo(
            f"Summary: total={summary.total_trials} "
            f"status_count={len(summary.status_counts)} "
            f"phase_count={len(summary.phase_counts)} "
            f"new={change_counts['new']} "
            f"updated={change_counts['updated']} "
            f"unchanged={change_counts['unchanged']}"
        )

        if output_path:
            path = Path(output_path)
            if output_format.lower() == "json":
                _write_json_payload(
                    path, {"summary": summary_dict, "trials": normalized_trials}
                )
            else:
                _write_csv(path, normalized_trials)
            logger.info("Wrote output %s to %s", output_format.lower(), path)
            click.echo(f"Wrote {output_format.lower()} output to {path}")

        if summary_path:
            summary_file = Path(summary_path)
        elif output_path and output_format.lower() == "csv":
            summary_file = Path(f"{output_path}.summary.json")
        else:
            summary_file = None

        if summary_file:
            _write_json_payload(summary_file, summary_dict)
            logger.info("Wrote summary to %s", summary_file)
            click.echo(f"Wrote summary to {summary_file}")

        if since_last_run and sink.lower() == "sqlite":
            previous_time = sink_impl.fetch_previous_run_time(run_id)
            change_records = [
                _change_to_dict(change)
                for change in sink_impl.fetch_diffs_between(
                    previous_time, run_meta["ingested_at"]
                )
            ]
        else:
            change_records = [
                _change_to_dict(change) for change in store_result.changes
            ]
        change_records.sort(
            key=lambda record: len(record.get("changed_fields", [])), reverse=True
        )
        changes_payload = {
            "run": run_meta,
            "changes": change_records,
            "top_changed": change_records[:5],
        }

        if changes_path:
            changes_file = Path(changes_path)
        elif output_path:
            changes_file = Path(f"{output_path}.changes.json")
        else:
            changes_file = None

        if changes_file:
            _write_json_payload(changes_file, changes_payload)
            logger.info("Wrote change summary to %s", changes_file)
            click.echo(f"Wrote change summary to {changes_file}")

    except ValueError as e:
        logger.warning("ValueError during run: %s", e)
        click.echo(f"Error: {e}")
    except Exception as e:
        logger.exception("Unexpected error during run")
        click.echo(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    run()
