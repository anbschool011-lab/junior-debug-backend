from fastapi import APIRouter, Request, HTTPException
import requests
import logging
from app.config import settings

logger = logging.getLogger("api_keys")
logger.setLevel(logging.INFO)

def _mask_auth_header(headers: dict):
    h = dict(headers)
    auth = h.get("authorization") or h.get("Authorization")
    if auth:
        h["authorization"] = "Bearer <redacted>"
    return h


router = APIRouter()


def _mask_key(key: str) -> str:
    if not key:
        return ""
    k = key.strip()
    if len(k) <= 8:
        return "****"
    return f"{k[:4]}...{k[-4:]}"


def supabase_get_user(access_token: str):
    """Get user info from Supabase Auth using the user's access token."""
    url = f"{settings.SUPABASE_URL}/auth/v1/user"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "apikey": settings.SUPABASE_KEY,
    }
    resp = requests.get(url, headers=headers)
    logger.debug(f"supabase_get_user: status={resp.status_code}, url={url}")
    try:
        body = resp.json()
    except Exception:
        body = resp.text
    logger.debug(f"supabase_get_user response: {body}")
    if resp.status_code != 200:
        return None
    if isinstance(body, dict) and body.get("id"):
        return body
    if isinstance(body, dict) and body.get("user"):
        return body.get("user")
    return None


@router.post("/save-api-key")
async def save_api_key(request: Request):
    try:
        body = await request.json()
        logger.info("save_api_key called")
        api_key = body.get("api_key")
        if not api_key:
            raise HTTPException(status_code=400, detail="Missing api_key in body")

        auth_header = request.headers.get("authorization")
        if not auth_header:
            raise HTTPException(status_code=401, detail="Missing Authorization header")

        token = auth_header.split(" ")[-1]
        user = supabase_get_user(token)
        if not user:
            logger.info("save_api_key: invalid user token")
            raise HTTPException(status_code=401, detail="Invalid user token")

        user_id = user.get("id") or user.get("user", {}).get("id")
        if not user_id:
            raise HTTPException(status_code=500, detail="Could not determine user id")

        url = f"{settings.SUPABASE_URL}/rest/v1/user_api_keys?on_conflict=user_id"
        headers = {
            "Content-Type": "application/json",
            "apikey": settings.SUPABASE_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_KEY}",
            "Prefer": "return=representation",
        }
        payload = {"user_id": user_id, "api_key": api_key}
        resp = requests.post(url, json=payload, headers=headers)
        logger.debug(f"save_api_key supabase resp: status={resp.status_code}")
        if not resp.ok:
            logger.error("Failed to save key to Supabase: %s", resp.text)
            raise HTTPException(status_code=400, detail="Failed to save API key (server error)")

        return {"status": "ok", "api_key": _mask_key(api_key)}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get-api-key")
async def get_api_key(request: Request):
    try:
        auth_header = request.headers.get("authorization")
        logger.info("get_api_key called")
        if not auth_header:
            raise HTTPException(status_code=401, detail="Missing Authorization header")
        token = auth_header.split(" ")[-1]
        user = supabase_get_user(token)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid user token")
        user_id = user.get("id") or user.get("user", {}).get("id")
        if not user_id:
            raise HTTPException(status_code=500, detail="Could not determine user id")

        url = f"{settings.SUPABASE_URL}/rest/v1/user_api_keys?user_id=eq.{user_id}&select=api_key"
        headers = {"apikey": settings.SUPABASE_KEY, "Authorization": f"Bearer {settings.SUPABASE_KEY}"}
        resp = requests.get(url, headers=headers)
        logger.debug(f"get_api_key supabase resp: status={resp.status_code}")
        if not resp.ok:
            logger.error("Failed to read user_api_keys: %s", resp.text)
            raise HTTPException(status_code=500, detail="Failed to read stored API key")
        data = resp.json()
        if not data:
            return {"status": "no_key"}
        api_key = data[0].get("api_key")
        return {"status": "ok", "api_key": _mask_key(api_key)}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete-api-key")
async def delete_api_key(request: Request):
    try:
        auth_header = request.headers.get("authorization")
        logger.info("delete_api_key called")
        if not auth_header:
            raise HTTPException(status_code=401, detail="Missing Authorization header")
        token = auth_header.split(" ")[-1]
        user = supabase_get_user(token)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid user token")
        user_id = user.get("id") or user.get("user", {}).get("id")
        if not user_id:
            raise HTTPException(status_code=500, detail="Could not determine user id")

        url = f"{settings.SUPABASE_URL}/rest/v1/user_api_keys?user_id=eq.{user_id}"
        headers = {"apikey": settings.SUPABASE_KEY, "Authorization": f"Bearer {settings.SUPABASE_KEY}"}
        resp = requests.delete(url, headers=headers)
        logger.debug(f"delete_api_key supabase resp: status={resp.status_code}")
        if not resp.ok:
            logger.error("Failed to delete user_api_keys: %s", resp.text)
            raise HTTPException(status_code=500, detail="Failed to delete stored API key")
        return {"status": "ok"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test-api-key")
async def test_api_key(request: Request):
    try:
        auth_header = request.headers.get("authorization")
        logger.info("test_api_key called")
        if not auth_header:
            raise HTTPException(status_code=401, detail="Missing Authorization header")
        token = auth_header.split(" ")[-1]
        user = supabase_get_user(token)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid user token")
        user_id = user.get("id") or user.get("user", {}).get("id")
        if not user_id:
            raise HTTPException(status_code=500, detail="Could not determine user id")

        url = f"{settings.SUPABASE_URL}/rest/v1/user_api_keys?user_id=eq.{user_id}&select=api_key"
        headers = {"apikey": settings.SUPABASE_KEY, "Authorization": f"Bearer {settings.SUPABASE_KEY}"}
        resp = requests.get(url, headers=headers)
        logger.debug(f"test_api_key supabase resp: status={resp.status_code}")
        if not resp.ok:
            logger.error("Failed to read user_api_keys: %s", resp.text)
            return {"status": "error", "detail": "Failed to read stored API key"}
        data = resp.json()
        if not data:
            return {"status": "no_key"}
        api_key = data[0].get("api_key")

        if api_key.startswith("sk-"):
            r = requests.get("https://api.openai.com/v1/models", headers={"Authorization": f"Bearer {api_key}"})
            if not r.ok:
                return {"status": "error", "detail": r.text}
            return {"status": "ok", "provider": "OpenAI"}

        if api_key.startswith("ya29.") or api_key.startswith("AIza") or api_key.startswith("gcp-"):
            return {"status": "ok", "provider": "Gemini"}

        return {"status": "unknown_provider", "provider": None}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
