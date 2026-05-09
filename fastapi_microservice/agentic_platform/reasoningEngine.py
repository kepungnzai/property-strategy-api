import vertexai
import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class REasoningEngine:
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

    async def sendQuery(self, message: str, user_id: str):
        try:
            logger.info(f"Using REASONING_ENGINE_ID: {self.REASONING_ENGINE_ID}")
            client = await self.get_client()
            remote_agent_engine = client.agent_engines.get(
                name=self.REASONING_ENGINE_ID
            )

            async for event in remote_agent_engine.async_stream_query(
                message=message, user_id=user_id
            ):
                yield event

        except Exception as e:
            logger.error(f"Error occurred: {e}")
