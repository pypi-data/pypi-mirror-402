from __future__ import annotations
import tempfile
from typing import List, Optional
import pandas as pd
from .path_types import FilePath, DirectoryPath
from .extractor import HyperExtractor
from .hyper_reader import HyperFile
from .writers import DataFrameCollection, CsvWriter, ExcelWriter


class Tdsx:
    @staticmethod
    def to_dataframe(path: str) -> List[pd.DataFrame]:
        if path == "": return 
        tdsx_file: FilePath = FilePath(path)
        tdsx_file.raise_if_not_exists()
        collection: DataFrameCollection = DataFrameCollection()
        temp_dir = tempfile.TemporaryDirectory(prefix="tdsx_")
        extractor: HyperExtractor = HyperExtractor(tdsx_file.as_string(), temp_dir.name)
        hyper_paths: List[str] = extractor.extract()
        Tdsx._collect_all_tables(collection, hyper_paths)
        temp_dir.cleanup()
        return collection.all()

    @staticmethod
    def _collect_all_tables(collection: DataFrameCollection, hyper_paths: List[str]) -> None:
        for hyper_path in hyper_paths:
            Tdsx._collect_tables_from_hyper(collection, hyper_path)

    @staticmethod
    def _collect_tables_from_hyper(collection: DataFrameCollection, hyper_path: str) -> None:
        if hyper_path == "": return 
        hyper: HyperFile = HyperFile(hyper_path)
        for table in hyper.tables().all():
            collection.add(hyper.read_table(table))

    @staticmethod
    def to_csv(path: str, out_dir: Optional[str] = None, index: bool = False) -> List[FilePath]:
        if path == "": return 
        tdsx_file: FilePath = FilePath(path)
        tdsx_file.raise_if_not_exists()
        output_dir: DirectoryPath = DirectoryPath(out_dir) if out_dir else tdsx_file.parent_directory()
        output_dir.create()
        dataframes: List[pd.DataFrame] = Tdsx.to_dataframe(path)
        writer: CsvWriter = CsvWriter(output_dir, tdsx_file.stem())
        return [writer.write(df) for df in dataframes]

    @staticmethod
    def to_excel(path: str, out_path: Optional[str] = None, engine: Optional[str] = None, order: list[str] = []) -> FilePath:
        if path == "": return 
        tdsx_file: FilePath = FilePath(path)
        tdsx_file.raise_if_not_exists()
        output: FilePath = FilePath(out_path) if out_path else FilePath(f"{tdsx_file.as_string().replace('.tdsx', '')}__tables.xlsx")
        output.parent_directory().create()
        dataframes: List[pd.DataFrame] = Tdsx.to_dataframe(path)
        if len(order) > 0:
            for df in dataframes:
                df = df.loc[:, order]

        writer: ExcelWriter = ExcelWriter(output)
        return writer.write(dataframes)

    @staticmethod
    def to_parquet(path: str, out_dir: Optional[str] = None, index: bool = False) -> List[FilePath]:
        if path == "": return 
        tdsx_file: FilePath = FilePath(path)
        tdsx_file.raise_if_not_exists()
        output_dir: DirectoryPath = DirectoryPath(out_dir) if out_dir else tdsx_file.parent_directory()
        output_dir.create()
        dataframes: List[pd.DataFrame] = Tdsx.to_dataframe(path)
        from .writers import ParquetWriter
        writer: ParquetWriter = ParquetWriter(output_dir, tdsx_file.stem())
        return [writer.write(df) for df in dataframes]
