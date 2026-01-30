from __future__ import annotations

import textwrap
from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import Any

from .presets import DEFAULT_PLACEHOLDER, PRESETS, FormatName, Templates


@dataclass(frozen=True)
class Change:
    change_id: str
    note: str
    kind: str


@dataclass(frozen=True)
class ProcessorConfig:
    format: FormatName
    templates: Templates
    changes_placeholder: str = DEFAULT_PLACEHOLDER
    shorten_notes_at: int | None = 80
    include_change_refs: bool = True
    append_changes_if_missing: bool = False


CRITIC_RE = (
    r"\{\+\+(?P<addition>.*?)\+\+\}"
    r"|\{--(?P<deletion>.*?)--\}"
    r"|\{~~(?P<sub_prev>.*?)~>(?P<sub_curr>.*?)~~\}"
    r"|\{==(?P<highlight>.*?)==\}"
    r"|\{>>(?P<comment>.*?)<<\}"
)


@dataclass
class ProcessResult:
    text: str
    changes: list[Change]


def _single_line(value: str) -> str:
    return " ".join(value.split())


def _shorten(value: str, width: int | None) -> str:
    if width is None:
        return value
    return textwrap.shorten(value, width=width, placeholder="…")


def _render_template(template: str, ctx: Mapping[str, str]) -> str:
    # Avoid str.format() because many target formats use braces heavily.
    out = template
    for key, value in ctx.items():
        out = out.replace("{" + key + "}", value)
    return out


class CriticMarkupProcessor:
    def __init__(self, config: ProcessorConfig) -> None:
        self.config = config

    @classmethod
    def from_preset(
        cls,
        format: FormatName,
        *,
        changes_placeholder: str = DEFAULT_PLACEHOLDER,
        shorten_notes_at: int | None = 80,
        include_change_refs: bool = True,
        append_changes_if_missing: bool = False,
        template_overrides: Mapping[str, str] | None = None,
    ) -> CriticMarkupProcessor:
        templates = PRESETS[format]
        if template_overrides:
            templates = replace(
                templates,
                **{k: v for k, v in template_overrides.items() if hasattr(templates, k)},
            )
        config = ProcessorConfig(
            format=format,
            templates=templates,
            changes_placeholder=changes_placeholder,
            shorten_notes_at=shorten_notes_at,
            include_change_refs=include_change_refs,
            append_changes_if_missing=append_changes_if_missing,
        )
        return cls(config)

    def process_text(self, text: str) -> ProcessResult:
        import re

        templates = self.config.templates
        changes: list[Change] = []
        counters: dict[str, int] = {"addition": 0, "deletion": 0, "substitution": 0}

        def make_ctx(*, change_id: str = "", note: str = "", **extra: Any) -> dict[str, str]:
            ctx: dict[str, str] = {
                "CHANGE_ID": change_id,
                "NOTE": note,
            }
            for key, value in extra.items():
                raw = str(value)
                ctx[key] = raw
                ctx[key + "_SINGLELINE"] = _single_line(raw)
                ctx[key + "_SHORT"] = _shorten(_single_line(raw), self.config.shorten_notes_at)
            return ctx

        def track_change(kind: str, note_template: str, ctx: dict[str, str]) -> tuple[str, str]:
            counters[kind] += 1
            change_id = f"{kind}-{counters[kind]}"
            note = _render_template(note_template, ctx)
            changes.append(Change(change_id=change_id, note=note, kind=kind))
            return change_id, note

        critic_re = re.compile(CRITIC_RE, re.DOTALL)

        def repl(match: re.Match[str]) -> str:
            if (addition := match.group("addition")) is not None:
                base_ctx = make_ctx(CURRENT=addition)
                change_id, note = track_change(
                    "addition",
                    templates.addition_note_template,
                    base_ctx,
                )
                ctx = {**base_ctx, "CHANGE_ID": change_id, "NOTE": note}
                ref = (
                    _render_template(templates.change_ref_template, ctx)
                    if self.config.include_change_refs
                    else ""
                )
                body = _render_template(templates.addition_replacement_template, ctx)
                return ref + body

            if (deletion := match.group("deletion")) is not None:
                base_ctx = make_ctx(PREVIOUS=deletion)
                change_id, note = track_change(
                    "deletion",
                    templates.deletion_note_template,
                    base_ctx,
                )
                ctx = {**base_ctx, "CHANGE_ID": change_id, "NOTE": note}
                ref = (
                    _render_template(templates.change_ref_template, ctx)
                    if self.config.include_change_refs
                    else ""
                )
                body = _render_template(templates.deletion_replacement_template, ctx)
                return ref + body

            if (sub_prev := match.group("sub_prev")) is not None:
                sub_curr = match.group("sub_curr") or ""
                base_ctx = make_ctx(PREVIOUS=sub_prev, CURRENT=sub_curr)
                change_id, note = track_change(
                    "substitution",
                    templates.substitution_note_template,
                    base_ctx,
                )
                ctx = {**base_ctx, "CHANGE_ID": change_id, "NOTE": note}
                ref = (
                    _render_template(templates.change_ref_template, ctx)
                    if self.config.include_change_refs
                    else ""
                )
                body = _render_template(templates.substitution_replacement_template, ctx)
                return ref + body

            if (highlight := match.group("highlight")) is not None:
                ctx = make_ctx(HIGHLIGHT=highlight)
                return _render_template(templates.highlight_replacement_template, ctx)

            if (comment := match.group("comment")) is not None:
                ctx = make_ctx(COMMENT=comment)
                return _render_template(templates.comment_replacement_template, ctx)

            return match.group(0)

        processed = critic_re.sub(repl, text)

        changes_list = "\n".join(
            _render_template(
                templates.change_list_item_template,
                {"CHANGE_ID": c.change_id, "NOTE": c.note},
            )
            for c in changes
        )

        if self.config.changes_placeholder in processed:
            processed = processed.replace(self.config.changes_placeholder, changes_list)
        elif self.config.append_changes_if_missing and changes_list:
            if self.config.format == "latex":
                processed = (
                    processed
                    + "\n\n"
                    + templates.changes_heading_template
                    + changes_list
                    + "\n\\end{itemize}\n"
                )
            else:
                processed = (
                    processed + "\n\n" + templates.changes_heading_template + changes_list + "\n"
                )

        return ProcessResult(text=processed, changes=changes)
