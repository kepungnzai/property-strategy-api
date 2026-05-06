# GraphQL Property Location Strategy Microservice

## Prerequisites
- Python 3.9+
- GCP account with Vertex AI enabled (if not using mock)

## Install Dependencies
```bash
pip install .
```

## Configure Environment
Copy `.env.example` to `.env` and fill in your values:
```bash
cp .env.example .env
```

## Run Service
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
Service runs on `http://localhost:8000/graphql`

## GraphQL Endpoint
`POST /graphql`

### Example Mutations
```graphql
 query { 
  analyze(location: "loc", propertyType: "type")
  { status analysis } 
}

 query { 
    generateReport(format: "html") { 
      status format content 
    } 
  }

```
