import logging
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
import os
import google.cloud.aiplatform as aiplatform
import vertexai

from fastapi_microservice.agentic_platform import ReasoningEngine

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

    client = vertexai.Client(
        location=LOCATION,
    )

    remote_agent_engine = client.agent_engines.get(name=REASONING_ENGINE_ID)
    response = remote_agent_engine.predict(
        message=f"Analyze {property_type} properties in {location}", user_id="test"
    )

    return {"status": "success", "analysis": response}


@app.get("/analyze/stream")
async def analyze_location_stream(
    location: str = "San Francisco", property_type: str = "residential"
):
    async def generate():
        MOCK_SERVICE = "true"
        if MOCK_SERVICE:
            yield f"Mock response for {property_type} properties in {location}\n"
            return

        client = vertexai.Client(
            location=LOCATION,
        )

        remote_agent_engine = client.agent_engines.get(name=REASONING_ENGINE_ID)

        async for event in remote_agent_engine.async_stream_query(
            message=f"Analyze {property_type} properties in {location}", user_id="test"
        ):
            yield f"{event}\n"

    return StreamingResponse(generate(), media_type="text/plain")


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
