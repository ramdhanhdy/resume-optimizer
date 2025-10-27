from __future__ import annotations

import json
import re
from typing import Any, Dict, Iterable, List, Sequence, Tuple


SENTINEL_START = "BEGIN_VALIDATION_SCORES_JSON"
SENTINEL_END = "END_VALIDATION_SCORES_JSON"

_RE_FENCED_JSON = re.compile(
    r"BEGIN_VALIDATION_SCORES_JSON[\s\S]*?```json\s*(\{[\s\S]*?\})\s*```[\s\S]*?END_VALIDATION_SCORES_JSON",
    re.IGNORECASE,
)

_REQUIRED_KEYS = [
    "requirements_match",
    "ats_optimization",
    "cultural_fit",
    "presentation_quality",
    "competitive_positioning",
]

_RED_FLAG_SECTION_KEYWORDS: Sequence[str] = (
    "red flag",
    "fabrication risk",
    "risks & mitigations",
    "risk register",
    "risk assessment",
)

_RECOMMENDATION_SECTION_KEYWORDS: Sequence[str] = (
    "recommendation",
    "quick win",
    "next step",
    "action plan",
    "polish opportunity",
)

_BULLET_PATTERN = re.compile(r"^\s*(?:[-*•]+|\d+[\.\)])\s*(.+)$")
_FABRICATION_PATTERN = re.compile(r"\bFABRICATION RISK[:\-]\s*(.+)", re.IGNORECASE)


def _coerce_score(value: Any) -> int:
    if isinstance(value, bool):  # explicitly disallow booleans
        raise ValueError("Boolean is not a valid score")
    if isinstance(value, (int, float)):
        n = int(round(value))
    elif isinstance(value, str):
        # Extract first integer-like token
        m = re.search(r"-?\d+", value)
        if not m:
            raise ValueError(f"Unable to parse score from string: {value!r}")
        n = int(m.group(0))
    else:
        raise ValueError(f"Unsupported score type: {type(value)}")
    # Clamp to [0, 100]
    return max(0, min(100, n))


def parse_validation_scores_from_text(text: str) -> Dict[str, int]:
    """Parse structured scores JSON emitted by the Validator agent.

    Expects a fenced JSON block wrapped by BEGIN_/END_ sentinels, e.g.:

    BEGIN_VALIDATION_SCORES_JSON
    ```json
    { "scores": { ... } }
    ```
    END_VALIDATION_SCORES_JSON
    """
    m = _RE_FENCED_JSON.search(text)
    if not m:
        raise ValueError(
            "Validation scores block not found. Ensure the agent outputs the JSON block with sentinels."
        )

    raw_json = m.group(1)
    data = json.loads(raw_json)

    if (
        not isinstance(data, dict)
        or "scores" not in data
        or not isinstance(data["scores"], dict)
    ):
        raise ValueError(
            "Invalid schema: expected top-level object with 'scores' field"
        )

    scores_in = data["scores"]

    out: Dict[str, int] = {}
    for key in _REQUIRED_KEYS:
        if key not in scores_in:
            raise ValueError(f"Missing required score: {key}")
        out[key] = _coerce_score(scores_in[key])

    # Optional overall_score; compute if absent
    if "overall_score" in scores_in:
        out["overall_score"] = _coerce_score(scores_in["overall_score"])
    else:
        out["overall_score"] = int(
            round(sum(out[k] for k in _REQUIRED_KEYS) / len(_REQUIRED_KEYS))
        )

    return out


def _dedupe_preserve_order(items: Iterable[str]) -> List[str]:
    seen: set[str] = set()
    result: List[str] = []
    for item in items:
        normalized = re.sub(r"\s+", " ", item).strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(normalized)
    return result


def _extract_section_ranges(
    lines: List[str], keywords: Sequence[str]
) -> List[Tuple[int, int]]:
    """Return start and end indices (exclusive) for sections whose heading matches keywords."""
    heading_indices: List[int] = []

    for idx, line in enumerate(lines):
        normalized = re.sub(r"[^a-z0-9\s]+", " ", line.lower()).strip()
        if not normalized:
            continue
        if any(keyword in normalized for keyword in keywords):
            heading_indices.append(idx)

    if not heading_indices:
        return []

    ranges: List[Tuple[int, int]] = []
    for start_idx in heading_indices:
        end_idx = len(lines)
        for idx in range(start_idx + 1, len(lines)):
            candidate = lines[idx].strip()
            if candidate.startswith("#"):
                end_idx = idx
                break
        ranges.append((start_idx, end_idx))
    return ranges


def _extract_items_from_lines(lines: Sequence[str]) -> List[str]:
    items: List[str] = []
    buffer: List[str] = []

    def flush_buffer() -> None:
        if buffer:
            items.append(" ".join(buffer).strip())
            buffer.clear()

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            flush_buffer()
            continue

        if line.startswith("#"):
            flush_buffer()
            continue

        bullet_match = _BULLET_PATTERN.match(line)
        if bullet_match:
            flush_buffer()
            content = bullet_match.group(1).strip()
            if content:
                items.append(content)
            continue

        fabrication_match = _FABRICATION_PATTERN.search(line)
        if fabrication_match:
            flush_buffer()
            items.append(line)
            continue

        buffer.append(line)

    flush_buffer()
    return items


def _extract_section_items(text: str, keywords: Sequence[str]) -> List[str]:
    lines = text.splitlines()
    ranges = _extract_section_ranges(lines, keywords)
    items: List[str] = []
    for start_idx, end_idx in ranges:
        section_lines = lines[start_idx + 1 : end_idx]
        items.extend(_extract_items_from_lines(section_lines))
    return _dedupe_preserve_order(items)


def _extract_red_flags(text: str) -> List[str]:
    items = _extract_section_items(text, _RED_FLAG_SECTION_KEYWORDS)
    if items:
        return items

    inline_items = [
        match.group(0).strip() for match in _FABRICATION_PATTERN.finditer(text)
    ]
    return _dedupe_preserve_order(inline_items)


def _extract_recommendations(text: str) -> List[str]:
    items = _extract_section_items(text, _RECOMMENDATION_SECTION_KEYWORDS)
    if items:
        return items

    fallback_matches = re.findall(
        r"([^.]*\b(recommend|quick win|next step|action)\b[^.]*)",
        text,
        re.IGNORECASE,
    )
    extracted = [match[0].strip() for match in fallback_matches]
    return _dedupe_preserve_order(extracted)


def extract_validation_artifacts(
    text: str,
) -> Tuple[Dict[str, float], List[str], List[str]]:
    """Parse validator output into scores, red flags, and recommendations."""
    raw_scores = parse_validation_scores_from_text(text)
    scores = {key: float(value) for key, value in raw_scores.items()}
    red_flags = _extract_red_flags(text)
    recommendations = _extract_recommendations(text)
    return scores, red_flags, recommendations
