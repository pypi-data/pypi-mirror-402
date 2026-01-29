from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List

from synthneura.core.schemas import ClinicalTrial

RunMeta = Dict[str, str]


@dataclass(frozen=True)
class ChangeRecord:
    nct_id: str
    change_status: str
    changed_fields: List[str]
    before: Dict[str, Any]
    after: Dict[str, Any]


@dataclass(frozen=True)
class StoreResult:
    counts: Dict[str, int]
    changes: List[ChangeRecord]


class TrialSink(ABC):
    @abstractmethod
    def store_trials(
        self,
        trials: List[ClinicalTrial],
        raw_trials: List[Dict[str, Any]],
        run_meta: RunMeta,
    ) -> StoreResult:
        """
        Persist trials and return counts for new/updated/unchanged/failed.
        """
        raise NotImplementedError
