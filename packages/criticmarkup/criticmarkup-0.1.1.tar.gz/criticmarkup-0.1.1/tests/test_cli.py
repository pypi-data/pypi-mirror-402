from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from criticmarkup.cli import app


def test_cli_convert_single_file_to_output(tmp_path: Path) -> None:
    inp = tmp_path / "in.md"
    inp.write_text("A {++b++}.", encoding="utf-8")
    out = tmp_path / "out.md"

    runner = CliRunner()
    res = runner.invoke(app, ["convert", str(inp), "--format", "markdown", "--output", str(out)])
    assert res.exit_code == 0
    assert out.read_text(encoding="utf-8") == (
        'A <a id="addition-1"></a><!-- Added "b" -->\n<ins>b</ins>.'
    )


def test_cli_convert_in_place(tmp_path: Path) -> None:
    inp = tmp_path / "in.md"
    inp.write_text("A {--b--}.", encoding="utf-8")
    runner = CliRunner()
    res = runner.invoke(app, ["convert", str(inp), "--format", "markdown", "--in-place"])
    assert res.exit_code == 0
    assert inp.read_text(encoding="utf-8") == (
        'A <a id="deletion-1"></a><!-- Deleted "b" -->\n<del>b</del>.'
    )


def test_cli_convert_uses_toml_template_overrides(tmp_path: Path) -> None:
    inp = tmp_path / "in.md"
    inp.write_text("A {++b++}.", encoding="utf-8")
    cfg = tmp_path / "criticmarkup.toml"
    cfg.write_text(
        "\n".join(
            [
                "[templates]",
                'addition_replacement_template = "X{CURRENT}X"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    runner = CliRunner()
    res = runner.invoke(
        app,
        [
            "convert",
            str(inp),
            "--format",
            "markdown",
            "--config",
            str(cfg),
        ],
    )
    assert res.exit_code == 0
    assert res.stdout == 'A <a id="addition-1"></a><!-- Added "b" -->\nXbX.'


def test_cli_multiple_inputs_to_directory_and_suffix(tmp_path: Path) -> None:
    a = tmp_path / "a.adoc"
    b = tmp_path / "b.adoc"
    a.write_text("A {++x++}", encoding="utf-8")
    b.write_text("B {++y++}", encoding="utf-8")
    out_dir = tmp_path / "out"

    runner = CliRunner()
    res = runner.invoke(
        app,
        [
            "convert",
            str(a),
            str(b),
            "--format",
            "asciidoc",
            "--output",
            str(out_dir),
            "--suffix",
            ".out",
        ],
    )
    assert res.exit_code == 0
    assert (out_dir / "a.out").read_text(encoding="utf-8") == (
        'A [[addition-1, Added "x"]]\n[red]#*x*#'
    )
    assert (out_dir / "b.out").read_text(encoding="utf-8") == (
        'B [[addition-1, Added "y"]]\n[red]#*y*#'
    )
