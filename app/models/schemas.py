from pydantic import BaseModel
from typing import List, Literal

TaskType = Literal["debug", "refactor", "debug-refactor", "performance", "comments"]
AIModel = Literal["gemini-pro-latest", "gemini-flash-latest", "auto"]
Language = Literal["javascript", "typescript", "python", "php", "html", "css", "java", "csharp", "go", "rust"]

class AnalyzeRequest(BaseModel):
    code: str
    # `task` may be provided as the task id (e.g. "debug") or the frontend may
    # send a human-friendly description via `task_description`. At least one
    # must be provided.
    task: TaskType | None = None
    task_description: str | None = None
    model: AIModel
    language: Language

class Explanation(BaseModel):
    title: str
    description: str

class AnalyzeResponse(BaseModel):
    code: str
    explanations: List[Explanation]