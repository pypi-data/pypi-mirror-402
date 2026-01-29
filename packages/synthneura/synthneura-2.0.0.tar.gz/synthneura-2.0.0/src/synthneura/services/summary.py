from collections import Counter
from typing import Any, Dict, Iterable, List, Optional

from synthneura.core.schemas import Summary, TopCount


def _as_str_list(values: Iterable[Any]) -> List[str]:
    out: List[str] = []
    for value in values:
        if value is None:
            continue
        if isinstance(value, str):
            if value.strip():
                out.append(value.strip())
            continue
        if isinstance(value, list):
            out.extend(_as_str_list(value))
            continue
        out.append(str(value))
    return out


def _top_counts(values: Iterable[str], limit: int = 5) -> List[TopCount]:
    counts = Counter(values)
    return [
        TopCount(value=value, count=count) for value, count in counts.most_common(limit)
    ]


def summarize_trials(
    trials: List[Dict[str, Any]],
    *,
    run_meta: Optional[Dict[str, str]] = None,
    change_counts: Optional[Dict[str, int]] = None,
) -> Summary:
    statuses = _as_str_list(trial.get("status") for trial in trials)
    phases = _as_str_list(trial.get("phase") for trial in trials)
    sponsors = _as_str_list(trial.get("sponsor") for trial in trials)

    conditions: List[str] = []
    interventions: List[str] = []
    for trial in trials:
        conditions.extend(_as_str_list(trial.get("conditions", [])))
        interventions.extend(_as_str_list(trial.get("interventions", [])))

    run_meta = run_meta or {}

    return Summary(
        total_trials=len(trials),
        status_counts=dict(Counter(statuses)),
        phase_counts=dict(Counter(phases)),
        top_conditions=_top_counts(conditions),
        top_sponsors=_top_counts(sponsors),
        top_interventions=_top_counts(interventions),
        change_counts=change_counts or {},
        run_id=run_meta.get("run_id"),
        ingested_at=run_meta.get("ingested_at"),
        source=run_meta.get("source"),
        query=run_meta.get("query"),
    )
