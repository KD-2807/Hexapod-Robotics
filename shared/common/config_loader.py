"""Đọc toàn bộ file JSON trong thư mục config/."""
import json
import os
from typing import Any, Dict, Optional

DEFAULT_CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "config")


class ConfigLoader:
    """Đọc <name>.json trong thư mục cấu hình; nội dung được cache."""

    def __init__(self, config_dir: Optional[str] = None):
        self._dir = config_dir or DEFAULT_CONFIG_DIR
        self._cache: Dict[str, Dict[str, Any]] = {}

    @property
    def directory(self) -> str:
        return self._dir

    def load(self, name: str) -> Dict[str, Any]:
        if name not in self._cache:
            path = os.path.join(self._dir, name + ".json")
            with open(path, "r", encoding="utf-8") as handle:
                self._cache[name] = json.load(handle)
        return self._cache[name]

    def save(self, name: str, data: Dict[str, Any]) -> None:
        path = os.path.join(self._dir, name + ".json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        self._cache[name] = data
