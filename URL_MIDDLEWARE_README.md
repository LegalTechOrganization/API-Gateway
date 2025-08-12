# URL Middleware для API Gateway

## Описание

URL Middleware автоматически заменяет URL auth сервиса на URL API Gateway в ответах. Это позволяет клиентам получать ссылки, которые указывают на API Gateway, а не на внутренний auth сервис.

## Как это работает

1. **Auth сервис** работает по адресу: `http://host.docker.internal:8000`
2. **API Gateway** получает запросы от клиентов
3. **Middleware** автоматически заменяет все URL auth сервиса на URL API Gateway в ответах

## Конфигурация

### Docker Compose
```yaml
environment:
  AUTH_SERVICE_URL: http://host.docker.internal:8000
```

### Auth Client
```python
# services/auth_client.py
self.base_url = os.getenv("AUTH_SERVICE_URL", "http://host.docker.internal:8000")
```

## Примеры работы

### До middleware:
```json
{
  "links": {
    "sign_up": "http://host.docker.internal:8000/v1/client/sign-up",
    "sign_in": "http://localhost:8000/v1/client/sign-in/password"
  }
}
```

### После middleware (запрос к localhost:8002):
```json
{
  "links": {
    "sign_up": "http://localhost:8002/v1/client/sign-up",
    "sign_in": "http://localhost:8002/v1/client/sign-in/password"
  }
}
```

### После middleware (запрос к production серверу):
```json
{
  "links": {
    "sign_up": "https://api.mycompany.com/v1/client/sign-up",
    "sign_in": "https://api.mycompany.com/v1/client/sign-in/password"
  }
}
```

## Поддерживаемые URL для замены

Middleware заменяет следующие URL auth сервиса:
- `http://host.docker.internal:8000`
- `http://localhost:8000`
- `https://host.docker.internal:8000`
- `https://localhost:8000`

## Структура файлов

```
├── utils/
│   ├── __init__.py
│   └── url_builder.py          # Утилиты для работы с URL
├── middleware/
│   ├── __init__.py
│   └── url_middleware.py       # Middleware для замены URL
├── main.py                     # Подключение middleware
├── test_url_middleware.py      # Тесты
└── example_usage.py           # Примеры использования
```

## Тестирование

Запустите тесты:
```bash
python test_url_middleware.py
```

Запустите пример:
```bash
python example_usage.py
```

## Автоматическая работа

Middleware автоматически:
1. Перехватывает все JSON ответы
2. Находит URL auth сервиса в данных
3. Заменяет их на URL API Gateway
4. Возвращает преобразованный ответ

Никаких дополнительных действий в коде не требуется!
