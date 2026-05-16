from strawberry.asgi import GraphQL
import strawberry
from dotenv import load_dotenv
import os
import google.cloud.aiplatform as aiplatform
import asyncio
from typing import Optional, List, Callable
from graphql_microservice.agentic.client import ReasoningEngineClient
from graphql_microservice.database import (
    find_report_by_location,
    find_reports_by_ids,
    find_report_by_id,
    find_reports_by_user_id,
    create_report,
    Location,
    ReportCreate,
    get_user_profile,
    save_user_profile,
    saveUserReport,
)
from graphql_microservice.profile import UserProfileInput, UserProfileData
from graphql_microservice.auth import verify_google_id_token, create_jwt_token
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
class LocationInput:
    suburb: str
    state: str
    country: str


@strawberry.input
class ReportInput:
    location: LocationInput
    property_type: str
    current_analysis: str
    user_id: Optional[str] = None


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
class ReportListResponse:
    status: str
    user_id: str
    reports: List[RetrievedReport] = strawberry.field(default_factory=list)


@strawberry.type
class UserProfileResponse:
    status: str
    user_id: str
    user_profile_criteria: List[UserProfileData] = strawberry.field(
        default_factory=list
    )


@strawberry.type
class UserReportResponse:
    status: str
    user_id: str
    report_id: Optional[str] = None


@strawberry.type
class AuthResponse:
    status: str
    token: Optional[str] = None
    user: Optional["UserData"] = None


@strawberry.type
class UserData:
    id: str
    email: str
    name: Optional[str] = None
    picture: Optional[str] = None


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
        MOCK_SERVICE = False
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

    @strawberry.field
    async def get_reports_by_user_id(
        self, user_id: str, limit: int = 50
    ) -> ReportListResponse:
        logger.info(
            f"get_reports_by_user_id query invoked - user_id: {user_id}, limit: {limit}"
        )

        user_id_result, reports = await find_reports_by_user_id(user_id, limit)

        if not reports:
            return ReportListResponse(
                status="success", user_id=user_id_result, reports=[]
            )

        retrieved_reports = []
        for report in reports:
            location_str = f"{report.location.suburb}, {report.location.state}, {report.location.country}"
            retrieved_reports.append(
                RetrievedReport(
                    status="success",
                    id=report.id,
                    location=location_str,
                    property_type=report.property_type,
                    current_analysis=report.current_analysis,
                )
            )

        logger.info(
            f"get_reports_by_user_id success - user_id: {user_id}, count: {len(retrieved_reports)}"
        )
        return ReportListResponse(
            status="success", user_id=user_id_result, reports=retrieved_reports
        )

    @strawberry.field
    async def get_user_profile(self, user_id: str) -> UserProfileResponse:
        logger.info(f"get_user_profile query invoked - user_id: {user_id}")

        result = await get_user_profile(user_id)

        if not result:
            return UserProfileResponse(
                status="success", user_id=user_id, user_profile_criteria=[]
            )

        profile = result.get("userProfileCriteria")
        if profile:
            user_profile_data = [UserProfileData(**profile)]
        else:
            user_profile_data = []
        return UserProfileResponse(
            status="success",
            user_id=result["userId"],
            user_profile_criteria=user_profile_data,
        )


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def google_sign_in(self, id_token: str) -> AuthResponse:
        logger.info("google_sign_in mutation invoked")

        google_user = await verify_google_id_token(id_token)
        if not google_user:
            return AuthResponse(
                status="error",
                token=None,
                user=None,
            )

        token = create_jwt_token(google_user.google_id, google_user.email)

        return AuthResponse(
            status="success",
            token=token,
            user=UserData(
                id=google_user.google_id,
                email=google_user.email,
                name=google_user.name,
                picture=google_user.picture,
            ),
        )

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
                user_id=report.user_id,
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

    @strawberry.mutation
    async def save_user_profile(
        self, user_id: str, profile: UserProfileInput
    ) -> UserProfileResponse:
        logger.info(f"save_user_profile mutation invoked - user_id: {user_id}")

        profile_data = {
            "property_price": profile.property_price,
            "property_price_increase": profile.property_price_increase,
            "proximity_amenities": profile.proximity_amenities,
            "proximity_schools": profile.proximity_schools,
            "proximity_train_station": profile.proximity_train_station,
            "natural_hazard_risk": profile.natural_hazard_risk,
        }

        result = await save_user_profile(user_id, profile_data)

        user_profile_data = UserProfileData(
            property_price=profile.property_price,
            property_price_increase=profile.property_price_increase,
            proximity_amenities=profile.proximity_amenities,
            proximity_schools=profile.proximity_schools,
            proximity_train_station=profile.proximity_train_station,
            natural_hazard_risk=profile.natural_hazard_risk,
        )

        return UserProfileResponse(
            status="success",
            user_id=result["userId"],
            user_profile_criteria=[user_profile_data],
        )

    @strawberry.mutation
    async def saveUserReport(self, user_id: str, report_id: str) -> UserReportResponse:
        logger.info(
            f"saveUserReport mutation invoked - user_id: {user_id}, report_id: {report_id}"
        )

        result = await saveUserReport(user_id, report_id)

        if result is None:
            return UserReportResponse(
                status="error",
                user_id=user_id,
                report_id=None,
            )

        return UserReportResponse(
            status="success",
            user_id=result.userId,
            report_id=result.reportId,
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
