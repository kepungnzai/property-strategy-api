import re
from typing import Optional, List
from bson import ObjectId
from .connection import get_database
from .models import Report, ReportCreate, Location


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
