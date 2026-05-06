import asyncio
import vertexai
import os 
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION")
REASONING_ENGINE_ID = os.getenv("REASONING_ENGINE_ID")
MOCK_SERVICE = os.getenv("MOCK_SERVICE", "false").lower() == "true"


LOCATION = "us-central1"
client = vertexai.Client(
    location=LOCATION,
)

async def sendQuery():

    try:
        print(f"Using REASONING_ENGINE_ID: {REASONING_ENGINE_ID}")
        remote_agent_engine = client.agent_engines.get(name=REASONING_ENGINE_ID)

        async for event in remote_agent_engine.async_stream_query(
        message="hi!", user_id="test"
    ):
            print(event)
    
    except Exception as e:
        print(f"Error occurred: {e}")