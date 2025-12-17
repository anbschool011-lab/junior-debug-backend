from fastapi import APIRouter, HTTPException, Request
from app.models.schemas import AnalyzeRequest, AnalyzeResponse
from app.services.prompt_builder import PromptBuilder
from app.services.ai_service import AIService
import requests
from app.config import settings

router = APIRouter()
ai_service = AIService()

def get_user_api_key(request: Request) -> str | None:
    """Get user's API key if authenticated, else None."""
    auth_header = request.headers.get("authorization")
    if not auth_header:
        return None
    token = auth_header.split(" ")[-1]
    # Call Supabase to get user
    url = f"{settings.SUPABASE_URL}/auth/v1/user"
    headers = {
        "Authorization": f"Bearer {token}",
        "apikey": settings.SUPABASE_KEY,
    }
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        return None
    user = resp.json()
    user_id = user.get("id")
    if not user_id:
        return None
    # Get user's API key from DB
    url = f"{settings.SUPABASE_URL}/rest/v1/user_api_keys?user_id=eq.{user_id}"
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
    }
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        return None
    data = resp.json()
    if data:
        return data[0].get("api_key")
    return None

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_code(request: Request, req: AnalyzeRequest) -> AnalyzeResponse:
    try:
        # Determine task id: prefer explicit `task` (id); if not provided,
        # attempt to map a human-readable `task_description` to a TaskType.
        task_id = None
        if req.task:
            task_id = req.task
        elif req.task_description:
            task_id = PromptBuilder.map_description_to_task(req.task_description)

        if not task_id:
            raise ValueError("Invalid or missing task. Provide a task id or task_description.")

        # Build the AI prompt
        prompt = PromptBuilder.build_prompt(
            code=req.code,
            task=task_id,
            language=req.language,
        )

        # Get user's API key if authenticated
        user_key = get_user_api_key(request)

        if user_key is None:
            # Anonymous user: try to use backend-configured AI key (Gemini preferred)
            backend_key = settings.GEMINI_API_KEY or getattr(settings, "OPENAI_API_KEY", None)
            if backend_key:
                # Use backend key to perform real analysis
                response = await ai_service.analyze_code(prompt, req.model, backend_key)
                return response

            # No backend key configured — return demonstration analysis
            return AnalyzeResponse(
                code="// Mock analysis for anonymous user\n" + req.code,
                explanations=[{
                    "title": "Mock Analysis",
                    "description": "This is a demonstration analysis. Sign up to get real AI-powered code analysis with your own API key."
                }]
            )

        # Authenticated user: call AI service with the user's key
        response = await ai_service.analyze_code(prompt, req.model, user_key)

        return response

    except ValueError as e:
        print(f"ValueError: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        msg = str(e).lower()
        # Quota/rate limit
        if "quota" in msg or "rate limit" in msg:
            raise HTTPException(status_code=429, detail="AI provider quota exceeded: please try again later or rotate your key")
        # Invalid/leaked key
        if "leak" in msg or "leaked" in msg or "reported" in msg or "invalid" in msg or "unauthorized" in msg:
            raise HTTPException(status_code=403, detail="AI provider key invalid or reported as leaked. Please rotate the key.")
        # Fallback
        raise HTTPException(status_code=502, detail=f"AI provider error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")