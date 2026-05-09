import logging
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
import os
from fastapi_microservice.agentic_platform.reasoningEngine import ReasoningEngine
import uuid

logging.basicConfig(level=logging.INFO)
load_dotenv()

PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION")
REASONING_ENGINE_ID = os.getenv("REASONING_ENGINE_ID")
MOCK_SERVICE = os.getenv("MOCK_SERVICE", "false").lower() == "true"

app = FastAPI(title="Property Location Strategy API (FastAPI)")

@app.get("/analyze")
async def analyze_location(location: str, property_type: str):
    MOCK_SERVICE = "true"
    if MOCK_SERVICE:
        return {
            "status": "mock_success",
            "analysis": f"Mock analysis for {property_type} properties in {location}",
        }

    re = ReasoningEngine()
    response = await re.sendQuery(
        message=f"Analyze {property_type} properties in {location}", user_id=str(uuid.uuid4())
    )

    return {"status": "success", "analysis": response}

# @app.get("/analyze/stream")
# async def analyze_location_stream(
#     location: str = "San Francisco", property_type: str = "residential"
# ):
#     async def generate():
#         MOCK_SERVICE = "true"
#         if MOCK_SERVICE:
#             yield f"Mock response for {property_type} properties in {location}\n"
#             return

#         re = ReasoningEngine()
#         return await re.sendQuery(
#             message=f"Analyze {property_type} properties in {location}", user_id=str(uuid.uuid4())
#         )
#     return StreamingResponse(generate(), media_type="text/plain")

@app.get("/report")
async def generate_report(format: str = "html"):
    if MOCK_SERVICE:
        if format == "pdf":
            return {
                "status": "mock_success",
                "format": "pdf",
                "content": "Dummy PDF report content",
            }
        return {
            "status": "mock_success",
            "format": "html",
            "content": f"<html><body>Mock Report for Property Strategy</body></html>",
        }
    return {
        "status": "success",
        "format": format,
        "content": f"Generated {format} report via Vertex AI",
    }
