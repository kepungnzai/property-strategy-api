from fastapi import FastAPI
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

app = FastAPI(title="Property Location Strategy API (FastAPI)")


@app.post("/analyze")
async def analyze_location(location: str, property_type: str):
    if MOCK_SERVICE:
        return {
            "status": "mock_success",
            "analysis": f"Mock analysis for {property_type} properties in {location}",
        }
    engine = aiplatform.ReasoningEngine(REASONING_ENGINE_ID)
    response = engine.predict({"location": location, "property_type": property_type})
    return {"status": "success", "analysis": response}


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
