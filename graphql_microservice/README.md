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
 uvicorn graphql_microservice.main:app --reload --host 0.0.0.0 --port 8000
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

subscription {
  analyzeStream(location: "New York", propertyType: "Residential") {
    status
    analysis
  }
}

query {
  compareProperty(
    property_ids: ["abc123", "def456"],
    profile: {
      property_price: 4,
      property_price_increase: 5,
      proximity_amenities: 3,
      proximity_schools: 4,
      proximity_train_station: 5,
      natural_hazard_risk: 2
    }
  ) {
    status
    comparison
  }
}


mutation {
  saveReport(
    report: {
      location: {
        suburb: "St Albans"
        state: "Melbourne"
        country: "Australia"
      }
      property_type: "House"
      current_analysis: "Property analysis details..."
    }
  ) {
    status
    id
    location
    property_type
    current_analysis
  }
}

mutation {
  saveReport(
    report: {
      location: {
        suburb: "St Albans"
        state: "Melbourne"
        country: "Australia"
      }
      propertyType: "House"
      currentAnalysis: "Property analysis details..."
    }
  ) {
    status
    id
    location
    propertyType
    currentAnalysis
  }
}



```
1. ensure the microservice support mongodb and add the production grade trial tested library.
i want to ensure when user call the graphql endpoint, the business logic performs a checks on locations for example St Albans, Melbourne, Australia and look up database container call reports by matching location which needs to be suburb, state, country (this might change). Suggest a best possible matching approach given that we are passing in a string "St Albans, Melbourne, Australia".

If a match is found, then pull the record out from the mongodb container. 

If it is a matched then 
  If it is /analyze endpoint return the results 
  if it is /analyze/stream then return the results by stream 100 character at a time or suggest a suitable. 

if we cannot find a match, pass it to the agentic agent to perform analysis 
  If it is /analyze endpoint return the results 
  if it is /analyze/stream then return the results by stream 100 character at a time or suggest a suitable. 

The report container is structures 
- id 
- location 
- property type 
- current analysis 

2. introduce another endpoint called /compareProperty that accepts an array of id - property_id_compare (id for records stored already in the database )
   the aim of this function is to pull records from mongodb and then pass these into agentic/client which will have a new function call profile_analysis to compare these records pass in as the property structure above and a profile.  Please create a user profile class which captures what is important for the users.  The profile looks like 

   1. Property price (Results will come in stars from 5 to 1)
   2. Property price increase (Results will come in stars from 5 to 1)
   3. Proximity to anemities (Results will come in stars from 5 to 1)
   4. Proximity to reputable school  (Results will come in stars from 5 to 1)
   5. Proximity to train station 
   6. Possible flood or bush fire 

in the graphql endpoint, please expose another service that allows me to 
1. save a report into database 
2  retrieve a report from the database 
The report container is structures 
- id 
- location 
- property type 
- current analysis 