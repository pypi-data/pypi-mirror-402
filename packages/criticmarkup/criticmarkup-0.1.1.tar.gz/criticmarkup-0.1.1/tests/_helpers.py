from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from criticmarkup.cli import app
from criticmarkup.core import CriticMarkupProcessor


def normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n")


def read_fixture(name: str) -> str:
    fixtures = Path(__file__).parent / "fixtures"
    return normalize_newlines((fixtures / name).read_text(encoding="utf-8"))


def read_case(case_name: str, filename: str) -> str:
    cases = Path(__file__).parent / "fixtures" / "cases"
    return normalize_newlines((cases / f"{case_name}.{filename}").read_text(encoding="utf-8"))


def convert_core(format: str, src: str, **kwargs: object) -> str:
    proc = CriticMarkupProcessor.from_preset(format, **kwargs)  # type: ignore[arg-type]
    return proc.process_text(src).text


def convert_cli(format: str, src: str, extra_args: list[str] | None = None) -> str:
    runner = CliRunner()
    args = ["convert", "-", "--format", format]
    if extra_args:
        args.extend(extra_args)
    res = runner.invoke(app, args, input=src)
    assert res.exit_code == 0, res.output
    return normalize_newlines(res.stdout)
