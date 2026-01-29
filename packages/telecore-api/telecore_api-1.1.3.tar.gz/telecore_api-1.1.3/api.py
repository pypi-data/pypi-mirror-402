"""
Высокоуровневый API клиент для Telecore.
Предоставляет удобные методы для всех эндпоинтов.
"""

from __future__ import annotations

from typing import Any

from .client import TelecoreClient, AsyncTelecoreClient, DEFAULT_BASE_URL, DEFAULT_TIMEOUT
from .models import (
    BaseResponse,
    UserProfile,
    UserChatStats,
    Message,
    MessagesList,
    MessageContext,
    ContextRequest,
    SemanticSearchRequest,
    SemanticSearchResult,
    SemanticSearchList,
    HistoryResponse,
    HistorySearchResponse,
    Channel,
    ChannelInfo,
    BalanceResponse,
)


class TelecoreAPI:
    """
    Высокоуровневый API клиент для Telecore.
    
    Предоставляет удобные методы для работы со всеми эндпоинтами API.
    
    Args:
        api_key: API ключ для авторизации
        base_url: Базовый URL API
        proxy: URL прокси сервера (http, https, socks5)
        timeout: Таймаут запросов в секундах
        
    Example:
        >>> api = TelecoreAPI(api_key="your-key", proxy="socks5://localhost:1080")
        >>> 
        >>> # Поиск пользователей
        >>> users = api.search_users(username="example")
        >>> for user in users.data:
        ...     print(f"{user.user_id}: {user.first_name}")
        >>> 
        >>> # Семантический поиск
        >>> results = api.semantic_search("CVE уязвимость", limit=20)
        >>> for msg in results.data.results:
        ...     print(f"{msg.score:.2f}: {msg.text[:50]}")
        >>> 
        >>> api.close()
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        proxy: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self._client = TelecoreClient(
            api_key=api_key,
            base_url=base_url,
            proxy=proxy,
            timeout=timeout,
        )
    
    def close(self) -> None:
        """Закрыть клиент."""
        self._client.close()
    
    def __enter__(self) -> TelecoreAPI:
        return self
    
    def __exit__(self, *args) -> None:
        self.close()
    
    # ========================================================================
    # Пользователи
    # ========================================================================
    
    def search_users(
        self,
        id: str | None = None,
        username: str | None = None,
        name: str | None = None,
        fuzzy: bool = False,
        limit: int = 25,
    ) -> BaseResponse[list[UserProfile]]:
        """
        Поиск пользователей по ID, юзернейму или имени.
        
        Args:
            id: Один или несколько ID пользователей (через запятую)
            username: Юзернейм для поиска
            name: Имя для поиска
            fuzzy: Включить нечеткий поиск
            limit: Максимум результатов (1-25)
            
        Returns:
            BaseResponse с списком найденных пользователей
            
        Example:
            >>> result = api.search_users(username="durov")
            >>> print(result.data[0].first_name)
        """
        data = self._client.get(
            "/api/v1/users/search",
            params={
                "id": id,
                "username": username,
                "name": name,
                "fuzzy": fuzzy,
                "limit": limit,
            }
        )
        
        return BaseResponse[list[UserProfile]](
            **{**data, "data": [UserProfile(**u) for u in data.get("data", [])]}
        )

    def get_user_chats(
        self,
        user_id: int,
        limit: int = 100,
    ) -> BaseResponse[list[UserChatStats]]:
        """
        Получить список чатов, в которых активен пользователь.
        
        Args:
            user_id: ID пользователя
            limit: Лимит чатов (1-500, по умолчанию 100)
            
        Returns:
            BaseResponse со списком статистики чатов
        """
        data = self._client.get(
            f"/api/v1/users/{user_id}/chats",
            params={
                "limit": limit,
            }
        )
        
        return BaseResponse[list[UserChatStats]](
            **{**data, "data": [UserChatStats(**c) for c in data.get("data", [])]}
        )

    # ========================================================================
    # Сообщения
    # ========================================================================
    
    def get_user_messages(
        self,
        user_id: int,
        chat_id: int | None = None,
        limit: int = 1000,
        offset: int = 0,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> BaseResponse[MessagesList]:
        """
        Получить сообщения, отправленные пользователем.
        
        Args:
            user_id: ID пользователя
            chat_id: Фильтр по ID чата (опционально)
            limit: Лимит сообщений (1-10000)
            offset: Смещение
            from_date: С даты (ISO формат)
            to_date: По дату (ISO формат)
            
        Returns:
            BaseResponse со списком сообщений
        """
        data = self._client.get(
            f"/api/v1/messages/user/{user_id}",
            params={
                "chat_id": chat_id,
                "limit": limit,
                "offset": offset,
                "from_date": from_date,
                "to_date": to_date,
            }
        )
        
        return BaseResponse[MessagesList](
            **{**data, "data": MessagesList(**data.get("data", {}))}
        )
    
    def get_message_context(
        self,
        chat_id: int,
        message_id: int,
        before: int = 5,
        after: int = 5,
    ) -> BaseResponse[MessageContext]:
        """
        Получить контекст сообщения (соседние сообщения).
        
        Args:
            chat_id: ID чата
            message_id: ID сообщения
            before: Количество сообщений до (0-20)
            after: Количество сообщений после (0-20)
            
        Returns:
            BaseResponse с контекстом сообщения
        """
        data = self._client.get(
            "/api/v1/messages/context",
            params={
                "chat_id": chat_id,
                "message_id": message_id,
                "before": before,
                "after": after,
            }
        )
        
        return BaseResponse[MessageContext](
            **{**data, "data": MessageContext(**data.get("data", {}))}
        )
    
    def get_context_batch(
        self,
        messages: list[dict[str, int]],
        before: int = 5,
        after: int = 5,
    ) -> BaseResponse[list[dict[str, Any]]]:
        """
        Пакетное получение контекста для нескольких сообщений.
        
        Args:
            messages: Список объектов {"chat_id": ..., "message_id": ...}
            before: Количество сообщений до (0-20)
            after: Количество сообщений после (0-20)
            
        Returns:
            BaseResponse со списком контекстов
            
        Example:
            >>> result = api.get_context_batch([
            ...     {"chat_id": -1001234, "message_id": 100},
            ...     {"chat_id": -1001234, "message_id": 200},
            ... ])
        """
        data = self._client.post(
            "/api/v1/messages/context/batch",
            json={"messages": messages, "before": before, "after": after},
        )
        
        return BaseResponse[list[dict[str, Any]]](
            **{**data, "data": data.get("data", [])}
        )

    def get_messages_range(
        self,
        chat_id: int,
        start_id: int,
        end_id: int,
    ) -> BaseResponse[list[Message]]:
        """
        Получить сообщения из чата по диапазону ID.
        
        Максимальный размер диапазона - 1000 сообщений.
        Если chat_id начинается с -100, поиск идет по канальному индексу.
        
        Args:
            chat_id: ID чата или канала (для канала ID начинается с -100)
            start_id: ID начального сообщения
            end_id: ID конечного сообщения
            
        Returns:
            BaseResponse со списком сообщений
        """
        data = self._client.get(
            "/api/v1/messages/range",
            params={
                "chat_id": chat_id,
                "start_id": start_id,
                "end_id": end_id,
            }
        )
        
        return BaseResponse[list[Message]](
            **{**data, "data": [Message(**m) for m in data.get("data", [])]}
        )
    
    # ========================================================================
    # Поиск
    # ========================================================================
    
    def semantic_search(
        self,
        query: str,
        limit: int = 10,
        sort_by_date: bool = False,
        chat_id: int | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> BaseResponse[SemanticSearchList]:
        """
        Гибридный семантический поиск (KNN + BM25).
        
        Комбинирует векторный поиск (по смыслу) и текстовый поиск
        (по ключевым словам) с использованием Reciprocal Rank Fusion.
        
        Args:
            query: Поисковый запрос
            limit: Лимит результатов (1-100)
            sort_by_date: Сортировать по дате (сначала новые)
            chat_id: Фильтр по ID чата
            from_date: С даты (ISO формат)
            to_date: По дату (ISO формат)
            
        Returns:
            BaseResponse с результатами поиска
            
        Example:
            >>> result = api.semantic_search(
            ...     "CVE chrome уязвимость",
            ...     limit=20,
            ...     sort_by_date=True
            ... )
            >>> for msg in result.data.results:
            ...     print(f"[{msg.score:.2f}] {msg.text[:80]}")
        """
        filters = {}
        if chat_id is not None:
            filters["chat_id"] = chat_id
        if from_date is not None:
            filters["from_date"] = from_date
        if to_date is not None:
            filters["to_date"] = to_date
        
        data = self._client.post(
            "/api/v1/search/semantic",
            json={
                "query": query,
                "limit": limit,
                "sort_by_date": sort_by_date,
                "filters": filters,  # всегда dict, пустой {} если нет фильтров
            }
        )
        
        return BaseResponse[SemanticSearchList](
            **{**data, "data": SemanticSearchList(**data.get("data", {"results": []}))}
        )
    
    # ========================================================================
    # История
    # ========================================================================
    
    def get_user_history(
        self,
        user_id: int,
        field: str | None = None,
        limit: int = 100,
    ) -> BaseResponse[HistoryResponse]:
        """
        Получить историю изменений профиля пользователя.
        
        Args:
            user_id: ID пользователя
            field: Фильтр по полю (username, first_name, last_name, phone, bio, photo)
            limit: Лимит записей (1-500)
            
        Returns:
            BaseResponse с историей изменений
        """
        data = self._client.get(
            f"/api/v1/history/user/{user_id}",
            params={
                "field": field,
                "limit": limit,
            }
        )
        
        return BaseResponse[HistoryResponse](
            **{**data, "data": HistoryResponse(**data.get("data", {"user_id": user_id, "changes": []}))}
        )
    
    def search_history(
        self,
        value: str,
        field: str | None = None,
        entity_type: str | None = None,
        limit: int = 50,
    ) -> BaseResponse[HistorySearchResponse]:
        """
        Поиск по истории изменений.
        
        Args:
            value: Значение для поиска (например @username, Antipov, telecore)
            field: Поле для поиска (username, first_name, last_name, phone, bio, photo)
            entity_type: Тип сущности (user/chat)
            limit: Лимит результатов (1-200)
            
        Returns:
            BaseResponse с найденными совпадениями
        """
        data = self._client.get(
            "/api/v1/history/search",
            params={
                "value": value,
                "field": field,
                "entity_type": entity_type,
                "limit": limit,
            }
        )
        
        return BaseResponse[HistorySearchResponse](
            **{**data, "data": HistorySearchResponse(**data.get("data", {"query": value, "matches": []}))}
        )
    
    # ========================================================================
    # Каналы
    # ========================================================================
    
    def search_channels(
        self,
        id: int | None = None,
        username: str | None = None,
        name: str | None = None,
        limit: int = 25,
    ) -> BaseResponse[list[Channel]]:
        """
        Поиск каналов и групп.
        
        Args:
            id: ID канала/группы
            username: Юзернейм (без @)
            name: Название (нечеткий поиск)
            limit: Лимит результатов (1-100)
            
        Returns:
            BaseResponse со списком каналов
        """
        data = self._client.get(
            "/api/v1/channels/search",
            params={
                "id": id,
                "username": username,
                "name": name,
                "limit": limit,
            }
        )
        
        return BaseResponse[list[Channel]](
            **{**data, "data": [Channel(**c) for c in data.get("data", [])]}
        )
    
    def get_channel_info(self, channel_id: int) -> BaseResponse[ChannelInfo]:
        """
        Получить детальную информацию о канале.
        
        Args:
            channel_id: ID канала
            
        Returns:
            BaseResponse с информацией о канале
        """
        data = self._client.get(f"/api/v1/channels/{channel_id}/info")
        
        return BaseResponse[ChannelInfo](
            **{**data, "data": ChannelInfo(**data.get("data", {}))}
        )
    
    # ========================================================================
    # Аккаунт
    # ========================================================================
    
    def get_balance(self) -> BaseResponse[BalanceResponse]:
        """
        Получить текущий баланс пользователя.
        
        Returns:
            BaseResponse с информацией о балансе
            
        Example:
            >>> result = api.get_balance()
            >>> print(f"Баланс: {result.data.balance} {result.data.currency}")
        """
        data = self._client.get("/api/v1/account/balance")
        
        return BaseResponse[BalanceResponse](
            **{**data, "data": BalanceResponse(**data.get("data", {}))}
        )
    
    # ========================================================================
    # Служебные
    # ========================================================================
    
    def health_check(self) -> dict[str, Any]:
        """
        Проверить работоспособность API.
        
        Returns:
            Ответ от /health эндпоинта
        """
        return self._client.get("/health")


class AsyncTelecoreAPI:
    """
    Асинхронный высокоуровневый API клиент для Telecore.
    
    Example:
        >>> async with AsyncTelecoreAPI(api_key="your-key") as api:
        ...     users = await api.search_users(username="example")
        ...     print(users.data)
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        proxy: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self._client = AsyncTelecoreClient(
            api_key=api_key,
            base_url=base_url,
            proxy=proxy,
            timeout=timeout,
        )
    
    async def close(self) -> None:
        """Закрыть клиент."""
        await self._client.close()
    
    async def __aenter__(self) -> AsyncTelecoreAPI:
        return self
    
    async def __aexit__(self, *args) -> None:
        await self.close()
    
    # ========================================================================
    # Пользователи
    # ========================================================================
    
    async def search_users(
        self,
        id: str | None = None,
        username: str | None = None,
        name: str | None = None,
        fuzzy: bool = False,
        limit: int = 25,
    ) -> BaseResponse[list[UserProfile]]:
        """Поиск пользователей по ID, юзернейму или имени."""
        data = await self._client.get(
            "/api/v1/users/search",
            params={
                "id": id,
                "username": username,
                "name": name,
                "fuzzy": fuzzy,
                "limit": limit,
            }
        )
        
        return BaseResponse[list[UserProfile]](
            **{**data, "data": [UserProfile(**u) for u in data.get("data", [])]}
        )

    async def get_user_chats(
        self,
        user_id: int,
        limit: int = 100,
    ) -> BaseResponse[list[UserChatStats]]:
        """Получить список чатов, в которых активен пользователь."""
        data = await self._client.get(
            f"/api/v1/users/{user_id}/chats",
            params={
                "limit": limit,
            }
        )
        
        return BaseResponse[list[UserChatStats]](
            **{**data, "data": [UserChatStats(**c) for c in data.get("data", [])]}
        )
    
    # ========================================================================
    # Сообщения
    # ========================================================================
    
    async def get_user_messages(
        self,
        user_id: int,
        chat_id: int | None = None,
        limit: int = 1000,
        offset: int = 0,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> BaseResponse[MessagesList]:
        """Получить сообщения, отправленные пользователем."""
        data = await self._client.get(
            f"/api/v1/messages/user/{user_id}",
            params={
                "chat_id": chat_id,
                "limit": limit,
                "offset": offset,
                "from_date": from_date,
                "to_date": to_date,
            }
        )
        
        return BaseResponse[MessagesList](
            **{**data, "data": MessagesList(**data.get("data", {}))}
        )
    
    async def get_message_context(
        self,
        chat_id: int,
        message_id: int,
        before: int = 5,
        after: int = 5,
    ) -> BaseResponse[MessageContext]:
        """Получить контекст сообщения."""
        data = await self._client.get(
            "/api/v1/messages/context",
            params={
                "chat_id": chat_id,
                "message_id": message_id,
                "before": before,
                "after": after,
            }
        )
        
        return BaseResponse[MessageContext](
            **{**data, "data": MessageContext(**data.get("data", {}))}
        )
    
    async def get_context_batch(
        self,
        messages: list[dict[str, int]],
        before: int = 5,
        after: int = 5,
    ) -> BaseResponse[list[dict[str, Any]]]:
        """Пакетное получение контекста для нескольких сообщений."""
        data = await self._client.post(
            "/api/v1/messages/context/batch",
            json={"messages": messages, "before": before, "after": after},
        )
        
        return BaseResponse[list[dict[str, Any]]](
            **{**data, "data": data.get("data", [])}
        )

    async def get_messages_range(
        self,
        chat_id: int,
        start_id: int,
        end_id: int,
    ) -> BaseResponse[list[Message]]:
        """Получить сообщения из чата по диапазону ID (макс. 1000)."""
        data = await self._client.get(
            "/api/v1/messages/range",
            params={
                "chat_id": chat_id,
                "start_id": start_id,
                "end_id": end_id,
            }
        )
        
        return BaseResponse[list[Message]](
            **{**data, "data": [Message(**m) for m in data.get("data", [])]}
        )
    
    # ========================================================================
    # Поиск
    # ========================================================================
    
    async def semantic_search(
        self,
        query: str,
        limit: int = 10,
        sort_by_date: bool = False,
        chat_id: int | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> BaseResponse[SemanticSearchList]:
        """Гибридный семантический поиск (KNN + BM25)."""
        filters = {}
        if chat_id is not None:
            filters["chat_id"] = chat_id
        if from_date is not None:
            filters["from_date"] = from_date
        if to_date is not None:
            filters["to_date"] = to_date
        
        data = await self._client.post(
            "/api/v1/search/semantic",
            json={
                "query": query,
                "limit": limit,
                "sort_by_date": sort_by_date,
                "filters": filters,  # всегда dict, пустой {} если нет фильтров
            }
        )
        
        return BaseResponse[SemanticSearchList](
            **{**data, "data": SemanticSearchList(**data.get("data", {"results": []}))}
        )
    
    # ========================================================================
    # История
    # ========================================================================
    
    async def get_user_history(
        self,
        user_id: int,
        field: str | None = None,
        limit: int = 100,
    ) -> BaseResponse[HistoryResponse]:
        """Получить историю изменений профиля пользователя."""
        data = await self._client.get(
            f"/api/v1/history/user/{user_id}",
            params={
                "field": field,
                "limit": limit,
            }
        )
        
        return BaseResponse[HistoryResponse](
            **{**data, "data": HistoryResponse(**data.get("data", {"user_id": user_id, "changes": []}))}
        )
    
    async def search_history(
        self,
        value: str,
        field: str | None = None,
        entity_type: str | None = None,
        limit: int = 50,
    ) -> BaseResponse[HistorySearchResponse]:
        """Поиск по истории изменений."""
        data = await self._client.get(
            "/api/v1/history/search",
            params={
                "value": value,
                "field": field,
                "entity_type": entity_type,
                "limit": limit,
            }
        )
        
        return BaseResponse[HistorySearchResponse](
            **{**data, "data": HistorySearchResponse(**data.get("data", {"query": value, "matches": []}))}
        )
    
    # ========================================================================
    # Каналы
    # ========================================================================
    
    async def search_channels(
        self,
        id: int | None = None,
        username: str | None = None,
        name: str | None = None,
        limit: int = 25,
    ) -> BaseResponse[list[Channel]]:
        """Поиск каналов и групп."""
        data = await self._client.get(
            "/api/v1/channels/search",
            params={
                "id": id,
                "username": username,
                "name": name,
                "limit": limit,
            }
        )
        
        return BaseResponse[list[Channel]](
            **{**data, "data": [Channel(**c) for c in data.get("data", [])]}
        )
    
    async def get_channel_info(self, channel_id: int) -> BaseResponse[ChannelInfo]:
        """Получить детальную информацию о канале."""
        data = await self._client.get(f"/api/v1/channels/{channel_id}/info")
        
        return BaseResponse[ChannelInfo](
            **{**data, "data": ChannelInfo(**data.get("data", {}))}
        )
    
    # ========================================================================
    # Аккаунт
    # ========================================================================
    
    async def get_balance(self) -> BaseResponse[BalanceResponse]:
        """Получить текущий баланс пользователя."""
        data = await self._client.get("/api/v1/account/balance")
        
        return BaseResponse[BalanceResponse](
            **{**data, "data": BalanceResponse(**data.get("data", {}))}
        )
    
    # ========================================================================
    # Служебные
    # ========================================================================
    
    async def health_check(self) -> dict[str, Any]:
        """Проверить работоспособность API."""
        return await self._client.get("/health")
