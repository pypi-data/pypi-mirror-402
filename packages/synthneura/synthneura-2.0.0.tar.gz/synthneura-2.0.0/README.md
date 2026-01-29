# 🧬 SynthNeura

SynthNeura is an early-stage, modular AI and data-engineering platform designed to accelerate clinical research, pharmaceutical intelligence, and personalized medicine.

Core objective:
SynthNeura is built to become a reliable pharma intelligence engine, not just a scraper or a chatbot. It autonomously ingests biomedical data, normalizes it into structured knowledge, and produces reliable, repeatable insights for research, strategy, and decision-making.

Built with a production-grade engineering mindset: clean architecture, strict linting, automated CI/CD, and reproducible workflows.

---

## 🚀 Current Capabilities (V2)

### 🔍 Clinical Trials Ingestion
- Fetches trials from ClinicalTrials.gov (API v2)
- Normalizes heterogeneous responses into a clean internal schema
- Handles missing fields and unexpected response shapes
- Persists structured data to SQLite for local analysis
- Tracks run metadata and stores change history

### 🧱 Normalization & Storage Pipeline
- Strongly typed domain model (`ClinicalTrial`)
- Robust normalization for legacy + modern API formats
- Schema-safe inserts with idempotent upserts
- Storage abstraction via sinks (SQLite default)
- History table for prior versions of updated trials

### 🖥️ Command Line Interface (CLI)

Run the full pipeline:

```bash
python -m synthneura.ui.cli --query "lung cancer"
```

Write results to JSON or CSV:

```bash
python -m synthneura.ui.cli --query "lung cancer" --output-path out.json
python -m synthneura.ui.cli --query "lung cancer" --output-path out.csv --output-format csv
```

Select a storage backend (SQLite only for now):

```bash
python -m synthneura.ui.cli --query "lung cancer" --sink sqlite --db-path trials.db
```

CLI features:
- Configurable logging levels
- Clear user-friendly output
- Structured debug logs for developers
- Summary stats generated from live trial data
- Change detection (new vs updated vs unchanged)
- Change summaries (top changed trials + changed fields)

Logging notes:
- `--log-level` controls all module loggers and handlers for the current run.

Output notes:
- JSON outputs include `summary` and `trials`.
- CSV outputs write trials to the CSV and a summary file at `<output>.summary.json` (or pass `--summary-path`).
- Change summaries are written to `<output>.changes.json` when `--output-path` is set (or pass `--changes-path`).
- Use `--since-last-run` to emit diffs since the previous run when writing change summaries.

---

## 🗄️ SQLite Storage Schema

Tables created automatically in the SQLite database:

- `clinical_trials` (latest state)
  - `nct_id` (primary key)
  - normalized fields: `title`, `status`, `phase`, `sponsor`, `conditions`, `interventions`, `outcomes`
  - `raw_json` (full payload)
  - `source`, `query`, `ingested_at`, `run_id`

- `clinical_trials_history` (prior versions on update)
  - same fields as `clinical_trials`
  - `valid_from`, `valid_to`

- `runs` (run metadata + counts)
  - `run_id`, `ingested_at`, `source`, `query`
  - `total`, `new_count`, `updated_count`, `unchanged_count`, `failed_count`

- `trial_diffs` (field-level changes for updates)
  - `nct_id`, `run_id`, `ingested_at`
  - `changed_fields`, `before_json`, `after_json`

Use cases:
- `clinical_trials` answers "what is the latest state?"
- `clinical_trials_history` answers "what changed and when?"
- `runs` answers "what happened in each run?"
- `trial_diffs` answers "which fields changed and how?"

Indexes:
- `clinical_trials(nct_id)`
- `clinical_trials_history(nct_id, valid_from)`
- `trial_diffs(nct_id, ingested_at)`

---

## ⚙️ Settings (Environment Variables)

- `SYNTHNEURA_DB_PATH` (default: `trials.db`)
- `SYNTHNEURA_SINK` (default: `sqlite`)
- `SYNTHNEURA_LOG_LEVEL` (default: `INFO`)
- `SYNTHNEURA_OUTPUT_PATH` (default: unset)
- `SYNTHNEURA_OUTPUT_FORMAT` (default: `json`)
- `SYNTHNEURA_SUMMARY_PATH` (default: unset)
- `SYNTHNEURA_CHANGES_PATH` (default: unset)
- `SYNTHNEURA_MAX_RESULTS` (default: `10`)

Example:

```bash
export SYNTHNEURA_DB_PATH="data/trials.db"
export SYNTHNEURA_SINK="sqlite"
export SYNTHNEURA_MAX_RESULTS=50
python -m synthneura.ui.cli --query "lung cancer"
```

---

## 🧪 Engineering & Quality Standards

Formatting and linting:
- Black
- isort
- Ruff
- Flake8
- Mypy

All checks are enforced via pre-commit hooks locally and in CI.

---

## 🔄 CI/CD Pipeline

Branch strategy:
- `feature/*` / `dev/*` → active development
- `main` → QA / staging
- Releases → production

Pipeline behavior:
- Every push / PR runs pre-commit + tests
- Merge to `main` triggers QA deployment
- Release published triggers production deployment

---

## 🛠️ Developer Workflow

Common commands:

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all linting & checks (same as CI)
make lint

# Auto-format code
make format

# Run tests
make test
```

Commit flow:

```bash
git add -A
git commit -m "Meaningful message"
git push
```

---

## 🧠 Design Philosophy

- Explicit typing
- Clear boundaries between ingestion, normalization, and storage
- Fail-fast behavior for invalid or unexpected data
- Minimal but extensible architecture

## 🔭 Long-Term Vision

- Multi-source biomedical data ingestion
- AI-driven analysis (GNNs, transformers, recommendation systems)
- Scalable APIs and enterprise-ready deployments
