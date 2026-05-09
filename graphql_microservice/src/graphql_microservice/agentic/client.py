import vertexai
import os
import logging
import json
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class ReasoningEngineClient:
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

    # async def predict(self, message: str, user_id: str) -> str:
    #     try:
    #         logger.info(f"Using REASONING_ENGINE_ID: {self.REASONING_ENGINE_ID}")
    #         client = await self.get_client()
    #         remote_agent_engine = client.agent_engines.get(
    #             name=self.REASONING_ENGINE_ID
    #         )
    #         return remote_agent_engine.predict(message=message, user_id=user_id)
    #     except Exception as e:
    #         logger.error(f"Error occurred: {e}")
    #         raise

    async def send_query(self, message: str, user_id: str):
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

    async def profile_analysis(self, properties: list, profile: dict, user_id: str):
        try:
            properties_json = json.dumps(properties, indent=2)
            profile_json = json.dumps(profile, indent=2)

            message = (
                f"Compare the following properties based on the user profile:\n\n"
                f"Properties:\n{properties_json}\n\n"
                f"User Profile (1-5 stars):\n{profile_json}\n\n"
                f"Please analyze and rank these properties according to the user's priorities."
            )

            client = await self.get_client()
            remote_agent_engine = client.agent_engines.get(
                name=self.REASONING_ENGINE_ID
            )

            async for event in remote_agent_engine.async_stream_query(
                message=message, user_id=user_id
            ):
                yield event

        except Exception as e:
            logger.error(f"Error in profile_analysis: {e}")
            raise
