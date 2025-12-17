from app.models.schemas import TaskType, Language

class PromptBuilder:
    @staticmethod
    def build_prompt(code: str, task: TaskType, language: Language) -> str:
        base_prompt = f"""Act as a senior software engineer with extensive experience in {language} development.

You are helping a junior developer debug and improve their code. Your task is to {PromptBuilder._get_task_description(task)}.

IMPORTANT CONSTRAINTS:
- Keep original function names unless they are clearly wrong
- Do not exceed 50 lines of code in your response
- Provide clear, educational explanations
- Focus on best practices for {language}

CODE TO ANALYZE:
``` {language}
{code}
```

{PromptBuilder._get_task_specific_instructions(task)}

Return your response in the following JSON format:
{{
  "code": "the improved code here",
  "explanations": [
    {{
      "title": "Brief title of the change",
      "description": "Detailed explanation of why this change was made"
    }}
  ]
}}

Ensure the code is properly formatted and functional."""

        return base_prompt

    @staticmethod
    def _get_task_description(task: TaskType) -> str:
        descriptions = {
            "debug": "identify and fix bugs, syntax errors, and logical issues",
            "refactor": "improve code structure, readability, and maintainability without changing functionality",
            "debug-refactor": "first fix any bugs, then improve the code structure and readability",
            "performance": "optimize the code for better performance while maintaining correctness",
            "comments": "add comprehensive comments and documentation to explain the code"
        }
        return descriptions[task]

    @staticmethod
    def _get_task_specific_instructions(task: TaskType) -> str:
        instructions = {
            "debug": "Focus on finding and fixing syntax errors, logical bugs, and runtime issues.",
            "refactor": "Improve variable names, function structure, and code organization.",
            "debug-refactor": "First ensure the code works correctly, then make it cleaner and more maintainable.",
            "performance": "Look for algorithmic improvements, reduce unnecessary operations, and optimize loops.",
            "comments": "Add JSDoc/docstring comments, inline explanations, and usage examples."
        }
        return instructions[task]
    @staticmethod
    def map_description_to_task(description: str) -> TaskType | None:
        """Map a human-friendly task description to a TaskType.

        Accepts trimmed, case-insensitive input and a few common synonyms.
        Returns the TaskType string (e.g. "debug") or None if unknown.
        """
        if not description:
            return None

        key = description.strip().lower()
        # direct id passthrough
        if key in ("debug", "refactor", "debug-refactor", "performance", "comments"):
            return key  # type: ignore[return-value]

        mapping = {
            "find and fix errors": "debug",
            "find and fix error": "debug",
            "find and fix bugs": "debug",
            "improve structure": "refactor",
            "improve structure and readability": "refactor",
            "full cleanup": "debug-refactor",
            "optimize speed": "performance",
            "optimize performance": "performance",
            "add comments": "comments",
            "document code": "comments",
            "document the code": "comments",
        }

        return mapping.get(key)