from __future__ import annotations
import zipfile
from pathlib import Path
from typing import List


class HyperExtractor:
    def __init__(self, tdsx_path: str, temp_directory: str) -> None:
        self._tdsx_path: str = tdsx_path
        self._temp_directory: str = temp_directory

    def extract(self) -> List[str]:
        hyper_files: List[str] = []
        archive: zipfile.ZipFile = zipfile.ZipFile(self._tdsx_path)
        hyper_files = self._extract_hyper_files(archive)
        archive.close()
        assert hyper_files, RuntimeError("Nenhum .hyper encontrado dentro do .tdsx")
        return hyper_files

    def _extract_hyper_files(self, archive: zipfile.ZipFile) -> List[str]:
        return [self._extract_file(archive, name) for name in archive.namelist() if self._is_hyper(name)]

    def _is_hyper(self, name: str) -> bool:
        return name.lower().endswith(".hyper")

    def _extract_file(self, archive: zipfile.ZipFile, name: str) -> str:
        destination: Path = Path(self._temp_directory) / Path(name).name
        source = archive.open(name)
        self._write_file(source, destination)
        source.close()
        return str(destination)

    def _write_file(self, source, destination: Path) -> None:
        output = open(destination, "wb")
        output.write(source.read())
        output.close()
