# GraphQL Property Location Strategy Microservice

## Prerequisites
- Python 3.9+
- GCP account with Vertex AI enabled (if not using mock)

## Install Dependencies
```bash
pip install -r requirements.txt
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
Service runs on `http://localhost:8000/graphql`

## GraphQL Endpoint
`POST /graphql`

### Example Mutations
```graphql
mutation {
  analyze(location: "New York", propertyType: "Residential") {
    status
    analysis
  }
}

mutation {
  generateReport(format: "html") {
    status
    format
    content
  }
}
```
