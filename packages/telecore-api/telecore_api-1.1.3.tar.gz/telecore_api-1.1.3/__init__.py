"""
Telecore API Client Library
============================

Удобная Python библиотека для работы с Telegram Database API
(https://api.telecore.info) с поддержкой proxy.

Быстрый старт
-------------

>>> from telecore import TelecoreAPI
>>> 
>>> # Создание клиента
>>> api = TelecoreAPI(api_key="your-api-key")
>>> 
>>> # С proxy
>>> api = TelecoreAPI(
...     api_key="your-api-key",
...     proxy="socks5://localhost:1080"
... )
>>> 
>>> # Поиск пользователей
>>> result = api.search_users(username="durov")
>>> for user in result.data:
...     print(f"{user.user_id}: {user.first_name} {user.last_name}")
>>> 
>>> # Семантический поиск
>>> result = api.semantic_search("CVE уязвимость", limit=10)
>>> for msg in result.data.results:
...     print(f"[{msg.score:.2f}] {msg.text[:50]}")
>>> 
>>> # Баланс
>>> balance = api.get_balance()
>>> print(f"Баланс: {balance.data.balance} {balance.data.currency}")
>>> 
>>> api.close()

Асинхронное использование
-------------------------

>>> import asyncio
>>> from telecore import AsyncTelecoreAPI
>>> 
>>> async def main():
...     async with AsyncTelecoreAPI(api_key="your-key") as api:
...         users = await api.search_users(username="example")
...         print(users.data)
>>> 
>>> asyncio.run(main())
"""

__version__ = "1.1.2"
__author__ = "Telecore"

# Основные классы API
from .api import TelecoreAPI, AsyncTelecoreAPI

# Низкоуровневые HTTP клиенты
from .client import TelecoreClient, AsyncTelecoreClient

# Все модели данных
from .models import (
    # Базовые
    BaseResponse,
    MetaInfo,
    
    # Пользователи
    UserProfile,
    UserChatStats,
    TopChat,
    MediaUsage,
    
    # Сообщения
    Message,
    MessagesList,
    MessageContext,
    ContextRequest,
    ChatBasicInfo,
    
    # Поиск
    SemanticSearchRequest,
    SemanticSearchResult,
    SemanticSearchList,
    
    # История
    HistoryResponse,
    HistorySearchResponse,
    UserChange,
    HistoryMatch,
    
    # Каналы
    Channel,
    ChannelInfo,
    
    # Аккаунт
    BalanceResponse,
    
    # Исключения
    TelecoreAPIError,
    AuthenticationError,
    RateLimitError,
    InsufficientBalanceError,
    NotFoundError,
)

__all__ = [
    # Версия
    "__version__",
    
    # API классы
    "TelecoreAPI",
    "AsyncTelecoreAPI",
    "TelecoreClient",
    "AsyncTelecoreClient",
    
    # Модели
    "BaseResponse",
    "MetaInfo",
    "UserProfile",
    "UserChatStats",
    "TopChat",
    "MediaUsage",
    "Message",
    "MessagesList",
    "MessageContext",
    "ContextRequest",
    "ChatBasicInfo",
    "SemanticSearchRequest",
    "SemanticSearchResult",
    "SemanticSearchList",
    "HistoryResponse",
    "HistorySearchResponse",
    "UserChange",
    "HistoryMatch",
    "Channel",
    "ChannelInfo",
    "BalanceResponse",
    
    # Исключения
    "TelecoreAPIError",
    "AuthenticationError",
    "RateLimitError",
    "InsufficientBalanceError",
    "NotFoundError",
]
