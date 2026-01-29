from __future__ import annotations
from pathlib import Path
from typing import Union


class FilePath:
    def __init__(self, value: Union[str, Path]) -> None:
        self._value: Path = Path(value)

    def exists(self) -> bool:
        return self._value.exists()

    def raise_if_not_exists(self) -> None:
        assert self.exists(), FileNotFoundError(self._value)

    def as_string(self) -> str:
        return str(self._value)

    def parent_directory(self) -> DirectoryPath:
        return DirectoryPath(self._value.parent)

    def stem(self) -> FileName:
        return FileName(self._value.stem)
    
    def encode(self, encoding: str = 'utf-8') -> bytes:
        return self.as_string().encode(encoding)


class DirectoryPath:
    def __init__(self, value: Union[str, Path]) -> None:
        self._value: Path = Path(value)

    def create(self) -> None:
        self._value.mkdir(parents=True, exist_ok=True)

    def join(self, file_name: FileName) -> FilePath:
        return FilePath(self._value / file_name.as_string())


class FileName:
    def __init__(self, value: str) -> None:
        self._value: str = str(value)

    def as_string(self) -> str:
        return self._value

    def sanitized(self) -> FileName:
        safe: str = self._value.replace("::", "__").replace("/", "-")
        forbidden: str = "<>:\\|?*\"\n\r\t"
        cleaned: str = "".join(ch for ch in safe if ch not in forbidden)[:200]
        return FileName(cleaned)


class SheetName:
    def __init__(self, value: str) -> None:
        self._value: str = str(value)

    def as_string(self) -> str:
        forbidden: str = ":\\/?*[]\""
        clean: str = "".join(ch for ch in self._value if ch not in forbidden)
        clean = self._handle_reserved(clean)
        return clean[:31] or "sheet"

    def _handle_reserved(self, name: str) -> str:
        return f"_{name}" if name.strip().lower() in {"history"} else name
