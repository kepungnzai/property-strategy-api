import re
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from .connection import get_database
from .models import Report, ReportCreate, Location, UserReport


def parse_location_string(location_str: str) -> Location:
    parts = [p.strip() for p in location_str.split(",")]
    if len(parts) >= 3:
        return Location(suburb=parts[0], state=parts[1], country=parts[2])
    elif len(parts) == 2:
        return Location(suburb=parts[0], state=parts[1], country="")
    else:
        return Location(suburb=parts[0], state="", country="")


def build_location_query(location_str: str) -> dict:
    parsed = parse_location_string(location_str)
    query = {}

    suburb_pattern = re.compile(parsed.suburb, re.IGNORECASE)

    if parsed.state and parsed.country:
        query = {
            "$or": [
                {
                    "location.suburb": {"$regex": suburb_pattern},
                    "location.state": {
                        "$regex": re.compile(parsed.state, re.IGNORECASE)
                    },
                    "location.country": {
                        "$regex": re.compile(parsed.country, re.IGNORECASE)
                    },
                },
                {
                    "location.suburb": {"$regex": suburb_pattern},
                },
            ]
        }
    elif parsed.state:
        query = {
            "$or": [
                {
                    "location.suburb": {"$regex": suburb_pattern},
                    "location.state": {
                        "$regex": re.compile(parsed.state, re.IGNORECASE)
                    },
                },
                {
                    "location.suburb": {"$regex": suburb_pattern},
                },
            ]
        }
    else:
        query = {"location.suburb": {"$regex": suburb_pattern}}

    return query


async def find_report_by_location(location_str: str) -> Optional[Report]:
    db = await get_database()
    query = build_location_query(location_str)

    document = await db.reports.find_one(query)
    if document:
        document["id"] = str(document.pop("_id"))
        return Report(**document)
    return None


async def find_reports_by_ids(report_ids: List[str]) -> List[Report]:
    db = await get_database()
    object_ids = [ObjectId(id_) for id_ in report_ids if ObjectId.is_valid(id_)]

    documents = await db.reports.find({"_id": {"$in": object_ids}}).to_list(length=None)

    reports = []
    for doc in documents:
        doc["id"] = str(doc.pop("_id"))
        reports.append(Report(**doc))

    return reports


async def create_report(report: ReportCreate) -> Report:
    db = await get_database()
    document = report.model_dump()
    result = await db.reports.insert_one(document)
    document["id"] = str(result.inserted_id)
    return Report(**document)


async def get_all_reports(limit: int = 100) -> List[Report]:
    db = await get_database()
    documents = await db.reports.find().to_list(length=limit)

    reports = []
    for doc in documents:
        doc["id"] = str(doc.pop("_id"))
        reports.append(Report(**doc))

    return reports


async def find_report_by_id(report_id: str) -> Optional[Report]:
    if not ObjectId.is_valid(report_id):
        return None
    db = await get_database()
    document = await db.reports.find_one({"_id": ObjectId(report_id)})
    if document:
        document["id"] = str(document.pop("_id"))
        return Report(**document)
    return None


async def find_reports_by_user_id(
    user_id: str, limit: int = 50
) -> tuple[str, List[Report]]:
    db = await get_database()

    user_report_docs = (
        await db.userReport.find({"userId": user_id})
        .sort("creationTime", -1)
        .to_list(length=limit)
    )

    if not user_report_docs:
        return (user_id, [])

    report_ids = [doc["reportId"] for doc in user_report_docs]
    object_ids = [ObjectId(rid) for rid in report_ids if ObjectId.is_valid(rid)]

    report_docs = await db.reports.find({"_id": {"$in": object_ids}}).to_list(
        length=None
    )

    reports = []
    for doc in report_docs:
        doc["id"] = str(doc.pop("_id"))
        reports.append(Report(**doc))

    return (user_id, reports)


async def get_user_profile(user_id: str) -> Optional[dict]:
    db = await get_database()
    document = await db.userProfile.find_one({"userId": user_id})
    if document:
        document.pop("_id", None)
        return document
    return None


async def save_user_profile(user_id: str, profile_data: dict) -> dict:
    db = await get_database()
    existing = await db.userProfile.find_one({"userId": user_id})

    if existing:
        criteria = existing.get("userProfileCriteria", [])
        criteria.append(profile_data)
        await db.userProfile.update_one(
            {"userId": user_id}, {"$set": {"userProfileCriteria": criteria}}
        )
    else:
        await db.userProfile.insert_one(
            {"userId": user_id, "userProfileCriteria": [profile_data]}
        )

    return {"userId": user_id, "userProfileCriteria": [profile_data]}


async def saveUserReport(user_id: str, report_id: str) -> Optional[UserReport]:
    db = await get_database()
    if not ObjectId.is_valid(report_id):
        return None
    report_exists = await db.reports.find_one({"_id": ObjectId(report_id)})
    if not report_exists:
        return None
    user_report = UserReport(
        userId=user_id, reportId=report_id, creationTime=datetime.utcnow()
    )
    await db.userReport.insert_one(user_report.model_dump())
    return user_report
