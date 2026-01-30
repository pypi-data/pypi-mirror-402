from __future__ import annotations

import pytest

from tests._helpers import convert_cli, convert_core, read_fixture


@pytest.mark.parametrize(
    ("format", "input_file", "expected_file"),
    [
        ("asciidoc", "example_input.adoc", "expected_asciidoc.adoc"),
        ("markdown", "example_input.md", "expected_markdown.md"),
        ("latex", "example_input.tex", "expected_latex.tex"),
    ],
)
def test_golden_example_matches_fixtures_core_and_cli(
    format: str,
    input_file: str,
    expected_file: str,
) -> None:
    src = read_fixture(input_file)
    expected = read_fixture(expected_file)

    assert convert_core(format, src) == expected
    assert convert_cli(format, src) == expected


def test_markdown_shorten_notes_at_is_end_to_end() -> None:
    src = "{+-~TOC-CHANGES~-+}\n\nX {++0123456789 ABC++}."
    expected = (
        '- [addition-1](#addition-1): Added "0123456789…"\n\n'
        'X <a id="addition-1"></a><!-- Added "0123456789…" -->\n'
        "<ins>0123456789 ABC</ins>."
    )
    assert convert_core("markdown", src, shorten_notes_at=11) == expected


def test_markdown_placeholder_replaced_multiple_times_end_to_end() -> None:
    src = "{+-~TOC-CHANGES~-+}\n\nX {++a++}\n\n{+-~TOC-CHANGES~-+}\n"
    expected = (
        '- [addition-1](#addition-1): Added "a"\n\n'
        'X <a id="addition-1"></a><!-- Added "a" -->\n'
        "<ins>a</ins>\n\n"
        '- [addition-1](#addition-1): Added "a"\n'
    )
    assert convert_core("markdown", src) == expected
