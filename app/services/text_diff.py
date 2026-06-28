from dataclasses import dataclass
from difflib import SequenceMatcher


@dataclass(frozen=True)
class DiffLine:
    kind: str
    left_no: int | None
    right_no: int | None
    left: str
    right: str


@dataclass(frozen=True)
class DiffHunk:
    index: int
    kind: str
    lines: list[DiffLine]
    left_text: str
    right_text: str
    choice: str


@dataclass(frozen=True)
class DiffResult:
    hunks: list[DiffHunk]
    merged_text: str
    added: int
    deleted: int
    modified: int
    left_lines: int
    right_lines: int
    left_chars: int
    right_chars: int
    added_chars: int
    deleted_chars: int


def compare_texts(left_text, right_text, choices=None):
    choices = choices or {}
    left_lines = left_text.splitlines(keepends=True)
    right_lines = right_text.splitlines(keepends=True)
    hunks = []
    merged = []
    added = deleted = modified = added_chars = deleted_chars = 0

    for index, (tag, left_start, left_end, right_start, right_end) in enumerate(
        SequenceMatcher(None, left_lines, right_lines).get_opcodes()
    ):
        left_block = left_lines[left_start:left_end]
        right_block = right_lines[right_start:right_end]
        kind = "modified" if tag == "replace" else tag
        lines = _diff_lines(tag, left_block, right_block, left_start, right_start)
        for line in lines:
            if line.kind in {"added", "modified"} and line.right_no is not None:
                added += 1
                added_chars += len(line.right)
            if line.kind in {"deleted", "modified"} and line.left_no is not None:
                deleted += 1
                deleted_chars += len(line.left)
            if line.kind == "modified":
                modified += 1

        choice = choices.get(index, "right" if tag != "equal" else "left")
        if choice not in {"left", "right"}:
            choice = "right"
        merged.append("".join(right_block if choice == "right" else left_block))
        hunks.append(
            DiffHunk(
                index=index,
                kind=kind,
                lines=lines,
                left_text="".join(left_block),
                right_text="".join(right_block),
                choice=choice,
            )
        )

    return DiffResult(
        hunks,
        "".join(merged),
        added,
        deleted,
        modified,
        len(left_lines),
        len(right_lines),
        _char_count(left_lines),
        _char_count(right_lines),
        added_chars,
        deleted_chars,
    )


def _char_count(lines):
    return sum(len(line.rstrip("\r\n")) for line in lines)


def _diff_lines(tag, left_block, right_block, left_start, right_start):
    if tag == "replace":
        return _replace_diff_lines(left_block, right_block, left_start, right_start)

    lines = []
    count = max(len(left_block), len(right_block))
    for offset in range(count):
        has_left = offset < len(left_block)
        has_right = offset < len(right_block)
        lines.append(
            DiffLine(
                kind="added" if tag == "insert" else "deleted" if tag == "delete" else "modified" if tag == "replace" else "equal",
                left_no=left_start + offset + 1 if has_left else None,
                right_no=right_start + offset + 1 if has_right else None,
                left=_display_line(left_block[offset]) if has_left else "",
                right=_display_line(right_block[offset]) if has_right else "",
            )
        )
    return lines


def _replace_diff_lines(left_block, right_block, left_start, right_start):
    lines = []
    left_display = [_display_line(line) for line in left_block]
    right_display = [_display_line(line) for line in right_block]
    for tag, left_from, left_to, right_from, right_to in SequenceMatcher(None, left_display, right_display).get_opcodes():
        count = max(left_to - left_from, right_to - right_from)
        for offset in range(count):
            has_left = left_from + offset < left_to
            has_right = right_from + offset < right_to
            lines.append(
                DiffLine(
                    kind="added" if tag == "insert" else "deleted" if tag == "delete" else "modified" if tag == "replace" else "equal",
                    left_no=left_start + left_from + offset + 1 if has_left else None,
                    right_no=right_start + right_from + offset + 1 if has_right else None,
                    left=left_display[left_from + offset] if has_left else "",
                    right=right_display[right_from + offset] if has_right else "",
                )
            )
    return lines


def _display_line(line):
    return line.rstrip("\r\n")
