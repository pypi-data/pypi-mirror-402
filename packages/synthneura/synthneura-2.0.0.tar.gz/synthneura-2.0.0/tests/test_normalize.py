from synthneura.services.pipeline import normalize_trial


def test_normalize_trial_v2() -> None:
    raw = {
        "protocolSection": {
            "identificationModule": {
                "nctId": "NCT00000001",
                "briefTitle": "Test Trial",
            },
            "statusModule": {"overallStatus": "COMPLETED"},
            "designModule": {"phases": ["PHASE1", "PHASE2"]},
            "sponsorsModule": {"leadSponsor": {"name": "Acme Pharma"}},
            "conditionsModule": {"conditions": ["Condition A", "Condition B"]},
            "armsInterventionsModule": {"interventions": ["Drug X"]},
            "outcomesModule": {"primaryOutcomes": [{"measure": "Overall Survival"}]},
        }
    }

    trial = normalize_trial(raw)

    assert trial.nct_id == "NCT00000001"
    assert trial.title == "Test Trial"
    assert trial.status == "COMPLETED"
    assert trial.phase == "PHASE1, PHASE2"
    assert trial.sponsor == "Acme Pharma"
    assert trial.conditions == ["Condition A", "Condition B"]
    assert trial.interventions == ["Drug X"]
    assert trial.outcomes == ["Overall Survival"]


def test_normalize_trial_v1() -> None:
    raw = {
        "Study": {
            "ProtocolSection": {
                "IdentificationModule": {
                    "NCTId": "NCT00000002",
                    "BriefTitle": "Legacy Trial",
                },
                "StatusModule": {"OverallStatus": "RECRUITING"},
                "DesignModule": {"Phase": "PHASE3"},
                "SponsorModule": {"LeadSponsor": {"Name": "Legacy Sponsor"}},
                "ConditionsModule": {
                    "ConditionList": {"Condition": ["Legacy Condition"]}
                },
                "ArmsInterventionsModule": {
                    "InterventionList": {"Intervention": [{"name": "Legacy Drug"}]}
                },
                "OutcomesModule": {
                    "PrimaryOutcomeList": {
                        "PrimaryOutcome": [{"measure": "Progression-Free Survival"}]
                    }
                },
            }
        }
    }

    trial = normalize_trial(raw)

    assert trial.nct_id == "NCT00000002"
    assert trial.title == "Legacy Trial"
    assert trial.status == "RECRUITING"
    assert trial.phase == "PHASE3"
    assert trial.sponsor == "Legacy Sponsor"
    assert trial.conditions == ["Legacy Condition"]
    assert trial.interventions == ["Legacy Drug"]
    assert trial.outcomes == ["Progression-Free Survival"]
