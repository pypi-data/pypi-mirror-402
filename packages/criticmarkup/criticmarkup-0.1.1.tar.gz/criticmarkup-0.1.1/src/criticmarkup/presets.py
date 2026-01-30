from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

FormatName = Literal["asciidoc", "markdown", "latex"]


@dataclass(frozen=True)
class Templates:
    change_ref_template: str
    change_list_item_template: str
    changes_heading_template: str

    addition_note_template: str
    addition_replacement_template: str

    deletion_note_template: str
    deletion_replacement_template: str

    substitution_note_template: str
    substitution_replacement_template: str

    highlight_replacement_template: str
    comment_replacement_template: str


PRESETS: dict[FormatName, Templates] = {
    "asciidoc": Templates(
        change_ref_template="[[{CHANGE_ID}, {NOTE}]]\n",
        change_list_item_template="- <<{CHANGE_ID}>>",
        changes_heading_template="== Changes\n\n",
        addition_note_template='Added "{CURRENT_SHORT}"',
        addition_replacement_template="[red]#*{CURRENT}*#",
        deletion_note_template='Deleted "{PREVIOUS_SHORT}"',
        deletion_replacement_template=(
            'footnote:[In previous version this said "{PREVIOUS_SINGLELINE}"]'
        ),
        substitution_note_template='Changed "{PREVIOUS_SHORT}" to "{CURRENT_SHORT}"',
        substitution_replacement_template=(
            "[red]#*{CURRENT}*#\n"
            'footnote:[In previous version this said "{PREVIOUS_SINGLELINE}"]'
        ),
        highlight_replacement_template="[yellow]#{HIGHLIGHT}#",
        comment_replacement_template='footnote:[{COMMENT_SINGLELINE}]',
    ),
    "markdown": Templates(
        change_ref_template='<a id="{CHANGE_ID}"></a><!-- {NOTE} -->\n',
        change_list_item_template="- [{CHANGE_ID}](#{CHANGE_ID}): {NOTE}",
        changes_heading_template="## Changes\n\n",
        addition_note_template='Added "{CURRENT_SHORT}"',
        addition_replacement_template="<ins>{CURRENT}</ins>",
        deletion_note_template='Deleted "{PREVIOUS_SHORT}"',
        deletion_replacement_template="<del>{PREVIOUS}</del>",
        substitution_note_template='Changed "{PREVIOUS_SHORT}" to "{CURRENT_SHORT}"',
        substitution_replacement_template="<del>{PREVIOUS}</del><ins>{CURRENT}</ins>",
        highlight_replacement_template="<mark>{HIGHLIGHT}</mark>",
        comment_replacement_template="<!-- {COMMENT_SINGLELINE} -->",
    ),
    "latex": Templates(
        change_ref_template="% {CHANGE_ID}: {NOTE}\n",
        change_list_item_template="\\item {CHANGE_ID}: {NOTE}",
        changes_heading_template="\\section*{Changes}\n\\begin{itemize}\n",
        addition_note_template='Added "{CURRENT_SHORT}"',
        addition_replacement_template="\\underline{{{CURRENT}}}",
        deletion_note_template='Deleted "{PREVIOUS_SHORT}"',
        deletion_replacement_template="\\sout{{{PREVIOUS}}}",
        substitution_note_template='Changed "{PREVIOUS_SHORT}" to "{CURRENT_SHORT}"',
        substitution_replacement_template="\\sout{{{PREVIOUS}}}\\underline{{{CURRENT}}}",
        highlight_replacement_template="\\fbox{{{HIGHLIGHT}}}",
        comment_replacement_template="% NOTE: {COMMENT_SINGLELINE}",
    ),
}


DEFAULT_PLACEHOLDER = "{+-~TOC-CHANGES~-+}"
