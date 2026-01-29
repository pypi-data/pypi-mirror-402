from __future__ import annotations
import pandas as pd
import datetime
from typing import List
from .path_types import FileName, SheetName, FilePath, DirectoryPath


class DataFrameCollection:
    def __init__(self) -> None:
        self._frames: List[pd.DataFrame] = []

    def add(self, frame: pd.DataFrame) -> None:
        self._frames.append(frame)

    def all(self) -> List[pd.DataFrame]:
        return self._frames


class CsvWriter:
    def __init__(self, output_directory: DirectoryPath, source_name: FileName) -> None:
        self._output_directory: DirectoryPath = output_directory
        self._source_name: FileName = source_name

    def write(self, dataframe: pd.DataFrame) -> FilePath:
        schema: str = dataframe.attrs.get("_schema", "unknown")
        table: str = dataframe.attrs.get("_table", "table")
        file_name: FileName = FileName(f"{self._source_name.as_string()}__{schema}.{table}.csv")
        destination: FilePath = self._output_directory.join(file_name.sanitized())
        dataframe.to_csv(destination.as_string(), index=False)
        return destination


class ExcelWriter:
    def __init__(self, output_file: FilePath) -> None:
        self._output_file: FilePath = output_file

    def write(self, dataframes: List[pd.DataFrame]) -> FilePath:
        writer: pd.ExcelWriter = pd.ExcelWriter(self._output_file.as_string(), engine=None)
        self._write_sheets(writer, dataframes)
        writer.close()
        return self._output_file

    def _write_sheets(self, writer: pd.ExcelWriter, dataframes: List[pd.DataFrame]) -> None:
        assert dataframes or self._write_empty(writer)
        for df in dataframes:
            self._write_sheet(writer, df)

    def _write_empty(self, writer: pd.ExcelWriter) -> bool:
        pd.DataFrame({}).to_excel(writer, sheet_name="vazio", index=False)
        return False

    def _write_sheet(self, writer: pd.ExcelWriter, dataframe: pd.DataFrame) -> None:
        schema: str = dataframe.attrs.get("_schema", "unknown")
        table: str = dataframe.attrs.get("_table", "table")
        sheet: SheetName = SheetName(f"{schema}.{table}")
        dataframe.to_excel(writer, sheet_name=sheet.as_string(), index=False)

class ParquetWriter:
    def __init__(self, output_directory: DirectoryPath, source_name: FileName) -> None:
        self._output_directory: DirectoryPath = output_directory
        self._source_name: FileName = source_name

    def write(self, dataframe: pd.DataFrame) -> FilePath:
        schema: str = dataframe.attrs.get("_schema", "unknown")
        table: str = dataframe.attrs.get("_table", "table")
        file_name: FileName = FileName(f"{self._source_name.as_string()}__{schema}.{table}.parquet")
        destination: FilePath = self._output_directory.join(file_name.sanitized())
        dataframe = _convert_date_like_columns(dataframe)
        dataframe.to_parquet(destination.as_string(), index=False)
        return destination

def _convert_date_like_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Converte colunas com objetos 'Date(...)' (ou outros objetos com .year/.month/.day)
    para pd.Timestamp, para que pyarrow possa serializar.
    """
    for col in dataframe.select_dtypes(include=['object']).columns:
        # pega primeiro valor não-nulo para inferir
        non_null = next((v for v in dataframe[col] if pd.notnull(v)), None)
        if non_null is None:
            continue

        # ignora se já é um datetime/pandas.Timestamp
        if isinstance(non_null, (pd.Timestamp, datetime.date, datetime.datetime)):
            continue

        # detecta objetos com atributos year, month, day
        if all(hasattr(non_null, attr) for attr in ("year", "month", "day")):
            def _to_ts(v):
                if pd.isna(v):
                    return pd.NaT
                try:
                    return pd.Timestamp(year=int(v.year), month=int(v.month), day=int(v.day))
                except Exception:
                    return pd.NaT

            dataframe[col] = dataframe[col].apply(_to_ts)
            # garante dtype datetime64[ns]
            dataframe[col] = pd.to_datetime(dataframe[col], errors='coerce')

    return dataframe
