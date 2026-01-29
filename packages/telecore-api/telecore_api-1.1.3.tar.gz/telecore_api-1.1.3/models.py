"""
Pydantic модели для Telecore API.
Автоматически сгенерировано из OpenAPI спецификации.
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


# ============================================================================
# Базовые модели
# ============================================================================

class MetaInfo(BaseModel):
    """Метаданные для списочных ответов."""
    total: int = Field(description="Общее количество элементов")
    returned: int = Field(description="Количество возвращенных элементов")
    offset: int | None = Field(default=None, description="Смещение (offset)")
    has_more: bool | None = Field(default=None, description="Есть ли еще данные")
    query: str | None = Field(default=None, description="Поисковый запрос")
    model: str | None = Field(default=None, description="Использованная модель поиска")


class BaseResponse(BaseModel, Generic[T]):
    """Базовый ответ API."""
    success: bool = Field(default=True, description="Успешность запроса")
    data: T = Field(description="Данные ответа")
    meta: MetaInfo | None = Field(default=None, description="Метаданные (для списков)")
    cost: float = Field(default=0.0, description="Стоимость запроса в кредитах")
    balance: float | None = Field(default=None, description="Оставшийся баланс пользователя")
    note: str | None = Field(default=None, description="Примечания или предупреждения")
    error: dict[str, Any] | None = Field(default=None, description="Детали ошибки (если есть)")


# ============================================================================
# Модели пользователей
# ============================================================================

class TopChat(BaseModel):
    """Топ чат в профиле пользователя."""
    chat_id: int = Field(description="ID чата")
    title: str | None = Field(default=None, description="Название чата")
    messages_count: int = Field(description="Количество сообщений пользователя")
    is_private: bool = Field(default=False, description="Приватный ли чат")
    is_channel_chat: bool = Field(default=False, description="Является ли чатом канала (linked_chat)")
    link: str | None = Field(default=None, description="Ссылка на чат")


class MediaUsage(BaseModel):
    """Статистика использования медиа пользователем."""
    voice_messages: int = Field(default=0, description="Голосовых сообщений")
    video_circles: int = Field(default=0, description="Видео сообщений (кружочков)")
    photos_percent: float = Field(default=0.0, description="Процент фото")
    links_percent: float = Field(default=0.0, description="Процент ссылок")
    replies_percent: float = Field(default=0.0, description="Процент ответов")
    replies: int = Field(default=0, description="Количество ответов")
    files: int = Field(default=0, description="Количество файлов")
    stickers: int = Field(default=0, description="Количество стикеров")
    polls: int = Field(default=0, description="Количество опросов")
    videos: int = Field(default=0, description="Количество видео")
    photos: int = Field(default=0, description="Количество фото")
    links: int = Field(default=0, description="Количество ссылок")
    tags: int = Field(default=0, description="Количество упоминаний")


class UserProfile(BaseModel):
    """Данные профиля пользователя."""
    user_id: int = Field(description="ID пользователя в Telegram")
    first_name: str | None = Field(default=None, description="Имя")
    last_name: str | None = Field(default=None, description="Фамилия")
    username: str | None = Field(default=None, description="Юзернейм (без @)")
    is_bot: bool = Field(default=False)
    is_premium: bool = Field(default=False)
    is_verified: bool = Field(default=False)
    is_scam: bool = Field(default=False)
    is_fake: bool = Field(default=False)
    first_seen: str | None = Field(default=None, description="Дата первого обнаружения (ISO)")
    last_seen: str | None = Field(default=None, description="Дата последней активности (ISO)")
    bio: str | None = Field(default=None, description="Описание профиля")
    total_messages: int = Field(default=0, description="Всего сообщений")
    total_groups: int = Field(default=0)
    top_chats: list[TopChat] = Field(default_factory=list)
    media_usage: MediaUsage | None = Field(default=None)


class UserChatStats(BaseModel):
    """Статистика пользователя в конкретном чате."""
    chat_id: int = Field(description="ID чата")
    title: str | None = Field(default=None, description="Название чата")
    is_private: bool = Field(default=False, description="Приватный ли чат")
    link: str | None = Field(default=None, description="Ссылка на чат")
    description: str | None = Field(default=None, description="Описание чата")
    last_processed_date: str | None = Field(default=None, description="Последняя обработка")
    linked_channel: str | None = Field(default=None, description="Привязанный канал (если есть)")
    last_message_id: int = Field(default=0)
    messages_count: int = Field(default=0)
    last_message_date: str | None = Field(default=None)
    first_message_date: str | None = Field(default=None)
    is_admin: bool = Field(default=False)
    is_left: bool = Field(default=False)


# ============================================================================
# Модели сообщений
# ============================================================================

class Message(BaseModel):
    """Объект сообщения."""
    message_id: int = Field(description="ID сообщения")
    chat_id: int = Field(description="ID чата")
    text: str | None = Field(default=None, description="Текст сообщения")
    date: str = Field(description="Дата сообщения (ISO)")
    reply_to: int | None = Field(default=None, description="ID сообщения, на которое ответили")
    has_media: bool = Field(default=False, description="Есть ли медиа")
    media_type: str | None = Field(default=None, description="Тип медиа (photo, video, etc)")
    forwards: int | None = Field(default=0, description="Количество пересылок")
    views: int | None = Field(default=0, description="Количество просмотров")
    position: str | None = Field(default=None, description="Позиция в контексте (target/before/after)")


class ChatBasicInfo(BaseModel):
    """Базовая информация о чате."""
    chat_id: int = Field(description="ID чата")
    title: str | None = Field(default=None, description="Название чата")
    username: str | None = Field(default=None, description="Юзернейм")
    link: str | None = Field(default=None, description="Ссылка")


class MessagesList(BaseModel):
    """Список сообщений пользователя."""
    user_id: int = Field(description="ID пользователя")
    messages: list[Message] = Field(description="Список сообщений")
    chats: list[ChatBasicInfo] = Field(default_factory=list, description="Информация о чатах, где найдены сообщения")


class MessageContext(BaseModel):
    """Контекст вокруг сообщения."""
    chat_id: int = Field(description="ID чата")
    target_message_id: int = Field(description="ID целевого сообщения")
    messages: list[Message] = Field(description="Список сообщений (до, цель, после)")


class ContextRequest(BaseModel):
    """Запрос на пакетное получение контекста."""
    messages: list[dict[str, int]] = Field(description="Список объектов {chat_id, message_id}")


# ============================================================================
# Модели поиска
# ============================================================================

class SemanticSearchRequest(BaseModel):
    """Тело запроса для семантического поиска."""
    query: str = Field(description="Поисковый запрос")
    limit: int = Field(default=10, description="Лимит результатов (1-100)")
    sort_by_date: bool = Field(default=False, description="Сортировать по дате (сначала новые)")
    filters: dict[str, Any] | None = Field(default=None, description="Фильтры: chat_id, from_date, to_date")


class SemanticSearchResult(BaseModel):
    """Результат семантического поиска."""
    message_id: int
    chat_id: int
    chat_title: str | None = None
    text: str | None = None
    date: str
    score: float = Field(description="Оценка релевантности (0-1)")
    user_id: int | None = None
    views: int | None = None
    forwards: int | None = None


class SemanticSearchList(BaseModel):
    """Список результатов семантического поиска."""
    results: list[SemanticSearchResult]


# ============================================================================
# Модели истории
# ============================================================================

class UserChange(BaseModel):
    """Событие изменения профиля пользователя."""
    field: str = Field(description="Измененное поле")
    old_value: str | None = Field(default=None, description="Старое значение")
    new_value: str | None = Field(default=None, description="Новое значение")
    changed_at: str | None = Field(default=None, description="Время изменения")
    detected_at: str | None = Field(default=None, description="Время обнаружения системой")


class HistoryResponse(BaseModel):
    """Модель ответа для истории пользователя."""
    user_id: int
    changes: list[UserChange]


class HistoryMatch(BaseModel):
    """Совпадение в поиске по истории."""
    entity_type: str = Field(description="Тип сущности (user/chat)")
    entity_id: int = Field(description="ID сущности")
    field: str | None = Field(default=None, description="Поле, где найдено совпадение")
    old_value: str | None = None
    new_value: str | None = None
    changed_at: str | None = None


class HistorySearchResponse(BaseModel):
    """Модель ответа поиска по истории."""
    query: str
    field: str | None = None
    matches: list[HistoryMatch]


# ============================================================================
# Модели каналов
# ============================================================================

class Channel(BaseModel):
    """Channel summary."""
    chat_id: int
    title: str | None = None
    username: str | None = None
    link: str | None = None
    type: str | None = None
    members_count: int | None = Field(default=0)
    description: str | None = None
    is_verified: bool = Field(default=False)
    is_private: bool = Field(default=False)
    is_scam: bool = Field(default=False)
    created_at: str | None = None
    last_update: str | None = None


class ChannelInfo(Channel):
    """Detailed channel info."""
    is_fake: bool = Field(default=False)
    linked_chat_id: int | None = None
    parent_channel_id: int | None = None
    # Message stats
    total_messages: int | None = Field(default=0, description="Всего сообщений")
    first_message_id: int | None = Field(default=None, description="ID первого сообщения")
    last_message_id: int | None = Field(default=None, description="ID последнего сообщения")


# ============================================================================
# Модели аккаунта
# ============================================================================

class BalanceResponse(BaseModel):
    """Account balance response."""
    balance: float
    currency: str = Field(default="credits")


# ============================================================================
# Исключения
# ============================================================================

class TelecoreAPIError(Exception):
    """Базовое исключение API."""
    def __init__(self, message: str, status_code: int | None = None, response: dict | None = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(message)


class AuthenticationError(TelecoreAPIError):
    """Ошибка авторизации (401)."""
    pass


class RateLimitError(TelecoreAPIError):
    """Превышение лимитов (429)."""
    pass


class InsufficientBalanceError(TelecoreAPIError):
    """Недостаточно кредитов."""
    pass


class NotFoundError(TelecoreAPIError):
    """Ресурс не найден (404)."""
    pass
