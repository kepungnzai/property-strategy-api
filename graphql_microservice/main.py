from strawberry.asgi import GraphQL
import strawberry
from dotenv import load_dotenv
import os
import google.cloud.aiplatform as aiplatform

load_dotenv()

PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION")
REASONING_ENGINE_ID = os.getenv("REASONING_ENGINE_ID")
MOCK_SERVICE = os.getenv("MOCK_SERVICE", "false").lower() == "true"

if not MOCK_SERVICE and PROJECT_ID and LOCATION:
    aiplatform.init(project=PROJECT_ID, location=LOCATION)


@strawberry.type
class AnalysisResponse:
    status: str
    analysis: str = None


@strawberry.type
class ReportResponse:
    status: str
    format: str
    content: str = None


@strawberry.type
class Query:
    @strawberry.field
    def health_check(self) -> str:
        return "GraphQL service is running"


@strawberry.type
class Mutation:
    @strawberry.mutation
    def analyze(self, location: str, property_type: str) -> AnalysisResponse:
        if MOCK_SERVICE:
            return AnalysisResponse(
                status="mock_success",
                analysis=f"Mock analysis for {property_type} in {location}",
            )
        engine = aiplatform.ReasoningEngine(REASONING_ENGINE_ID)
        response = engine.predict(
            {"location": location, "property_type": property_type}
        )
        return AnalysisResponse(status="success", analysis=str(response))

    @strawberry.mutation
    def generate_report(self, format: str = "html") -> ReportResponse:
        if MOCK_SERVICE:
            content = (
                "<html><body>Mock Report</body></html>"
                if format == "html"
                else "Dummy PDF Content"
            )
            return ReportResponse(status="mock_success", format=format, content=content)
        return ReportResponse(
            status="success", format=format, content=f"Generated {format} report"
        )


schema = strawberry.Schema(query=Query, mutation=Mutation)
app = GraphQL(schema)
