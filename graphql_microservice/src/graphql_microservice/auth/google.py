import os
import httpx
from typing import Optional
from graphql_microservice.database.models import GoogleUser
import logging

logger = logging.getLogger(__name__)

GOOGLE_TOKEN_INFO_URL = "https://oauth2.googleapis.com/tokeninfo"
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")


async def verify_google_id_token(id_token: str) -> Optional[GoogleUser]:
    if not GOOGLE_CLIENT_ID:
        logger.error("GOOGLE_CLIENT_ID not configured")
        return None

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                GOOGLE_TOKEN_INFO_URL,
                params={"id_token": id_token},
                timeout=10.0,
            )

        if response.status_code != 200:
            logger.warning(f"Google token validation failed: {response.status_code}")
            return None

        data = response.json()

        aud = data.get("aud")
        if aud != GOOGLE_CLIENT_ID:
            logger.warning(
                f"Token audience mismatch: expected {GOOGLE_CLIENT_ID}, got {aud}"
            )
            return None

        return GoogleUser(
            google_id=data.get("sub", ""),
            email=data.get("email", ""),
            name=data.get("name"),
            picture=data.get("picture"),
        )

    except httpx.RequestError as e:
        logger.error(f"Failed to verify Google token: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error verifying Google token: {e}")
        return None
