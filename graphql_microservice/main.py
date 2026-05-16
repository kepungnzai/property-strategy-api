from strawberry.asgi import GraphQL
import strawberry
from dotenv import load_dotenv
import os
import google.cloud.aiplatform as aiplatform
import asyncio
from typing import Optional, List
from agentic.client import ReasoningEngineClient
from database import find_report_by_location, find_reports_by_ids, parse_location_string
from profile import UserProfile
import uuid

load_dotenv()

PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION")
REASONING_ENGINE_ID = os.getenv("REASONING_ENGINE_ID")
MOCK_SERVICE = os.getenv("MOCK_SERVICE", "false").lower() == "true"

if not MOCK_SERVICE and PROJECT_ID and LOCATION:
    try:
        aiplatform.init(project=PROJECT_ID, location=LOCATION)
    except Exception as e:
        print(f"Warning: Failed to initialize AI Platform: {e}")



@strawberry.type
class AnalysisResponse:
    status: str
    analysis: Optional[str] = None
    source: Optional[str] = None


@strawberry.type
class ReportResponse:
    status: str
    format: str
    content: Optional[str] = None


@strawberry.type
class StreamResponse:
    status: str
    analysis: Optional[str] = None


@strawberry.type
class CompareResponse:
    status: str
    comparison: Optional[str] = None


@strawberry.input
class UserProfileInput:
    property_price: int
    property_price_increase: int
    proximity_amenities: int
    proximity_schools: int
    proximity_train_station: int
    natural_hazard_risk: int


@strawberry.type
class Query:
    @strawberry.field
    async def health_check(self) -> str:
        return "Property analysis GraphQL service is running"

    @strawberry.field
    async def analyze(self, location: str, property_type: str) -> AnalysisResponse:
        if MOCK_SERVICE:
            return AnalysisResponse(
                status="mock_success",
                analysis=f"Mock analysis for {property_type} in {location}",
            )

        report = await find_report_by_location(location)
        if report:
            return AnalysisResponse(
                status="success",
                analysis=report.current_analysis,
                source="database",
            )

        if not REASONING_ENGINE_ID:
            return AnalysisResponse(
                status="error",
                analysis="REASONING_ENGINE_ID environment variable is not set",
            )
        try:
            re = ReasoningEngineClient()
            full_response = ""
            async for event in re.send_query(
                message=f"Analyze {property_type} in {location}",
                user_id=str(uuid.uuid4()),
            ):
                full_response += str(event)

            return AnalysisResponse(status="success", analysis=full_response)
        except Exception as e:
            return AnalysisResponse(status="error", analysis=str(e))

    @strawberry.field
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

    @strawberry.field
    async def compare_property(
        self, property_ids: List[str], profile: UserProfileInput
    ) -> CompareResponse:
        if MOCK_SERVICE:
            return CompareResponse(
                status="mock_success",
                comparison=f"Mock comparison for properties: {', '.join(property_ids)}",
            )

        if not REASONING_ENGINE_ID:
            return CompareResponse(
                status="error",
                comparison="REASONING_ENGINE_ID environment variable is not set",
            )

        try:
            reports = await find_reports_by_ids(property_ids)
            if not reports:
                return CompareResponse(
                    status="error",
                    comparison="No properties found for the given IDs",
                )

            properties_data = [
                {
                    "id": r.id,
                    "location": f"{r.location.suburb}, {r.location.state}, {r.location.country}",
                    "property_type": r.property_type,
                    "current_analysis": r.current_analysis,
                }
                for r in reports
            ]

            profile_dict = {
                "property_price": profile.property_price,
                "property_price_increase": profile.property_price_increase,
                "proximity_amenities": profile.proximity_amenities,
                "proximity_schools": profile.proximity_schools,
                "proximity_train_station": profile.proximity_train_station,
                "natural_hazard_risk": profile.natural_hazard_risk,
            }

            re = ReasoningEngineClient()
            full_response = ""
            async for event in re.profile_analysis(
                properties=properties_data,
                profile=profile_dict,
                user_id=str(uuid.uuid4()),
            ):
                full_response += str(event)

            return CompareResponse(status="success", comparison=full_response)
        except Exception as e:
            return CompareResponse(status="error", comparison=str(e))


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def analyze_stream(self, location: str, property_type: str) -> StreamResponse:
        print(
            f"analyze_stream called with location={location}, property_type={property_type}"
        )

        if MOCK_SERVICE:
            numbers = [
                "100000000000000000000",
                "200000000000000000000",
                "300000000000000000000",
                "400000000000000000000",
                "500000000000000000000",
            ]
            for num in numbers:
                yield StreamResponse(status="success", analysis=num)
                await asyncio.sleep(1)
            return

        report = await find_report_by_location(location)
        if report:
            analysis = report.current_analysis
            for i in range(0, len(analysis), 100):
                chunk = analysis[i : i + 100]
                yield StreamResponse(status="success", analysis=chunk)
                await asyncio.sleep(0.1)
            return

        if not REASONING_ENGINE_ID:
            yield StreamResponse(
                status="error",
                analysis="REASONING_ENGINE_ID environment variable is not set",
            )
            return

        try:
            re = ReasoningEngineClient()
            async for event in re.send_query(
                message=f"Analyze {property_type} in {location}",
                user_id=str(uuid.uuid4()),
            ):
                event_str = str(event)
                for i in range(0, len(event_str), 100):
                    chunk = event_str[i : i + 100]
                    yield StreamResponse(status="success", analysis=chunk)
                    await asyncio.sleep(0.1)

        except Exception as e:
            yield StreamResponse(status="error", analysis=str(e))


schema = strawberry.Schema(query=Query, subscription=Subscription)
app = GraphQL(schema)
