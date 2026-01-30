from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from criticmarkup.cli import app


def test_cli_in_place_and_output_are_mutually_exclusive(tmp_path: Path) -> None:
    inp = tmp_path / "in.md"
    inp.write_text("X {++a++}", encoding="utf-8")
    out = tmp_path / "out.md"
    runner = CliRunner()
    res = runner.invoke(app, ["convert", str(inp), "--output", str(out), "--in-place"])
    assert res.exit_code != 0
    assert "mutually exclusive" in res.output


def test_cli_multiple_inputs_output_must_be_directory_when_file_exists(tmp_path: Path) -> None:
    a = tmp_path / "a.md"
    b = tmp_path / "b.md"
    a.write_text("A {++x++}", encoding="utf-8")
    b.write_text("B {++y++}", encoding="utf-8")
    out = tmp_path / "out.md"
    out.write_text("already a file", encoding="utf-8")

    runner = CliRunner()
    res = runner.invoke(app, ["convert", str(a), str(b), "--output", str(out)])
    assert res.exit_code != 0
    assert "directory" in res.output


def test_cli_infers_format_from_extension_markdown(tmp_path: Path) -> None:
    inp = tmp_path / "doc.md"
    inp.write_text("X {++a++}", encoding="utf-8")
    runner = CliRunner()
    res = runner.invoke(app, ["convert", str(inp)])
    assert res.exit_code == 0
    assert res.stdout == 'X <a id="addition-1"></a><!-- Added "a" -->\n<ins>a</ins>'


def test_cli_rejects_mismatched_format_and_extension(tmp_path: Path) -> None:
    inp = tmp_path / "doc.md"
    inp.write_text("X {++a++}", encoding="utf-8")
    runner = CliRunner()
    res = runner.invoke(app, ["convert", str(inp), "--format", "asciidoc"])
    assert res.exit_code != 0
    assert "looks like markdown" in res.output


def test_cli_stdin_requires_format_when_not_provided() -> None:
    runner = CliRunner()
    res = runner.invoke(app, ["convert", "-"], input="X {++a++}\n")
    assert res.exit_code != 0
    assert "infer --format" in res.output


def test_cli_stdin_to_stdout(tmp_path: Path) -> None:
    runner = CliRunner()
    res = runner.invoke(
        app,
        ["convert", "-", "--format", "markdown"],
        input="We {++add++}.\n",
    )
    assert res.exit_code == 0
    assert res.stdout == 'We <a id="addition-1"></a><!-- Added "add" -->\n<ins>add</ins>.\n'


def test_cli_emit_changes_json_to_stderr(tmp_path: Path) -> None:
    runner = CliRunner()
    res = runner.invoke(
        app,
        [
            "convert",
            "-",
            "--format",
            "markdown",
            "--emit-changes-json",
            "--output",
            str(tmp_path / "out.md"),
        ],
        input="X {--y--}.\n",
    )
    assert res.exit_code == 0
    payload = json.loads(res.output.strip())
    assert payload == [{"id": "deletion-1", "kind": "deletion", "note": 'Deleted "y"'}]


def test_cli_invalid_templates_config_errors(tmp_path: Path) -> None:
    cfg = tmp_path / "bad.toml"
    cfg.write_text('templates = "nope"\n', encoding="utf-8")
    runner = CliRunner()
    res = runner.invoke(app, ["convert", "-", "--config", str(cfg)], input="X {++a++}\n")
    assert res.exit_code != 0


@pytest.mark.parametrize("format", ["asciidoc", "markdown", "latex"])
def test_cli_presets_command_lists_known_presets(format: str) -> None:
    runner = CliRunner()
    res = runner.invoke(app, ["presets"])
    assert res.exit_code == 0
    assert format in res.stdout.splitlines()
