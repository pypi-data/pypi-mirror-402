from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Annotated

import typer

from .core import CriticMarkupProcessor
from .presets import DEFAULT_PLACEHOLDER, PRESETS, FormatName

app = typer.Typer(add_completion=False, no_args_is_help=True)


def _load_toml(path: Path) -> dict:
    import tomllib

    data = tomllib.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise typer.BadParameter("Config root must be a TOML table.")
    return data


def _read_text(path: Path | None) -> str:
    if path is None or str(path) == "-":
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8")


def _write_text(path: Path | None, text: str) -> None:
    if path is None or str(path) == "-":
        sys.stdout.write(text)
        return
    Path(path).write_text(text, encoding="utf-8")


@app.command()
def presets() -> None:
    """List available output presets."""
    typer.echo("\n".join(sorted(PRESETS.keys())))


@app.command()
def convert(
    inputs: Annotated[list[Path], typer.Argument(help="Input file(s). Use '-' for stdin.")] = (),
    format: Annotated[
        FormatName | None,
        typer.Option(
            "--format",
            "-f",
            help="Preset (usually inferred from file extension).",
        ),
    ] = None,
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Output file (single input) or directory (multi-input).",
        ),
    ] = None,
    in_place: Annotated[
        bool,
        typer.Option("--in-place", help="Overwrite input file(s) in-place."),
    ] = False,
    suffix: Annotated[
        str | None,
        typer.Option("--suffix", help="Output suffix when writing to a directory."),
    ] = None,
    config: Annotated[
        Path | None,
        typer.Option("--config", help="TOML config file with template overrides."),
    ] = None,
    changes_placeholder: Annotated[
        str,
        typer.Option(
            "--changes-placeholder",
            help="Placeholder to replace with generated change list.",
        ),
    ] = DEFAULT_PLACEHOLDER,
    include_change_refs: Annotated[
        bool,
        typer.Option(
            "--include-change-refs/--no-change-refs",
            help="Insert change markers near changes.",
        ),
    ] = True,
    append_changes_if_missing: Annotated[
        bool,
        typer.Option(
            "--append-changes-if-missing",
            help="Append a change list if placeholder is missing.",
        ),
    ] = False,
    shorten_notes_at: Annotated[
        int | None,
        typer.Option("--shorten-notes-at", help="Shorten notes to this width; set 0 to disable."),
    ] = 80,
    addition_note_template: Annotated[str | None, typer.Option("--addition-note-template")] = None,
    addition_replacement_template: Annotated[
        str | None, typer.Option("--addition-replacement-template")
    ] = None,
    deletion_note_template: Annotated[str | None, typer.Option("--deletion-note-template")] = None,
    deletion_replacement_template: Annotated[
        str | None, typer.Option("--deletion-replacement-template")
    ] = None,
    substitution_note_template: Annotated[
        str | None, typer.Option("--substitution-note-template")
    ] = None,
    substitution_replacement_template: Annotated[
        str | None, typer.Option("--substitution-replacement-template")
    ] = None,
    highlight_replacement_template: Annotated[
        str | None, typer.Option("--highlight-replacement-template")
    ] = None,
    comment_replacement_template: Annotated[
        str | None, typer.Option("--comment-replacement-template")
    ] = None,
    change_ref_template: Annotated[str | None, typer.Option("--change-ref-template")] = None,
    change_list_item_template: Annotated[
        str | None, typer.Option("--change-list-item-template")
    ] = None,
    emit_changes_json: Annotated[
        bool,
        typer.Option("--emit-changes-json", help="Print change metadata as JSON to stderr."),
    ] = False,
) -> None:
    """Convert CriticMarkup to a target format."""
    if in_place and output is not None:
        raise typer.BadParameter("--in-place and --output are mutually exclusive.")

    if shorten_notes_at == 0:
        shorten_notes_at = None

    overrides: dict[str, str] = {}
    direct_overrides = {
        "addition_note_template": addition_note_template,
        "addition_replacement_template": addition_replacement_template,
        "deletion_note_template": deletion_note_template,
        "deletion_replacement_template": deletion_replacement_template,
        "substitution_note_template": substitution_note_template,
        "substitution_replacement_template": substitution_replacement_template,
        "highlight_replacement_template": highlight_replacement_template,
        "comment_replacement_template": comment_replacement_template,
        "change_ref_template": change_ref_template,
        "change_list_item_template": change_list_item_template,
    }
    overrides.update({k: v for k, v in direct_overrides.items() if v is not None})

    if config is not None:
        cfg = _load_toml(config)
        templates = cfg.get("templates", {})
        if not isinstance(templates, dict):
            raise typer.BadParameter("[templates] must be a TOML table.")
        for key, value in templates.items():
            if isinstance(value, str):
                overrides[key] = value

    if not inputs:
        inputs = [Path("-")]

    def infer_format(path: Path) -> FormatName | None:
        ext = path.suffix.lower()
        return {
            ".adoc": "asciidoc",
            ".asciidoc": "asciidoc",
            ".md": "markdown",
            ".markdown": "markdown",
            ".tex": "latex",
        }.get(ext)

    multi = len(inputs) > 1
    if multi and output is not None and output.exists() and output.is_file():
        raise typer.BadParameter("--output must be a directory when converting multiple inputs.")

    processors: dict[FormatName, CriticMarkupProcessor] = {}

    for inp in inputs:
        inferred = None if str(inp) == "-" else infer_format(inp)
        if format is None:
            if inferred is None:
                raise typer.BadParameter(
                    "Unable to infer --format; pass --format for stdin or unknown extensions."
                )
            current_format: FormatName = inferred
        else:
            current_format = format
            if inferred is not None and inferred != current_format:
                raise typer.BadParameter(
                    f"Input '{inp.name}' looks like {inferred} but --format is {current_format}."
                )

        if current_format not in processors:
            processors[current_format] = CriticMarkupProcessor.from_preset(
                current_format,
                changes_placeholder=changes_placeholder,
                shorten_notes_at=shorten_notes_at,
                include_change_refs=include_change_refs,
                append_changes_if_missing=append_changes_if_missing,
                template_overrides=overrides,
            )
        processor = processors[current_format]

        fmt_suffix = suffix
        if fmt_suffix is None:
            fmt_suffix = {"asciidoc": ".adoc", "markdown": ".md", "latex": ".tex"}[current_format]

        text = _read_text(inp)
        result = processor.process_text(text)

        if emit_changes_json:
            payload = [{"id": c.change_id, "kind": c.kind, "note": c.note} for c in result.changes]
            sys.stderr.write(json.dumps(payload, ensure_ascii=False) + "\n")

        if in_place and str(inp) != "-":
            _write_text(inp, result.text)
            continue

        if output is None:
            _write_text(None, result.text)
            continue

        if output.is_dir() or (multi and not output.exists()):
            output.mkdir(parents=True, exist_ok=True)
            out_path = output / (inp.stem + fmt_suffix)
            _write_text(out_path, result.text)
        else:
            _write_text(output, result.text)


def main() -> None:  # pragma: no cover
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
