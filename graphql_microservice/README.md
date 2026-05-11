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

query { 
  getReport(reportId: "69ffb02965244429466456ec")
  { status , currentAnalysis } 
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
      userId: "123"
    }
  ) {
    status
    id
    location
    propertyType
    currentAnalysis
  }
}

query GetReportsByUserId($userId: String!, $limit: Int) {
  getReportsByUserId(userId: $userId, limit: $limit) {
    status
    userId
    reports {
      id
      location
      propertyType
      currentAnalysis
    }
  }
}


Variables 

{
  "userId": "123",
  "limit": 10
}


# Get User Profile
query GetUserProfile($userId: String!) {
  getUserProfile(userId: $userId) {
    status
    userId
    user_profile_criteria {
      property_price
      property_price_increase
      proximity_amenities
      proximity_schools
      proximity_train_station
      natural_hazard_risk
    }
  }
}

# Variables
{
  "userId": "123"
}

# Save User Profile

query GetUserProfile($userId: String!) {
  getUserProfile(userId: $userId) {
    status
    userId
     userProfileCriteria {
      propertyPrice
      propertyPriceIncrease
      proximityAmenities
      proximitySchools
      proximityTrainStation
      naturalHazardRisk
    }
  }
}

# Variables
{
  "userId": "123"
}


mutation {
  saveUserReport(
    userId: "user123",
    reportId: "507f1f77bcf86cd799439011"
  ) {
    status
    userId
    reportId
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

In the get_reports_by_user_id the implementation is not quite right, it needs to be update to retrieve from a new collection called userReport which contains reportId, userId, creationTime. When this function is called 1. we will retrieve data from  userReport by userId. Then based on reportId, it will retrieve the relevant report from report collections. Then we will return response as userId and list of RetrievedReport.

Create 2 additional endpoint for saveUserProfile and getUserProfile to save userProfile into a new db collection call userProfile. The userProfile should have the following structure:

- userId
- userProfileCriteria which reference 

- class UserProfileInput:
    property_price: int
    property_price_increase: int
    proximity_amenities: int
    proximity_schools: int
    proximity_train_station: int
    natural_hazard_risk: int

getUserProfile endpoint accept userId and returns a response which contains userId and list of UserProfileInput.
saveUserPrfile endpoint accept userId and UserProfileInput (single) 
please provide implementations for both

Implement saveUserReport which accept userId, reportId that persist data into userReport (this collections store user association to a report)
please provide validation to ensure reportId exist first before writting to the database. 