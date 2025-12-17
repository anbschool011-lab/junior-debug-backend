import sys
from pathlib import Path

# Ensure backend package importable when running script directly
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.prompt_builder import PromptBuilder
from app.services.ai_service import AIService

# Define the tasks and languages used by the frontend TaskSelector/LanguageSelector
TASKS = [
    "debug-refactor",
    "debug",
    "refactor",
    "performance",
    "comments",
]

LANGUAGES = [
    "javascript",
    "python",
    "typescript",
    "java",
    "go",
]

sample_code = """function calculateSum(arr) {
  let sum = 0
  for (i = 0; i < arr.length; i++) {
    sum = sum + arr[i]
  }
  return sum
}
"""

ai = AIService()

print("Running anonymous (mock) analysis tests for task/language combinations:\n")

for task in TASKS:
    for lang in LANGUAGES:
        prompt = PromptBuilder.build_prompt(code=sample_code, task=task, language=lang)
        # Pass api_key=None so AIService returns mock response for Gemini/OpenAI
        try:
            result = __import__("asyncio").get_event_loop().run_until_complete(
                ai.analyze_code(prompt, "auto", api_key=None)
            )
            print(f"TASK={task}, LANG={lang} -> OK (code length {len(result.code)})")
        except Exception as e:
            print(f"TASK={task}, LANG={lang} -> ERROR: {e}")

print("\nTest run complete.")
