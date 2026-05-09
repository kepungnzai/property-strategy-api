import asyncio
import vertexai
import os 
from dotenv import load_dotenv

class ReasoningEngine:
    def __init__(self):
        load_dotenv()
        self.PROJECT_ID = os.getenv("PROJECT_ID")
        self.LOCATION = os.getenv("LOCATION")
        self.REASONING_ENGINE_ID = os.getenv("REASONING_ENGINE_ID")
        self.MOCK_SERVICE = os.getenv("MOCK_SERVICE", "false").lower() == "true"
    
    async def get_client(self):
        return vertexai.Client(
            location=self.LOCATION,
        )

    async def sendQuery(self):
        try:
            print(f"Using REASONING_ENGINE_ID: {self.REASONING_ENGINE_ID}")
            client = await self.get_client()
            remote_agent_engine = client.agent_engines.get(name=self.REASONING_ENGINE_ID)

            async for event in remote_agent_engine.async_stream_query(
                message="hi!", user_id="test"
            ):
                print(event)
        
        except Exception as e:
            print(f"Error occurred: {e}")