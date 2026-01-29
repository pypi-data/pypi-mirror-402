"""
HTTP клиент для Telecore API с поддержкой proxy.
"""

from __future__ import annotations

from typing import Any, TypeVar
import httpx

from .models import (
    BaseResponse,
    TelecoreAPIError,
    AuthenticationError,
    RateLimitError,
    InsufficientBalanceError,
    NotFoundError,
)

T = TypeVar("T")

DEFAULT_BASE_URL = "https://api.telecore.info"
DEFAULT_TIMEOUT = 60.0


class TelecoreClient:
    """
    HTTP клиент для работы с Telecore API.
    
    Args:
        api_key: API ключ для авторизации (Bearer token)
        base_url: Базовый URL API (по умолчанию https://api.telecore.info)
        proxy: URL прокси сервера (поддерживает http, https, socks5)
               Примеры:
               - "http://proxy:8080"
               - "http://user:pass@proxy:8080"
               - "socks5://localhost:1080"
        timeout: Таймаут запросов в секундах (по умолчанию 30)
        
    Example:
        >>> client = TelecoreClient(api_key="your-api-key")
        >>> result = client.get("/api/v1/account/balance")
        >>> print(result["data"]["balance"])
        
        >>> # С прокси
        >>> client = TelecoreClient(
        ...     api_key="your-api-key",
        ...     proxy="socks5://localhost:1080"
        ... )
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        proxy: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.proxy = proxy
        self.timeout = timeout
        
        self._client: httpx.Client | None = None
    
    def _get_client(self) -> httpx.Client:
        """Получить или создать HTTP клиент."""
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.base_url,
                proxy=self.proxy,
                timeout=self.timeout,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )
        return self._client
    
    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """
        Обработать ответ API.
        
        Raises:
            AuthenticationError: При ошибке авторизации (401)
            RateLimitError: При превышении лимитов (429)
            NotFoundError: Когда ресурс не найден (404)
            TelecoreAPIError: При других ошибках API
        """
        try:
            data = response.json()
        except Exception:
            data = {"error": response.text}
        
        if response.status_code == 401:
            raise AuthenticationError(
                "Ошибка авторизации. Проверьте API ключ.",
                status_code=401,
                response=data,
            )
        
        if response.status_code == 403:
            # Может быть недостаточно баланса
            error_msg = data.get("detail", "") or data.get("error", "")
            if "balance" in str(error_msg).lower() or "credits" in str(error_msg).lower():
                raise InsufficientBalanceError(
                    "Недостаточно кредитов на балансе.",
                    status_code=403,
                    response=data,
                )
            raise TelecoreAPIError(
                f"Доступ запрещен: {error_msg}",
                status_code=403,
                response=data,
            )
        
        if response.status_code == 404:
            raise NotFoundError(
                "Ресурс не найден.",
                status_code=404,
                response=data,
            )
        
        if response.status_code == 429:
            raise RateLimitError(
                "Превышен лимит запросов. Подождите и повторите.",
                status_code=429,
                response=data,
            )
        
        if response.status_code >= 400:
            error_msg = data.get("detail", "") or data.get("error", "") or str(data)
            raise TelecoreAPIError(
                f"Ошибка API: {error_msg}",
                status_code=response.status_code,
                response=data,
            )
        
        return data
    
    def get(
        self, 
        path: str, 
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        GET запрос к API.
        
        Args:
            path: Путь эндпоинта (например "/api/v1/users/search")
            params: Query параметры
            
        Returns:
            Ответ API в виде словаря
        """
        client = self._get_client()
        
        # Убираем None значения из параметров
        if params:
            params = {k: v for k, v in params.items() if v is not None}
        
        response = client.get(path, params=params)
        return self._handle_response(response)
    
    def post(
        self,
        path: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        POST запрос к API.
        
        Args:
            path: Путь эндпоинта
            json: Тело запроса (JSON)
            params: Query параметры
            
        Returns:
            Ответ API в виде словаря
        """
        client = self._get_client()
        
        # Убираем None значения
        if params:
            params = {k: v for k, v in params.items() if v is not None}
        if json:
            json = {k: v for k, v in json.items() if v is not None}
        
        response = client.post(path, json=json, params=params)
        return self._handle_response(response)
    
    def close(self) -> None:
        """Закрыть HTTP клиент."""
        if self._client is not None:
            self._client.close()
            self._client = None
    
    def __enter__(self) -> TelecoreClient:
        return self
    
    def __exit__(self, *args) -> None:
        self.close()


class AsyncTelecoreClient:
    """
    Асинхронный HTTP клиент для работы с Telecore API.
    
    Args:
        api_key: API ключ для авторизации (Bearer token)
        base_url: Базовый URL API
        proxy: URL прокси сервера
        timeout: Таймаут запросов в секундах
        
    Example:
        >>> async with AsyncTelecoreClient(api_key="your-api-key") as client:
        ...     result = await client.get("/api/v1/account/balance")
        ...     print(result["data"]["balance"])
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        proxy: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.proxy = proxy
        self.timeout = timeout
        
        self._client: httpx.AsyncClient | None = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Получить или создать async HTTP клиент."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                proxy=self.proxy,
                timeout=self.timeout,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )
        return self._client
    
    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Обработать ответ API."""
        try:
            data = response.json()
        except Exception:
            data = {"error": response.text}
        
        if response.status_code == 401:
            raise AuthenticationError(
                "Ошибка авторизации. Проверьте API ключ.",
                status_code=401,
                response=data,
            )
        
        if response.status_code == 403:
            error_msg = data.get("detail", "") or data.get("error", "")
            if "balance" in str(error_msg).lower() or "credits" in str(error_msg).lower():
                raise InsufficientBalanceError(
                    "Недостаточно кредитов на балансе.",
                    status_code=403,
                    response=data,
                )
            raise TelecoreAPIError(
                f"Доступ запрещен: {error_msg}",
                status_code=403,
                response=data,
            )
        
        if response.status_code == 404:
            raise NotFoundError(
                "Ресурс не найден.",
                status_code=404,
                response=data,
            )
        
        if response.status_code == 429:
            raise RateLimitError(
                "Превышен лимит запросов. Подождите и повторите.",
                status_code=429,
                response=data,
            )
        
        if response.status_code >= 400:
            error_msg = data.get("detail", "") or data.get("error", "") or str(data)
            raise TelecoreAPIError(
                f"Ошибка API: {error_msg}",
                status_code=response.status_code,
                response=data,
            )
        
        return data
    
    async def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """GET запрос к API."""
        client = await self._get_client()
        
        if params:
            params = {k: v for k, v in params.items() if v is not None}
        
        response = await client.get(path, params=params)
        return self._handle_response(response)
    
    async def post(
        self,
        path: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """POST запрос к API."""
        client = await self._get_client()
        
        if params:
            params = {k: v for k, v in params.items() if v is not None}
        if json:
            json = {k: v for k, v in json.items() if v is not None}
        
        response = await client.post(path, json=json, params=params)
        return self._handle_response(response)
    
    async def close(self) -> None:
        """Закрыть HTTP клиент."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
    
    async def __aenter__(self) -> AsyncTelecoreClient:
        return self
    
    async def __aexit__(self, *args) -> None:
        await self.close()
