import json
import asyncio
from typing import Dict, Any, Optional
from app.config import settings
from app.models.schemas import AIModel, AnalyzeResponse
import logging

logger = logging.getLogger("ai_service")

try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

class AIService:
    def __init__(self):
        self.gemini_key = settings.GEMINI_API_KEY
        if genai:
            genai.configure(api_key=self.gemini_key)
        # Log masked key for diagnostics (do not log full secret)
        def _mask_key(k: str):
            if not k:
                return "<none>"
            if len(k) <= 8:
                return "****"
            return f"{k[:4]}...{k[-4:]}"
        logger.info(f"Gemini key set: {_mask_key(self.gemini_key)}")

    async def analyze_code(self, prompt: str, model: AIModel, api_key: Optional[str] = None) -> AnalyzeResponse:
        if model == "auto":
            model = self._select_best_model(prompt)

        if model in ["gemini-pro-latest", "gemini-flash-latest"]:
            key = api_key or self.gemini_key
            return await self._call_gemini(prompt, model, key)
        elif model in ["gpt-4", "gpt-4o", "gpt-4o-mini"]:
            key = api_key or settings.OPENAI_API_KEY
            if not key:
                raise ValueError("OpenAI API key not configured")
            return await self._call_openai(prompt, model, key)
        else:
            raise ValueError(f"Unsupported model: {model}")

    def _select_best_model(self, prompt: str) -> AIModel:
        # Simple heuristic: use Gemini Pro for most tasks, Flash for faster responses
        if len(prompt) > 2000:
            return "gemini-pro-latest"  # Better for longer contexts
        return "gemini-flash-latest"

    async def _call_gemini(self, prompt: str, model: str, api_key: str) -> AnalyzeResponse:
        if not api_key or api_key.startswith("your_") or not genai:
            # Return mock response for development
            return AnalyzeResponse(
                code="// Mock response: Please set a valid Gemini API key\n" + prompt.split("```")[1].split("```")[0] if "```" in prompt else "// Mock response",
                explanations=[{
                    "title": "Mock Response",
                    "description": "This is a mock response because no valid Gemini API key is configured. Please set GEMINI_API_KEY in your .env file."
                }]
            )

        try:
            # Run Gemini API call in a thread pool to make it async-compatible
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._sync_call_gemini, prompt, model, api_key)
            return result
        except Exception as e:
            # Handle quota exceeded or other errors by raising so router can map to HTTP status
            error_msg = str(e).lower()
            # Quota / rate limit -> caller should return 429
            if "quota" in error_msg or "rate limit" in error_msg:
                raise RuntimeError("Gemini quota exceeded: " + str(e))

            # Detected leaked/disabled API key -> caller should return 403
            if "leak" in error_msg or "leaked" in error_msg or "reported as leaked" in error_msg or "reported" in error_msg or "unauthorized" in error_msg:
                raise RuntimeError("Gemini API key invalid or reported as leaked: " + str(e))

            # Unknown error: re-raise
            raise

    def _sync_call_gemini(self, prompt: str, model: str, api_key: str) -> AnalyzeResponse:
        # Temporarily configure genai with the provided key
        original_key = getattr(genai, '_api_key', None)
        genai.configure(api_key=api_key)
        try:
            generation_config = genai.types.GenerationConfig(
                temperature=0.1,  # Low temperature for consistent code output
                max_output_tokens=2000,
            )

            model_instance = genai.GenerativeModel(
                model_name=model,
                generation_config=generation_config
            )

            response = model_instance.generate_content(prompt)
            content = response.text

            return self._parse_ai_response(content)
        finally:
            # Restore original key
            if original_key:
                genai.configure(api_key=original_key)

    async def _call_openai(self, prompt: str, model: str, api_key: str) -> AnalyzeResponse:
        if not OpenAI:
            raise ValueError("OpenAI library not installed")

        try:
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=2000
            )
            content = response.choices[0].message.content
            return self._parse_ai_response(content)
        except Exception as e:
            error_msg = str(e).lower()
            if "invalid" in error_msg or "unauthorized" in error_msg:
                raise RuntimeError("OpenAI API key invalid or leaked: " + str(e))
            if "quota" in error_msg or "rate limit" in error_msg:
                raise RuntimeError("OpenAI quota exceeded: " + str(e))
            raise

    def _parse_ai_response(self, content: str) -> AnalyzeResponse:
        # Try several strategies to extract a JSON object from the model output.
        # The model may include code fences, prose, or JSON with extra braces inside
        # code/docstrings. We'll scan for balanced `{...}` candidates and try to
        # parse each one until we succeed.
        def try_parse_json_segment(s: str) -> Optional[AnalyzeResponse]:
            try:
                data = json.loads(s)
                return AnalyzeResponse(**data)
            except Exception:
                return None

        content_str = content or ""

        # First, try parsing the entire content as JSON (best case)
        parsed = try_parse_json_segment(content_str)
        if parsed:
            return parsed

        # Next, scan for balanced {...} substrings and try parsing them.
        indices = [i for i, ch in enumerate(content_str) if ch == "{"]
        for i in indices:
            depth = 0
            for j in range(i, len(content_str)):
                if content_str[j] == "{":
                    depth += 1
                elif content_str[j] == "}":
                    depth -= 1
                    if depth == 0:
                        candidate = content_str[i : j + 1]
                        parsed = try_parse_json_segment(candidate)
                        if parsed:
                            return parsed
                        break

        # Finally, as a last resort, try to locate a JSON-looking substring
        # using simple heuristics (e.g., the first '{' to the last '}' ) and
        # attempt to parse that.
        start = content_str.find("{")
        end = content_str.rfind("}") + 1
        if start != -1 and end != -1 and end > start:
            candidate = content_str[start:end]
            parsed = try_parse_json_segment(candidate)
            if parsed:
                return parsed

        # If all parsing attempts failed, return an error-wrapping response
        logger.debug("AI response could not be parsed as JSON; returning error wrapper")
        return AnalyzeResponse(
            code="// Error parsing AI response\n" + content_str,
            explanations=[
                {
                    "title": "AI Response Error",
                    "description": "Could not parse the AI response as JSON. Please check model output or prompt formatting."
                }
            ],
        )