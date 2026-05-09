from strawberry.asgi import GraphQL
import strawberry
from dotenv import load_dotenv
import os
import google.cloud.aiplatform as aiplatform
import asyncio
from typing import Optional, List
from graphql_microservice.agentic.client import ReasoningEngineClient
from graphql_microservice.database import (
    find_report_by_location,
    find_reports_by_ids,
    find_report_by_id,
    create_report,
    Location,
    ReportCreate,
)
from graphql_microservice.profile import UserProfile
import uuid
import logging
import sys

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)

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
    flood_bushfire_risk: int


@strawberry.input
class LocationInput:
    suburb: str
    state: str
    country: str


@strawberry.input
class ReportInput:
    location: LocationInput
    property_type: str
    current_analysis: str


@strawberry.type
class SavedReport:
    status: str
    id: Optional[str] = None
    location: Optional[str] = None
    property_type: Optional[str] = None
    current_analysis: Optional[str] = None


@strawberry.type
class RetrievedReport:
    status: str
    id: Optional[str] = None
    location: Optional[str] = None
    property_type: Optional[str] = None
    current_analysis: Optional[str] = None


@strawberry.type
class Query:
    @strawberry.field
    async def health_check(self) -> str:
        return "Property analysis GraphQL service is running"

    @strawberry.field
    async def analyze(self, location: str, property_type: str) -> AnalysisResponse:
        logger.info(
            f"analyze query invoked - location: {location}, property_type: {property_type}"
        )

        if MOCK_SERVICE:
            logger.info("analyze using mock service")
            return AnalysisResponse(
                status="mock_success",
                analysis=f"Mock analysis for {property_type} in {location}",
            )

        report = await find_report_by_location(location)
        if report:
            logger.info(f"analyze found report in database - location: {location}")
            return AnalysisResponse(
                status="success",
                analysis=report.current_analysis,
                source="database",
            )

        if not REASONING_ENGINE_ID:
            logger.warning("analyze - REASONING_ENGINE_ID not set")
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

            logger.info(f"analyze success - location: {location}")
            return AnalysisResponse(status="success", analysis=full_response)
        except Exception as e:
            logger.error(
                f"analyze error - exception: {type(e).__name__}, message: {str(e)}",
                exc_info=True,
            )
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
        logger.info(f"compare_property query invoked - property_ids: {property_ids}")

        if MOCK_SERVICE:
            logger.info("compare_property using mock service")
            return CompareResponse(
                status="mock_success",
                comparison=f"Mock comparison for properties: {', '.join(property_ids)}",
            )

        if not REASONING_ENGINE_ID:
            logger.warning("compare_property - REASONING_ENGINE_ID not set")
            return CompareResponse(
                status="error",
                comparison="REASONING_ENGINE_ID environment variable is not set",
            )

        try:
            reports = await find_reports_by_ids(property_ids)
            if not reports:
                logger.warning(
                    f"compare_property - no properties found for ids: {property_ids}"
                )
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
                "flood_bushfire_risk": profile.flood_bushfire_risk,
            }

            re = ReasoningEngineClient()
            full_response = ""
            async for event in re.profile_analysis(
                properties=properties_data,
                profile=profile_dict,
                user_id=str(uuid.uuid4()),
            ):
                full_response += str(event)

            logger.info(f"compare_property success - property_ids: {property_ids}")
            return CompareResponse(status="success", comparison=full_response)
        except Exception as e:
            logger.error(
                f"compare_property error - exception: {type(e).__name__}, message: {str(e)}",
                exc_info=True,
            )
            return CompareResponse(status="error", comparison=str(e))

    @strawberry.field
    async def get_report(self, report_id: str) -> RetrievedReport:
        if MOCK_SERVICE:
            return RetrievedReport(
                status="mock_success",
                id=report_id,
                location="Mock Location",
                property_type="Mock Property",
                current_analysis="Mock Analysis",
            )

        report = await find_report_by_id(report_id)
        if report:
            location_str = f"{report.location.suburb}, {report.location.state}, {report.location.country}"
            return RetrievedReport(
                status="success",
                id=report.id,
                location=location_str,
                property_type=report.property_type,
                current_analysis=report.current_analysis,
            )
        return RetrievedReport(
            status="error",
            id=report_id,
            location=None,
            property_type=None,
            current_analysis=None,
        )


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def save_report(self, report: ReportInput) -> SavedReport:
        logger.info(f"save_report mutation invoked")
        logger.debug(
            f"save_report input - location: {report.location.suburb}, {report.location.state}, {report.location.country}, property_type: {report.property_type}, current_analysis: {report.current_analysis}"
        )

        MOCK_SERVICE = False
        if MOCK_SERVICE:
            logger.info("save_report using mock service")
            return SavedReport(
                status="mock_success",
                id=str(uuid.uuid4()),
                location=f"{report.location.suburb}, {report.location.state}, {report.location.country}",
                property_type=report.property_type,
                current_analysis=report.current_analysis,
            )

        try:
            location = Location(
                suburb=report.location.suburb,
                state=report.location.state,
                country=report.location.country,
            )

            report_create = ReportCreate(
                location=location,
                property_type=report.property_type,
                current_analysis=report.current_analysis,
            )
            saved = await create_report(report_create)
            location_str = f"{saved.location.suburb}, {saved.location.state}, {saved.location.country}"
            logger.info(f"save_report success - report_id: {saved.id}")
            return SavedReport(
                status="success",
                id=saved.id,
                location=location_str,
                property_type=saved.property_type,
                current_analysis=saved.current_analysis,
            )
        except Exception as e:
            logger.error(
                f"save_report error - exception: {type(e).__name__}, message: {str(e)}",
                exc_info=True,
            )
            return SavedReport(
                status="error",
                id=None,
                location=None,
                property_type=None,
                current_analysis=None,
            )


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def analyze_stream(self, location: str, property_type: str) -> StreamResponse:
        logger.info(
            f"analyze_stream subscription invoked - location: {location}, property_type: {property_type}"
        )

        if MOCK_SERVICE:
            logger.info("analyze_stream using mock service")
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
            logger.info(
                f"analyze_stream found report in database - location: {location}"
            )
            analysis = report.current_analysis
            for i in range(0, len(analysis), 100):
                chunk = analysis[i : i + 100]
                yield StreamResponse(status="success", analysis=chunk)
                await asyncio.sleep(0.1)
            return

        if not REASONING_ENGINE_ID:
            logger.warning("analyze_stream - REASONING_ENGINE_ID not set")
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
            logger.error(
                f"analyze_stream error - exception: {type(e).__name__}, message: {str(e)}",
                exc_info=True,
            )
            yield StreamResponse(status="error", analysis=str(e))


schema = strawberry.Schema(query=Query, mutation=Mutation, subscription=Subscription)
app = GraphQL(schema)
