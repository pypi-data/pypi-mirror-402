import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional


@dataclass(frozen=True)
class Settings:
    db_path: str
    sink: str
    log_level: str
    output_path: Optional[str]
    output_format: str
    summary_path: Optional[str]
    changes_path: Optional[str]
    max_results: int


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    db_path = os.getenv("SYNTHNEURA_DB_PATH", "trials.db")
    sink = os.getenv("SYNTHNEURA_SINK", "sqlite")
    log_level = os.getenv("SYNTHNEURA_LOG_LEVEL", "INFO")
    output_path = os.getenv("SYNTHNEURA_OUTPUT_PATH")
    output_format = os.getenv("SYNTHNEURA_OUTPUT_FORMAT", "json")
    summary_path = os.getenv("SYNTHNEURA_SUMMARY_PATH")
    changes_path = os.getenv("SYNTHNEURA_CHANGES_PATH")
    max_results_raw = os.getenv("SYNTHNEURA_MAX_RESULTS", "10")

    try:
        max_results = int(max_results_raw)
    except ValueError:
        max_results = 10

    return Settings(
        db_path=db_path,
        sink=sink,
        log_level=log_level,
        output_path=output_path,
        output_format=output_format,
        summary_path=summary_path,
        changes_path=changes_path,
        max_results=max_results,
    )
