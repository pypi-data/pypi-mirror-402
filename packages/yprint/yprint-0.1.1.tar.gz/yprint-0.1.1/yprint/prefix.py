import hashlib
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .terminal import default_prefix_width

ARROW = " \u2192 "
ELLIPSIS = "\u2026"
TRUNCATE_MARK = "-"

PASTEL_COLORS = [
    110, 111, 112, 113, 114, 115, 116, 117,
    118, 119, 120, 121, 150, 151, 152, 153,
    180, 181, 182, 183, 189, 195, 216, 223,
]


@dataclass
class Segment:
    text: str
    color: Optional[int]


def _env(primary: str, legacy: str) -> Optional[str]:
    value = os.environ.get(primary)
    if value:
        return value
    return os.environ.get(legacy)


def _parse_prefix_width():
    env = _env("YPRINT_PREFIX_WIDTH", "PWATCH_PREFIX_WIDTH")
    if not env:
        return default_prefix_width()
    try:
        value = int(env)
    except ValueError:
        return default_prefix_width()
    return value if value > 0 else default_prefix_width()


def _parse_only_paths():
    raw = _env("YPRINT_ONLY", "PWATCH_ONLY") or ""
    if not raw:
        return []
    paths = []
    for entry in raw.split(os.pathsep):
        if not entry:
            continue
        paths.append(os.path.realpath(os.path.abspath(entry)))
    return paths


PREFIX_WIDTH = _parse_prefix_width()
ONLY_PATHS = _parse_only_paths()

_path_cache: Dict[str, str] = {}
_allowed_cache: Dict[str, bool] = {}
_color_cache: Dict[str, int] = {}


def _normalize_path(path: str) -> str:
    cached = _path_cache.get(path)
    if cached is not None:
        return cached
    resolved = os.path.realpath(path)
    _path_cache[path] = resolved
    return resolved


def _is_allowed(path: Optional[str]) -> bool:
    if not ONLY_PATHS:
        return True
    if not path or path.startswith("<"):
        return False
    cached = _allowed_cache.get(path)
    if cached is not None:
        return cached
    real_path = _normalize_path(path)
    for base in ONLY_PATHS:
        if real_path == base or real_path.startswith(base + os.sep):
            _allowed_cache[path] = True
            return True
    _allowed_cache[path] = False
    return False


def _color_for_path(path: Optional[str]) -> int:
    key = path or "<unknown>"
    cached = _color_cache.get(key)
    if cached is not None:
        return cached
    digest = hashlib.blake2b(key.encode("utf-8", "surrogateescape"), digest_size=2).digest()
    idx = int.from_bytes(digest, "big") % len(PASTEL_COLORS)
    color = PASTEL_COLORS[idx]
    _color_cache[key] = color
    return color


def _collapse_frames(frames: List[Tuple[str, Optional[str]]]) -> List[Tuple[str, Optional[str]]]:
    collapsed: List[Tuple[str, Optional[str]]] = []
    hidden_run = False
    for func, path in frames:
        visible = _is_allowed(path)
        if visible:
            if hidden_run:
                collapsed.append((ELLIPSIS, None))
                hidden_run = False
            collapsed.append((func, path))
        else:
            hidden_run = True
    if hidden_run:
        collapsed.append((ELLIPSIS, None))
    return collapsed


def _render_segments(items: List[Tuple[str, Optional[str]]]) -> List[Segment]:
    segments: List[Segment] = []
    prev_kind = None
    for text, path in items:
        is_ellipsis = text == ELLIPSIS and path is None
        if is_ellipsis:
            if prev_kind is not None:
                segments.append(Segment(" ", None))
            segments.append(Segment(ELLIPSIS, None))
            prev_kind = "ellipsis"
            continue
        if prev_kind == "func":
            segments.append(Segment(ARROW, None))
        elif prev_kind == "ellipsis":
            segments.append(Segment(" ", None))
        segments.append(Segment(text, _color_for_path(path)))
        prev_kind = "func"
    return segments


def _apply_color(segment: Segment) -> str:
    if segment.color is None:
        return segment.text
    return f"\x1b[38;5;{segment.color}m{segment.text}\x1b[0m"


def _truncate_and_pad(segments: List[Segment], width: int) -> Tuple[str, str]:
    width = max(1, width)
    total = sum(len(segment.text) for segment in segments)

    if total <= width:
        plain = "".join(segment.text for segment in segments)
        colored = "".join(_apply_color(segment) for segment in segments)
    else:
        keep = max(width - 1, 0)
        drop = total - keep
        trimmed: list[Segment] = []
        for segment in segments:
            if drop <= 0:
                trimmed.append(segment)
                continue
            seg_len = len(segment.text)
            if drop >= seg_len:
                drop -= seg_len
                continue
            trimmed.append(Segment(segment.text[drop:], segment.color))
            drop = 0
        plain = TRUNCATE_MARK + "".join(segment.text for segment in trimmed)
        colored = TRUNCATE_MARK + "".join(_apply_color(segment) for segment in trimmed)

    if len(plain) < width:
        padding = " " * (width - len(plain))
        plain += padding
        colored += padding
    return plain, colored


def format_prefix(frames: List[Tuple[str, Optional[str]]]) -> Tuple[str, str]:
    if not frames:
        spaces = " " * PREFIX_WIDTH
        return spaces, spaces
    collapsed = _collapse_frames(frames)
    segments = _render_segments(collapsed)
    return _truncate_and_pad(segments, PREFIX_WIDTH)
