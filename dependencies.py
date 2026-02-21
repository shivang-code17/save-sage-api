import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config import get_settings

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Validates the Supabase JWT by calling the GoTrue /user endpoint.
    This guarantees the token is cryptographically valid and not revoked.
    """
    settings = get_settings()
    token = credentials.credentials

    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"{settings.supabase_url}/auth/v1/user",
            headers={
                "apikey": settings.supabase_anon_key,
                "Authorization": f"Bearer {token}",
            }
        )

    if res.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_data = res.json()
    user_id = user_data.get("id")
    
    return {
        "id": user_id, 
        "email": user_data.get("email"), 
        "payload": {
            "sub": user_id, 
            "email": user_data.get("email"), 
            "access_token": token
        }
    }


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
) -> dict | None:
    """
    Like get_current_user but doesn't raise if no token is provided.
    Useful for endpoints that work for both guests and logged-in users.
    """
    if not credentials:
        return None
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
