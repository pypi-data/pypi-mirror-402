# Telecore API Client

Python клиент для работы с [Telecore Telegram Database API](https://api.telecore.info) с поддержкой proxy.

## Установка

```bash
pip install telecore-api
```

## Быстрый старт

```python
from telecore import TelecoreAPI

# Создание клиента
api = TelecoreAPI(api_key="your-api-key")

# С proxy
api = TelecoreAPI(
    api_key="your-api-key",
    proxy="socks5://localhost:1080"
)
pypi-AgEIcHlwaS5vcmcCJDY1MzkzM2M5LTBiNWMtNGZkZC1hNDIwLWJjODZkNGUxOWVjMQACKlszLCI3Y2M5OWQ1ZS1mZDUxLTQxMDYtYTljZC0zMTAzYzg4YzBkZmMiXQAABiCCU23tYLL7N__08s-sufPfXy--pvsl0KAVFGykZ2_wNA
# Поиск пользователей
result = api.search_users(username="durov")
for user in result.data:
    print(f"{user.user_id}: {user.first_name}")

# Семантический поиск
result = api.semantic_search("уязвимость CVE", limit=10)
for msg in result.data.results:
    print(f"[{msg.score:.2f}] {msg.text[:50]}")

# Баланс
balance = api.get_balance()
print(f"Баланс: {balance.data.balance}")

api.close()
```

## Async

```python
import asyncio
from telecore import AsyncTelecoreAPI

async def main():
    async with AsyncTelecoreAPI(api_key="your-key") as api:
        users = await api.search_users(username="example")
        print(users.data)

asyncio.run(main())
```

## Proxy Support

```python
# HTTP/HTTPS
api = TelecoreAPI(api_key="xxx", proxy="http://proxy:8080")

# SOCKS5
api = TelecoreAPI(api_key="xxx", proxy="socks5://localhost:1080")

# С аутентификацией
api = TelecoreAPI(api_key="xxx", proxy="http://user:pass@proxy:8080")
```

## API Методы

| Метод | Описание |
|-------|----------|
| `search_users()` | Поиск пользователей |
| `get_user_messages()` | Сообщения пользователя |
| `get_message_context()` | Контекст сообщения |
| `semantic_search()` | Семантический поиск |
| `get_user_history()` | История изменений профиля |
| `search_history()` | Поиск по истории |
| `search_channels()` | Поиск каналов |
| `get_channel_info()` | Информация о канале |
| `get_balance()` | Баланс аккаунта |

## License

MIT
