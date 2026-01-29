from __future__ import annotations
from dataclasses import dataclass


@dataclass
class SchemaName:
    value: str


@dataclass
class TableName:
    schema: SchemaName
    name: str
