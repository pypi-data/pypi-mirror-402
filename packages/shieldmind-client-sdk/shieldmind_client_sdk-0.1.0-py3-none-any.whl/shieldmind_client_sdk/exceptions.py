"""
Исключения для Shieldmind Client SDK
"""


class ShieldmindException(Exception):
    """Базовое исключение Shieldmind Client SDK"""

    def __init__(self, message: str, status_code: int = None, response: dict = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)


class ShieldmindAuthError(ShieldmindException):
    """Ошибка аутентификации"""

    pass


class ShieldmindAPIError(ShieldmindException):
    """Ошибка API"""

    pass


class ShieldmindRateLimitError(ShieldmindException):
    """Превышен лимит запросов"""

    pass


class ShieldmindValidationError(ShieldmindException):
    """Ошибка валидации данных"""

    pass
