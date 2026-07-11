# Domain Intelligence v1.0

A clean, modular backend for investigating candidate `.com` domains and returning evidence to ChatGPT.

This service does **not** make the final acquisition decision. It gathers reliable evidence; ChatGPT applies your rubric and master feedback file.

## Architecture

```text
API
 ├── Evidence Collector
 ├── Marketplace Detector
 ├── Company-Use Detector
 ├── Classifier
 ├── Feedback Store
 └── Regression Tests
```

## Main endpoint

### `POST /investigate`

Input:

```json
{
  "names": ["Resolve", "Harbor", "Courseback"]
}
```

Output:

- DNS status
- HTTP status
- redirect chain
- final URL
- cross-domain redirect
- marketplace/sale URL evidence
- explicit sale phrases
- sparse/coming-soon/parking evidence
- operating-company evidence
- suggested classification
- confidence
- explanation

## Classification options

- `for sale`
- `likely for sale`
- `check manually`
- `not for sale`

## Setup locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DOMAIN_API_KEY="choose-a-long-secret"
uvicorn app.main:app --reload --port 8000
```

Open:

```text
http://127.0.0.1:8000/docs
```

## Deploy on Render

Build command:

```text
pip install -r requirements.txt
```

Start command:

```text
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Render supplies `$PORT` automatically.

## Tests

```bash
pytest
```

Regression cases include:

- GoDaddy `/forsale/` redirect → `for sale`
- generic cross-domain redirect → `likely for sale`
- sparse `coming soon` → `likely for sale`
- strong operating-company evidence → `not for sale`

## ChatGPT Action

Use `openapi.yaml` after replacing:

```text
https://YOUR-SERVICE.onrender.com
```

with your deployed service URL.

## Feedback

The service supports exact overrides through:

```text
data/domain_feedback_master.csv
```

Columns:

- domain
- corrected_classification
- reviewer_note

Exact feedback overrides the automated classifier.
