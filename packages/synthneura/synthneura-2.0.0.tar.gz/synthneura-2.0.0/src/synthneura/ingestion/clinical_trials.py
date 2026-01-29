from typing import Any, Dict, List

import requests

from synthneura.core.logger import get_logger

CTG_V2_STUDIES_URL = "https://clinicaltrials.gov/api/v2/studies"

logger = get_logger(__name__)


def fetch_trials(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Fetch clinical trials from ClinicalTrials.gov API v2.
    Returns a list of study objects (dicts).
    """
    logger.info("Fetching ClinicalTrials.gov trials")
    logger.debug("Query=%s max_results=%s", query, max_results)

    params: dict[str, str] = {
        "query.term": query,
        "pageSize": str(max_results),
        "format": "json",
        "countTotal": "true",
    }

    try:
        response = requests.get(
            CTG_V2_STUDIES_URL,
            params=params,
            timeout=30,
        )
    except requests.RequestException as exc:
        logger.exception("HTTP request to ClinicalTrials.gov failed")
        raise RuntimeError("Failed to contact ClinicalTrials.gov") from exc

    logger.info(
        "ClinicalTrials.gov response status=%s url=%s",
        response.status_code,
        response.url,
    )

    content_type = response.headers.get("Content-Type", "")
    if "text/html" in content_type.lower():
        logger.error(
            "Received HTML instead of JSON (status=%s). Response preview=%s",
            response.status_code,
            response.text[:200],
        )
        raise ValueError(
            f"ClinicalTrials.gov returned HTML (not JSON). "
            f"Status={response.status_code}. Check endpoint/params."
        )

    try:
        response.raise_for_status()
    except requests.HTTPError:
        logger.error(
            "HTTP error from ClinicalTrials.gov status=%s body=%s",
            response.status_code,
            response.text[:200],
        )
        raise

    data = response.json()
    studies = data.get("studies", [])

    if not studies:
        logger.warning("No trials found for query=%s", query)
        raise ValueError(f"No trials found for query: {query}")

    logger.info("Fetched %d trials from ClinicalTrials.gov", len(studies))
    return studies
