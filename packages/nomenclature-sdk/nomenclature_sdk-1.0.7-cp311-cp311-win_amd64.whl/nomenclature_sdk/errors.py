class SDKError(Exception):
    """Базовая ошибка SDK"""

class ConnectionError(SDKError):
    pass


class QueryError(SDKError):
    pass