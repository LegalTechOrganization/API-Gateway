# API Эндпоинта /me с Поддержкой Полного Имени

## Обзор

Эндпоинт `/v1/client/me` возвращает информацию о текущем авторизованном пользователе, включая полное имя (`full_name`).

## Endpoint

### GET /v1/client/me

Возвращает информацию о текущем пользователе.

#### Заголовки

| Заголовок | Тип | Обязательный | Описание |
|-----------|-----|--------------|----------|
| `Authorization` | string | Нет* | Bearer токен (если не указан, используется cookie) |
| Cookie | string | Нет* | HTTP-Only cookie с токеном (если не указан Authorization) |

*Один из способов авторизации должен быть указан

#### Ответ

**Статус:** `200 OK`

```json
{
  "user_id": "user-123",
  "email": "user@example.com",
  "full_name": "Иван Иванов",
  "orgs": [
    {
      "org_id": "org-456",
      "name": "Моя Организация",
      "role": "admin"
    }
  ]
}
```

#### Параметры ответа

| Параметр | Тип | Описание |
|----------|-----|----------|
| `user_id` | string | Уникальный идентификатор пользователя |
| `email` | string | Email пользователя |
| `full_name` | string | Полное имя пользователя (может быть null) |
| `orgs` | array | Список организаций пользователя |

#### Ошибки

| Статус | Описание |
|--------|----------|
| `401 Unauthorized` | Неверный или отсутствующий токен авторизации |
| `500 Internal Server Error` | Внутренняя ошибка сервера |

## Примеры использования

### Успешный запрос с Bearer токеном

```bash
curl -X GET "http://localhost:8000/v1/client/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Успешный запрос с cookie

```bash
curl -X GET "http://localhost:8000/v1/client/me" \
  -H "Cookie: access_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Запрос без авторизации

```bash
curl -X GET "http://localhost:8000/v1/client/me"
```

Ответ:
```json
{
  "detail": "Missing or invalid authorization header or cookie"
}
```

### Запрос с невалидным токеном

```bash
curl -X GET "http://localhost:8000/v1/client/me" \
  -H "Authorization: Bearer invalid_token"
```

Ответ:
```json
{
  "detail": "Invalid or expired token"
}
```

## Обработка full_name

### В ответе от auth-service

Auth-service теперь возвращает `full_name` в ответе:

```json
{
  "sub": "user-id",
  "email": "user@example.com", 
  "full_name": "Иван Иванов",
  "orgs": [...],
  "active_org_id": "org-id"
}
```

### Преобразование в API Gateway

Функция `transform_user_response` в `utils/jwt_utils.py` корректно обрабатывает поле `full_name`:

```python
def transform_user_response(auth_result: Dict[str, Any]) -> Dict[str, Any]:
    result = {
        "user_id": auth_result.get("user_id", "unknown"),
        "email": auth_result.get("email", "unknown@example.com"),
        "full_name": auth_result.get("full_name"),  # Поддержка full_name
        "orgs": auth_result.get("orgs", [])
    }
    return result
```

### Схема User

Схема `User` в `routers/auth.py` поддерживает `full_name` как опциональное поле:

```python
class User(BaseModel):
    user_id: str = Field(..., example="user-123")
    email: EmailStr
    full_name: Optional[str] = None  # Поддержка full_name
    orgs: Optional[List[dict]] = None
```

## Тестирование

Для тестирования эндпоинта `/me` создан файл `test_me_endpoint.py` с тестами:

- Успешный запрос с полным именем
- Запрос без авторизации
- Запрос с невалидным токеном
- Запрос с токеном в cookie

Запуск тестов:
```bash
python test_me_endpoint.py
```

## Совместимость

- ✅ Обратная совместимость: Да (full_name опционально)
- ✅ Auth-service: Поддерживает full_name в ответе
- ✅ Cookie авторизация: Поддерживается
- ✅ Bearer токен: Поддерживается
- ✅ Валидация токена: Проверяется перед запросом к auth-service

## Изменения в системе

### 1. Обновлена обработка ответа от auth-service

Auth-service теперь возвращает `full_name` в ответе `/me`, и API Gateway корректно обрабатывает это поле.

### 2. Поддержка в схемах

Схема `User` уже поддерживала `full_name` как опциональное поле.

### 3. Преобразование данных

Функция `transform_user_response` корректно обрабатывает поле `full_name` из ответа auth-service.

### 4. Тестирование

Добавлены тесты для проверки корректной работы с `full_name`.
