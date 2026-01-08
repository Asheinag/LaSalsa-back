from typing import Any

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth

security = HTTPBearer()


async def verify_firebase_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict[str, Any]:  # noqa: B008
    token = credentials.credentials
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except auth.ExpiredIdTokenError as e:
        raise HTTPException(
            status_code=401, detail="Firebase ID token has expired"
        ) from e
    except auth.InvalidIdTokenError as e:
        raise HTTPException(status_code=401, detail="Invalid Firebase ID token") from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error verifying Firebase ID token: {str(e)}"
        ) from e
