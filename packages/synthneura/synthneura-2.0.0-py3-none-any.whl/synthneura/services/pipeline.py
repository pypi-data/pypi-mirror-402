from typing import Any, Dict, List

from synthneura.core.logger import get_logger
from synthneura.core.schemas import ClinicalTrial

logger = get_logger(__name__)


def _as_list(x: Any) -> List[str]:
    """Coerce strings / lists / missing values into a list[str]."""
    if x is None:
        return []
    if isinstance(x, str):
        return [x]
    if isinstance(x, list):
        out: List[str] = []
        for item in x:
            if item is None:
                continue
            if isinstance(item, str):
                out.append(item)
            elif isinstance(item, dict):
                # Try common name fields
                name = item.get("name") or item.get("measure") or item.get("title")
                if name:
                    out.append(str(name))
            else:
                out.append(str(item))
        return out
    if isinstance(x, dict):
        # legacy containers like {"Condition": [...]}
        for key in ("Condition", "Intervention", "PrimaryOutcome"):
            if key in x:
                return _as_list(x.get(key))
        # fallback: stringify dict
        return [str(x)]
    return [str(x)]


def normalize_trial(raw_trial: Dict[str, Any]) -> ClinicalTrial:
    """
    Normalize raw trial data into the ClinicalTrial schema.
    Supports:
      - ClinicalTrials.gov API v2 (preferred)
      - Legacy v1 'FullStudies' shape (fallback)
    """
    # --- Detect v1 wrapper ---
    if "Study" in raw_trial:
        ps = raw_trial["Study"]["ProtocolSection"]

        nct_id = ps["IdentificationModule"]["NCTId"]
        title = ps["IdentificationModule"].get("BriefTitle") or ps[
            "IdentificationModule"
        ].get("OfficialTitle")
        status = ps.get("StatusModule", {}).get("OverallStatus")
        phase = ps.get("DesignModule", {}).get("Phase")
        sponsor = ps.get("SponsorModule", {}).get("LeadSponsor", {}).get("Name")

        conditions = _as_list(
            ps.get("ConditionsModule", {}).get("ConditionList", {}).get("Condition")
        )
        interventions = _as_list(
            ps.get("ArmsInterventionsModule", {})
            .get("InterventionList", {})
            .get("Intervention")
        )
        outcomes = _as_list(
            ps.get("OutcomesModule", {})
            .get("PrimaryOutcomeList", {})
            .get("PrimaryOutcome")
        )

        logger.debug(
            "Normalized v1 trial nct_id=%s title=%s", nct_id, (title or "")[:60]
        )

        return ClinicalTrial(
            nct_id=nct_id,
            title=title,
            status=status,
            phase=phase,
            sponsor=sponsor,
            conditions=conditions,
            interventions=interventions,
            outcomes=outcomes,
        )

    # --- v2 path ---
    ps = raw_trial.get("protocolSection", {}) or {}

    ident = ps.get("identificationModule", {}) or {}
    status_mod = ps.get("statusModule", {}) or {}
    design_mod = ps.get("designModule", {}) or {}
    sponsor_mod = ps.get("sponsorsModule", {}) or {}
    cond_mod = ps.get("conditionsModule", {}) or {}
    arms_mod = ps.get("armsInterventionsModule", {}) or {}
    outcomes_mod = ps.get("outcomesModule", {}) or {}

    nct_id = ident.get("nctId")
    title = ident.get("briefTitle") or ident.get("officialTitle")
    status = status_mod.get("overallStatus")

    phases = design_mod.get("phases")
    phase = ", ".join(_as_list(phases)) if phases else None

    sponsor = (sponsor_mod.get("leadSponsor", {}) or {}).get("name")

    conditions = _as_list(cond_mod.get("conditions"))
    interventions = _as_list(arms_mod.get("interventions"))

    primary_outcomes = outcomes_mod.get("primaryOutcomes")
    outcomes = _as_list(primary_outcomes)

    if not nct_id:
        logger.error(
            "Missing nctId in trial record. Keys=%s",
            list(raw_trial.keys()),
        )
        raise ValueError(
            "Missing nctId in trial record "
            "(unexpected ClinicalTrials.gov response shape)."
        )

    # Helpful warnings (non-fatal)
    if not title:
        logger.warning("Missing title for nct_id=%s", nct_id)
    if not status:
        logger.warning("Missing status for nct_id=%s", nct_id)

    logger.debug("Normalized v2 trial nct_id=%s title=%s", nct_id, (title or "")[:60])

    return ClinicalTrial(
        nct_id=nct_id,
        title=title,
        status=status,
        phase=phase,
        sponsor=sponsor,
        conditions=conditions,
        interventions=interventions,
        outcomes=outcomes,
    )
