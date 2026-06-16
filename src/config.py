from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List


DEFAULT_KEYWORDS_PATH = Path("config/keywords.yaml")


def load_keywords(path: Path = DEFAULT_KEYWORDS_PATH) -> Dict[str, Dict[str, List[str]]]:
    if not path.exists():
        raise FileNotFoundError(f"Keyword config not found: {path}")

    try:
        import yaml  # type: ignore
    except ImportError:
        return _load_simple_keywords_yaml(path)

    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}

    return _validate_keywords(data)


def _load_simple_keywords_yaml(path: Path) -> Dict[str, Dict[str, List[str]]]:
    data: Dict[str, Dict[str, List[str]]] = {}
    current_section: str | None = None
    current_key: str | None = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue

        if not line.startswith(" ") and line.endswith(":"):
            current_section = line[:-1].strip()
            data[current_section] = {}
            current_key = None
            continue

        if line.startswith("  ") and not line.startswith("    ") and line.endswith(":"):
            if current_section is None:
                raise ValueError(f"Invalid YAML structure near: {raw_line}")
            current_key = line[:-1].strip()
            data[current_section][current_key] = []
            continue

        if line.startswith("    - "):
            if current_section is None or current_key is None:
                raise ValueError(f"Invalid YAML list item near: {raw_line}")
            data[current_section][current_key].append(_strip_quotes(line[6:].strip()))
            continue

        raise ValueError(f"Unsupported YAML syntax near: {raw_line}")

    return _validate_keywords(data)


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _validate_keywords(data: Any) -> Dict[str, Dict[str, List[str]]]:
    if not isinstance(data, dict):
        raise ValueError("Keyword config must be a mapping.")

    normalized: Dict[str, Dict[str, List[str]]] = {}
    for section, values in data.items():
        if not isinstance(section, str) or not isinstance(values, dict):
            raise ValueError("Keyword config sections must be mappings.")

        normalized[section] = {}
        for key, keywords in values.items():
            if not isinstance(key, str) or not isinstance(keywords, list):
                raise ValueError("Keyword groups must be lists.")
            normalized[section][key] = [str(keyword) for keyword in keywords]

    return normalized

