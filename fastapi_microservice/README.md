# FastAPI Property Location Strategy Microservice

## Prerequisites
- Python 3.9+
- GCP account with Vertex AI enabled (if not using mock)

## Install Dependencies
```bash
uv pip install .
```

## Configure Environment
Copy `.env.example` to `.env` and fill in your values:
```bash
cp .env.example .env
```

## Run Service
```bash
uvicorn main:app --reload
```
Service runs on `http://localhost:8000`

## Endpoints
- `POST /analyze?location=<string>&property_type=<string>`: Analyze property location
- `GET /report?format=html|pdf`: Generate property report
