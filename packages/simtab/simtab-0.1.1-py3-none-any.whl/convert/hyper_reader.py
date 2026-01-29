from __future__ import annotations
import pandas as pd
from typing import List
from tableauhyperapi import HyperProcess, Telemetry, Connection, Name, TableName
from .table_types import SchemaName, TableName as TableName_


class HyperFile:
    def __init__(self, path: str) -> None:
        self._path: str = path

    def tables(self) -> TableList:
        return TableList(self._path)

    def read_table(self, table_name: TableName_) -> pd.DataFrame:
        return TableReader(self._path, table_name).read()


class TableList:
    def __init__(self, hyper_path: str) -> None:
        self._hyper_path: str = hyper_path

    def all(self) -> List[TableName_]:
        return self._extract_non_system_tables()

    def _extract_non_system_tables(self) -> List[TableName_]:
        items: List[TableName_] = []
        process: HyperProcess = HyperProcess(Telemetry.SEND_USAGE_DATA_TO_TABLEAU)
        connection: Connection = Connection(endpoint=process.endpoint, database=self._hyper_path)
        items = self._collect_tables(connection)
        connection.close()
        process.close()
        assert items, RuntimeError(f"Nenhuma tabela visível em {self._hyper_path}")
        return sorted(items, key=lambda x: (x.schema.value, x.name))

    def _collect_tables(self, connection: Connection) -> List[TableName_]:
        items: List[TableName_] = []
        for schema in connection.catalog.get_schema_names():
            items.extend(self._tables_in_schema(connection, schema))
        return items

    def _tables_in_schema(self, connection: Connection, schema) -> List[TableName_]:
        schema_name: str = schema.name.unescaped
        return [] if self._is_system_schema(schema_name) else self._extract_tables(connection, schema, schema_name)

    def _is_system_schema(self, schema_name: str) -> bool:
        return schema_name in {"pg_catalog", "information_schema"}

    def _extract_tables(self, connection: Connection, schema, schema_name: str) -> List[TableName_]:
        return [TableName_(SchemaName(schema_name), t.name.unescaped) for t in connection.catalog.get_table_names(schema=schema)]


class TableReader:
    def __init__(self, hyper_path: str, table_name: TableName_) -> None:
        self._hyper_path: str = hyper_path
        self._table_name: TableName_ = table_name

    def read(self) -> pd.DataFrame:
        process: HyperProcess = HyperProcess(Telemetry.SEND_USAGE_DATA_TO_TABLEAU)
        connection: Connection = Connection(endpoint=process.endpoint, database=self._hyper_path)
        dataframe: pd.DataFrame = self._read_dataframe(connection)
        connection.close()
        process.close()
        return dataframe

    def _read_dataframe(self, connection: Connection) -> pd.DataFrame:
        table: TableName = TableName(Name(self._table_name.schema.value), Name(self._table_name.name))
        definition = connection.catalog.get_table_definition(table)
        columns: List[str] = [c.name.unescaped for c in definition.columns]
        query: str = f'"{self._table_name.schema.value}"."{self._table_name.name}"'
        rows: List = connection.execute_list_query(f"SELECT * FROM {query}")
        return self._create_dataframe(rows, columns)

    def _create_dataframe(self, rows: List, columns: List[str]) -> pd.DataFrame:
        df: pd.DataFrame = pd.DataFrame(rows, columns=columns)
        df.attrs["_schema"] = self._table_name.schema.value
        df.attrs["_table"] = self._table_name.name
        return df
