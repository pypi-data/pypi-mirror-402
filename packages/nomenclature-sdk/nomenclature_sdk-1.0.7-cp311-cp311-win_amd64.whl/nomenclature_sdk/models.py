from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

@dataclass(frozen=True)
class ConnectionOptions:
    """
    Опции для подключения к базе данных

    Attributes:
        server: Имя или IP-адрес сервера БД.
        database: Имя базы данных, к которой выполняется подключение.
        user: Имя пользователя SQL Server.
        password: Пароль пользователя.
        encrypt: Использовать ли шифрование соединения (TLS).
        port: TCP-порт SQL Server. По умолчанию: 1433.
        trust_server_certificate: Доверять ли сертификату сервера без проверки цепочки.
        timeout: Таймаут подключения в секундах.
    """
    server: str
    database: str
    user: str
    password: str
    encrypt: bool = True
    port: int = 1433
    trust_server_certificate: bool = False
    timeout: int = 5

@dataclass(frozen=True)
class DBInfo:
    """
    Информация о базе данных

    Attributes:
        nomenclature_count_rows: Количество записей в номенклатурном справочнике.
        manufacturer_synonym_count_rows: Количество синонимов для производителей.
        user_fields: Пользовательские поля
    """
    nomenclature_count_rows: int
    manufacturer_synonym_count_rows: int
    user_fields: List[str]

@dataclass(frozen=True)
class NomenclatureKey:
    """
    Ключ номенклатуры.

    Attributes:
        manufacturer: Производитель товара.
        identifier: Идентификатор товара.
    """
    manufacturer: str
    identifier: str

@dataclass(frozen=True)
class NomenclatureItem:
    """
    Товар номенклатуры.

    Attributes:
        key: Ключ номенклатуры.
        article: Артикул.
        arths_codeicle: Код ТН ВЭД.
        product_name: Наименвоание товара.
        product_details: Характеристики товара.
        product_model: Модель товара.
        product_brand: Марка товара.
    """
    key: NomenclatureKey
    article: Optional[str]
    hs_code: Optional[str]
    product_name: Optional[str]
    product_details: Optional[str] = None
    product_model: Optional[str] = None
    product_brand: Optional[str] = None

class NomenclatureFoundStatus(Enum):
    """
    Статус найденности.

    Attributes:
        FOUND_BY_MANUFACTURER_AND_IDENTIFIER = 1: Товар найден по производителю и идентификатору.
        FOUND_BY_MANUFACTURER_SYNONYM_AND_IDENTIFIER = 2: Товар найден по синониму производителя и идентификатору.
        NOT_FOUND = 3: Товар не найден.
    """
    FOUND_BY_MANUFACTURER_AND_IDENTIFIER = 1
    FOUND_BY_MANUFACTURER_SYNONYM_AND_IDENTIFIER = 2
    NOT_FOUND = 3

@dataclass(frozen=True)
class FieldCompareResult:
    """
    Результат сравнения поля.

    Attributes:
        input_value: Входящие данные.
        nomenclature_value: Данные из номенклатурного справочника.
        is_equal: Данные идентичны.
    """
    input_value: str
    nomenclature_value: str
    is_equal: bool

@dataclass(frozen=True)
class NomenclatureCheckResult:
    """
    Результат сравнения товара.

    Attributes:
        key: люч номенклатуры.
        article: Артикул.
        arths_codeicle: Код ТН ВЭД.
        product_name: Наименвоание товара.
        product_details: Характеристики товара.
        product_model: Модель товара.
        product_brand: Марка товара.
        found_status: Статус найденности.
        is_equal: Данные идентичны.
    """
    key: NomenclatureKey
    article: FieldCompareResult
    hs_code: FieldCompareResult
    product_name: FieldCompareResult
    product_details: FieldCompareResult
    product_model: FieldCompareResult
    product_brand: FieldCompareResult
    found_status: NomenclatureFoundStatus
    is_equal: bool