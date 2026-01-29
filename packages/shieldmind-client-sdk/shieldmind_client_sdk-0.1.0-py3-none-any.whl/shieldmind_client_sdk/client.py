"""
Основной клиент Shieldmind Client SDK
"""
import requests
from typing import Optional, Dict, Any
from .exceptions import (
    ShieldmindException,
    ShieldmindAuthError,
    ShieldmindAPIError,
    ShieldmindRateLimitError,
    ShieldmindValidationError,
)
from .models import ValidationResult, RemainingChecks


class ShieldmindClient:
    """Легковесный клиент для валидации LLM запросов через Shieldmind API"""

    def __init__(
        self,
        base_url: str = "http://localhost:3001",
        api_key: Optional[str] = None,
    ):
        """
        Инициализация клиента

        Args:
            base_url: URL Auth Service (по умолчанию http://localhost:3001)
            api_key: API ключ для аутентификации (опционально, можно использовать для публичного доступа)
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._session = requests.Session()

    def _get_headers(self, include_auth: bool = True) -> Dict[str, str]:
        """Получить заголовки для запроса"""
        headers = {"Content-Type": "application/json"}
        
        if include_auth and self.api_key:
            headers["x-api-key"] = self.api_key
        
        return headers

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Обработка ответа API"""
        try:
            data = response.json() if response.text else {}
        except ValueError:
            data = {"message": response.text}

        if response.status_code == 401:
            raise ShieldmindAuthError(
                message=data.get("message", "Authentication failed"),
                status_code=401,
                response=data,
            )
        elif response.status_code == 403:
            raise ShieldmindAuthError(
                message=data.get("message", "Access forbidden"),
                status_code=403,
                response=data,
            )
        elif response.status_code == 429:
            raise ShieldmindRateLimitError(
                message=data.get("message", "Rate limit exceeded"),
                status_code=429,
                response=data,
            )
        elif response.status_code >= 400:
            if response.status_code == 400:
                raise ShieldmindValidationError(
                    message=data.get("message", "Validation error"),
                    status_code=400,
                    response=data,
                )
            raise ShieldmindAPIError(
                message=data.get("message", f"API error: {response.status_code}"),
                status_code=response.status_code,
                response=data,
            )

        return data

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        include_auth: bool = True,
    ) -> Dict[str, Any]:
        """Выполнить HTTP запрос"""
        url = f"{self.base_url}/api/v1{endpoint}"
        
        request_headers = self._get_headers(include_auth)
        if headers:
            request_headers.update(headers)

        try:
            response = self._session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=request_headers,
                timeout=30,
            )
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            raise ShieldmindException(f"Request failed: {str(e)}")

    def check_llm(
        self,
        api_url: str,
        request_body: Dict[str, Any],
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ) -> ValidationResult:
        """
        Проверить промпт/запрос к LLM на угрозы безопасности

        Args:
            api_url: URL LLM API (например, https://api.openai.com/v1/chat/completions)
            request_body: Тело запроса к LLM API
            api_key: API ключ LLM (если требуется для проверки ответа)
            model: Название модели (опционально)

        Returns:
            ValidationResult с результатами проверки безопасности

        Example:
            >>> client = ShieldmindClient(api_key="your-key")
            >>> result = client.check_llm(
            ...     api_url="https://api.openai.com/v1/chat/completions",
            ...     request_body={"messages": [{"role": "user", "content": "Hello"}]}
            ... )
            >>> if result.isSafe:
            ...     print("Запрос безопасен!")
            >>> else:
            ...     print(f"Обнаружены угрозы: {result.threats}")
        """
        data: Dict[str, Any] = {
            "apiUrl": api_url,
            "requestBody": request_body,
        }
        if api_key:
            data["apiKey"] = api_key
        if model:
            data["model"] = model

        response = self._request("POST", "/llm-checker/check", data=data, include_auth=True)
        return ValidationResult.from_dict(response)

    def get_remaining_checks(self) -> RemainingChecks:
        """
        Получить информацию об оставшихся проверках

        Returns:
            RemainingChecks с информацией о лимитах и оставшихся проверках

        Example:
            >>> client = ShieldmindClient(api_key="your-key")
            >>> remaining = client.get_remaining_checks()
            >>> print(f"Осталось проверок: {remaining.remaining}/{remaining.limit}")
        """
        response = self._request("GET", "/llm-checker/remaining", include_auth=True)
        return RemainingChecks.from_dict(response)
