from pathlib import Path

def load_prompt(*path_parts: str) -> str:
    root = Path(__file__).resolve().parents[2] / "prompts"
    return (root.joinpath(*path_parts)).read_text(encoding="utf-8")
