import pytest

from app.services.prompt_builder import PromptBuilder


@pytest.mark.parametrize(
    "input_desc,expected",
    [
        ("Find and fix errors", "debug"),
        (" find and fix errors ", "debug"),
        ("Improve Structure", "refactor"),
        ("Full cleanup", "debug-refactor"),
        ("Optimize Speed", "performance"),
        ("Add Comments", "comments"),
        ("document code", "comments"),
        ("debug", "debug"),
        ("refactor", "refactor"),
    ],
)
def test_map_description_to_task_matches(input_desc, expected):
    result = PromptBuilder.map_description_to_task(input_desc)
    assert result == expected


def test_map_description_to_task_unknown_returns_none():
    assert PromptBuilder.map_description_to_task("") is None
    assert PromptBuilder.map_description_to_task("unknown task") is None
