# Интеграция Полного Имени (Full Name) в API Gateway

## Обзор

API Gateway теперь полностью поддерживает поле `full_name` (полное имя) в системе аутентификации. Это включает регистрацию пользователей с полным именем и получение этой информации через различные эндпоинты.

## Основные изменения

### 1. Регистрация пользователей (Sign-up)

**Endpoint:** `POST /v1/client/sign-up`

Теперь требует обязательное поле `full_name`:

```json
{
  "email": "user@example.com",
  "password": "password123",
  "full_name": "Иван Иванов"
}
```

### 2. Получение информации о пользователе (Me)

**Endpoint:** `GET /v1/client/me`

Возвращает информацию о пользователе, включая `full_name`:

```json
{
  "user_id": "user-123",
  "email": "user@example.com",
  "full_name": "Иван Иванов",
  "orgs": []
}
```

## Изменения в коде

### routers/auth.py

1. **Обновлена схема SignUpRequest:**
```python
class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str = Field(..., min_length=1, description="Полное имя пользователя")
```

2. **Обновлен вызов auth-service:**
```python
auth_result = await auth_client.sign_up(data.email, data.password, data.full_name)
```

3. **Обновлены события Kafka:**
```python
# В sign-up
await send_auth_event("user_registered", {
    "email": data.email,
    "full_name": data.full_name
})

# В /me
await send_user_event("user_info_requested", {
    "user_id": result.get("user_id"),
    "full_name": result.get("full_name")
})
```

### services/auth_client.py

Метод `sign_up` уже поддерживал `full_name`:
```python
async def sign_up(self, email: str, password: str, full_name: str) -> Dict[str, Any]:
    data = {
        "email": email,
        "password": password,
        "full_name": full_name
    }
    return await self._make_request("POST", "/v1/client/sign-up", data)
```

### utils/jwt_utils.py

Функция `transform_user_response` корректно обрабатывает `full_name`:
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

## Схемы данных

### User (все эндпоинты)
```python
class User(BaseModel):
    user_id: str = Field(..., example="user-123")
    email: EmailStr
    full_name: Optional[str] = None  # Опционально для обратной совместимости
    orgs: Optional[List[dict]] = None
```

### UserDetailInfo (внутренние эндпоинты)
```python
class UserDetailInfo(BaseModel):
    id: str
    email: EmailStr
    full_name: Optional[str] = None  # Поддержка full_name
    active_org_id: Optional[str] = None
```

## Валидация

### Sign-up валидация
- `full_name` обязательное поле
- `full_name` не может быть пустой строкой (min_length=1)
- Email должен быть валидным
- Пароль обязателен

### Me endpoint валидация
- Токен авторизации обязателен (Bearer или Cookie)
- Токен должен быть валидным
- `full_name` может быть null (для обратной совместимости)

## Тестирование

### test_signup_with_fullname.py
- ✅ Успешная регистрация с полным именем
- ✅ Проверка ошибки при отсутствии полного имени
- ✅ Проверка ошибки при пустом полном имени

### test_me_endpoint.py
- ✅ Успешный запрос с полным именем
- ✅ Запрос без авторизации
- ✅ Запрос с невалидным токеном
- ✅ Запрос с токеном в cookie

## Совместимость

### Обратная совместимость
- ❌ **Sign-up**: Нет (требует обязательное поле `full_name`)
- ✅ **Me endpoint**: Да (`full_name` опционально в ответе)
- ✅ **Auth-service**: Поддерживает `full_name`
- ✅ **Kafka события**: Включают `full_name`

### Поддерживаемые форматы авторизации
- ✅ Bearer токен в заголовке Authorization
- ✅ HTTP-Only cookies
- ✅ Автоматическое переключение между форматами

## Документация

Созданы следующие файлы документации:
- `SIGNUP_API_README.md` - Документация API регистрации
- `ME_ENDPOINT_README.md` - Документация эндпоинта /me
- `FULL_NAME_INTEGRATION_README.md` - Общая документация интеграции

## Примеры использования

### Регистрация нового пользователя
```bash
curl -X POST "http://localhost:8000/v1/client/sign-up" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "ivan@example.com",
    "password": "securepassword123",
    "full_name": "Иван Петрович Иванов"
  }'
```

### Получение информации о пользователе
```bash
curl -X GET "http://localhost:8000/v1/client/me" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Обработка ошибок

### Sign-up ошибки
- `422 Unprocessable Entity`: Невалидные данные (пустое имя, невалидный email)
- `409 Conflict`: Пользователь уже существует
- `500 Internal Server Error`: Внутренняя ошибка

### Me endpoint ошибки
- `401 Unauthorized`: Неверный или отсутствующий токен
- `500 Internal Server Error`: Внутренняя ошибка

## События Kafka

### user_registered
```json
{
  "email": "user@example.com",
  "full_name": "Иван Иванов"
}
```

### user_info_requested
```json
{
  "user_id": "user-123",
  "full_name": "Иван Иванов"
}
```

## Заключение

Интеграция `full_name` полностью завершена. Система теперь:
- Требует полное имя при регистрации
- Возвращает полное имя в ответах
- Поддерживает валидацию
- Включает полное имя в события Kafka
- Имеет полное тестовое покрытие
- Документирована для разработчиков
