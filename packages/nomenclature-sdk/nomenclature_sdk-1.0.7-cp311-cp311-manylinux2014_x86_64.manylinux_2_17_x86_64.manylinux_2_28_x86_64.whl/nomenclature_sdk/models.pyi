from dataclasses import dataclass
from enum import Enum

@dataclass(frozen=True)
class ConnectionOptions:
    server: str
    database: str
    user: str
    password: str
    encrypt: bool = ...
    port: int = ...
    trust_server_certificate: bool = ...
    timeout: int = ...

@dataclass(frozen=True)
class DBInfo:
    nomenclature_count_rows: int
    manufacturer_synonym_count_rows: int
    user_fields: list[str]

@dataclass(frozen=True)
class NomenclatureKey:
    manufacturer: str
    identifier: str

@dataclass(frozen=True)
class NomenclatureItem:
    key: NomenclatureKey
    article: str | None
    hs_code: str | None
    product_name: str | None
    product_details: str | None = ...
    product_model: str | None = ...
    product_brand: str | None = ...

class NomenclatureFoundStatus(Enum):
    FOUND_BY_MANUFACTURER_AND_IDENTIFIER = 1
    FOUND_BY_MANUFACTURER_SYNONYM_AND_IDENTIFIER = 2
    NOT_FOUND = 3

@dataclass(frozen=True)
class FieldCompareResult:
    input_value: str
    nomenclature_value: str
    is_equal: bool

@dataclass(frozen=True)
class NomenclatureCheckResult:
    key: NomenclatureKey
    article: FieldCompareResult
    hs_code: FieldCompareResult
    product_name: FieldCompareResult
    product_details: FieldCompareResult
    product_model: FieldCompareResult
    product_brand: FieldCompareResult
    found_status: NomenclatureFoundStatus
    is_equal: bool
