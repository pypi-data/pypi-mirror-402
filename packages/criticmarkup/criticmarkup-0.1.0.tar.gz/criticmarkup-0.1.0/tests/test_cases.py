from __future__ import annotations

import pytest

from tests._helpers import convert_cli, convert_core, read_case


@pytest.mark.parametrize(
    ("case_name", "format", "input_name", "expected_name", "kwargs"),
    [
        ("markdown_simple", "markdown", "input.md", "expected.md", {}),
        (
            "markdown_append_changes",
            "markdown",
            "input.md",
            "expected.md",
            {"append_changes_if_missing": True},
        ),
        ("markdown_many_ids", "markdown", "input.md", "expected.md", {}),
        ("markdown_no_tracked_changes", "markdown", "input.md", "expected.md", {}),
        ("markdown_multiline_addition", "markdown", "input.md", "expected.md", {}),
        (
            "markdown_no_change_refs",
            "markdown",
            "input.md",
            "expected.md",
            {"include_change_refs": False},
        ),
        (
            "markdown_custom_placeholder",
            "markdown",
            "input.md",
            "expected.md",
            {"changes_placeholder": "<<CHANGES>>"},
        ),
        (
            "latex_append_changes",
            "latex",
            "input.tex",
            "expected.tex",
            {"append_changes_if_missing": True},
        ),
    ],
)
def test_cases_core_end_to_end(
    case_name: str,
    format: str,
    input_name: str,
    expected_name: str,
    kwargs: dict[str, object],
) -> None:
    src = read_case(case_name, input_name)
    expected = read_case(case_name, expected_name)
    assert convert_core(format, src, **kwargs) == expected


@pytest.mark.parametrize(
    ("case_name", "format", "input_name", "expected_name", "extra_args"),
    [
        ("markdown_simple", "markdown", "input.md", "expected.md", []),
        ("markdown_many_ids", "markdown", "input.md", "expected.md", []),
        (
            "markdown_no_change_refs",
            "markdown",
            "input.md",
            "expected.md",
            ["--no-change-refs"],
        ),
        (
            "latex_append_changes",
            "latex",
            "input.tex",
            "expected.tex",
            ["--append-changes-if-missing"],
        ),
    ],
)
def test_cases_cli_end_to_end(
    case_name: str,
    format: str,
    input_name: str,
    expected_name: str,
    extra_args: list[str],
) -> None:
    src = read_case(case_name, input_name)
    expected = read_case(case_name, expected_name)
    assert convert_cli(format, src, extra_args=extra_args) == expected
