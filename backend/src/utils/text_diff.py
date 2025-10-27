"""Utilities for text comparison and diff visualization."""

import difflib
from typing import Dict, List, Tuple


def get_text_diff(original: str, modified: str) -> List[Tuple[str, str]]:
    """Generate line-by-line diff between two texts.

    Args:
        original: Original text
        modified: Modified text

    Returns:
        List of (status, line) tuples where status is '+', '-', or ' '
    """
    original_lines = original.splitlines(keepends=True)
    modified_lines = modified.splitlines(keepends=True)

    diff = list(
        difflib.unified_diff(
            original_lines,
            modified_lines,
            lineterm="",
            n=1000,  # Large context to show all lines
        )
    )

    result: List[Tuple[str, str]] = []
    for line in diff[2:]:  # Skip header lines
        if line.startswith("+"):
            result.append(("+", line[1:]))
        elif line.startswith("-"):
            result.append(("-", line[1:]))
        elif not line.startswith("@@"):
            result.append((" ", line[1:] if line.startswith(" ") else line))

    return result


def get_change_summary(original: str, modified: str) -> Dict[str, int | float]:
    """Get summary statistics about changes.

    Args:
        original: Original text
        modified: Modified text

    Returns:
        Dictionary with change statistics
    """
    diff = get_text_diff(original, modified)

    additions = sum(1 for status, _ in diff if status == "+")
    deletions = sum(1 for status, _ in diff if status == "-")
    unchanged = sum(1 for status, _ in diff if status == " ")

    return {
        "additions": additions,
        "deletions": deletions,
        "unchanged": unchanged,
        "total_changes": additions + deletions,
        "change_percentage": round(
            (additions + deletions) / max(len(original.splitlines()), 1) * 100, 1
        ),
    }


def highlight_keywords(text: str, keywords: List[str]) -> str:
    """Highlight keywords in text for display.

    Args:
        text: Text to process
        keywords: List of keywords to highlight

    Returns:
        Text with keywords wrapped in markdown bold
    """
    result = text
    for keyword in keywords:
        # Case-insensitive replacement
        import re

        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        result = pattern.sub(f"**{keyword}**", result)

    return result


def extract_optimized_resume(agent_output: str) -> str:
    """Extract the optimized resume from Agent 2's output.

    Args:
        agent_output: Full output from Agent 2 including report and resume

    Returns:
        Just the optimized resume text, or full output if extraction fails
    """
    import re

    # Try to find the "PART 8: COMPLETE OPTIMIZED RESUME" section
    patterns = [
        r"## PART 8: COMPLETE OPTIMIZED RESUME.*?```\s*(.+?)\s*```\s*\*\*END OF OPTIMIZED RESUME\*\*",
        r"## COMPLETE OPTIMIZED RESUME.*?```\s*(.+?)\s*```",
        r"# COMPLETE OPTIMIZED RESUME.*?```\s*(.+?)\s*```",
        r"OPTIMIZED RESUME:.*?```\s*(.+?)\s*```",
    ]

    for pattern in patterns:
        match = re.search(pattern, agent_output, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()

    # If no clear section found, return the full output
    # (fallback for when the model doesn't follow the exact format)
    return agent_output
