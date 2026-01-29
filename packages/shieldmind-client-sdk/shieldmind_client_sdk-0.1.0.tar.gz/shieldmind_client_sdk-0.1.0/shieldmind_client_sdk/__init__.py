"""
Shieldmind Client SDK - Легковесный клиент для валидации LLM запросов
"""
from .client import ShieldmindClient
from .exceptions import (
    ShieldmindException,
    ShieldmindAuthError,
    ShieldmindAPIError,
    ShieldmindRateLimitError,
    ShieldmindValidationError,
)
from .models import ValidationResult, Threat, RemainingChecks

__version__ = "0.1.0"

__all__ = [
    "ShieldmindClient",
    "ShieldmindException",
    "ShieldmindAuthError",
    "ShieldmindAPIError",
    "ShieldmindRateLimitError",
    "ShieldmindValidationError",
    "ValidationResult",
    "Threat",
    "RemainingChecks",
]
