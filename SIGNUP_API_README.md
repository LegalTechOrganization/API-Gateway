# API Регистрации с Полным Именем

## Обзор

API Gateway теперь поддерживает регистрацию пользователей с полным именем. Это позволяет собирать дополнительную информацию о пользователях при регистрации.

## Endpoint

### POST /v1/client/sign-up

Регистрирует нового пользователя в системе.

#### Запрос

**Content-Type:** `application/json`

```json
{
  "email": "user@example.com",
  "password": "password123",
  "full_name": "Иван Иванов"
}
```

#### Параметры

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| `email` | string | Да | Email пользователя (должен быть валидным email) |
| `password` | string | Да | Пароль пользователя |
| `full_name` | string | Да | Полное имя пользователя (не может быть пустым) |

#### Ответ

**Статус:** `201 Created`

```json
{
  "jwt": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "user_id": "user-123",
    "email": "user@example.com",
    "full_name": "Иван Иванов",
    "orgs": []
  }
}
```

#### Ошибки

| Статус | Описание |
|--------|----------|
| `400 Bad Request` | Неверные данные запроса |
| `422 Unprocessable Entity` | Ошибка валидации (например, невалидный email или пустое полное имя) |
| `409 Conflict` | Пользователь с таким email уже существует |
| `500 Internal Server Error` | Внутренняя ошибка сервера |

## Примеры использования

### Успешная регистрация

```bash
curl -X POST "http://localhost:8000/v1/client/sign-up" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "ivan@example.com",
    "password": "securepassword123",
    "full_name": "Иван Петрович Иванов"
  }'
```

### Ошибка валидации (пустое полное имя)

```bash
curl -X POST "http://localhost:8000/v1/client/sign-up" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "full_name": ""
  }'
```

Ответ:
```json
{
  "detail": [
    {
      "loc": ["body", "full_name"],
      "msg": "ensure this value has at least 1 characters",
      "type": "value_error.any_str.min_length"
    }
  ]
}
```

### Ошибка валидации (отсутствует полное имя)

```bash
curl -X POST "http://localhost:8000/v1/client/sign-up" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'
```

Ответ:
```json
{
  "detail": [
    {
      "loc": ["body", "full_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## Изменения в системе

### 1. Обновлена схема SignUpRequest

Добавлено обязательное поле `full_name` с валидацией:

```python
class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str = Field(..., min_length=1, description="Полное имя пользователя")
```

### 2. Обновлен вызов auth-service

Теперь `full_name` передается в auth-service:

```python
auth_result = await auth_client.sign_up(data.email, data.password, data.full_name)
```

### 3. Обновлено событие Kafka

В событие `user_registered` добавлено поле `full_name`:

```python
await send_auth_event("user_registered", {
    "email": data.email,
    "full_name": data.full_name
})
```

## Тестирование

Для тестирования API создан файл `test_signup_with_fullname.py` с тестами:

- Успешная регистрация с полным именем
- Проверка ошибки при отсутствии полного имени
- Проверка ошибки при пустом полном имени

Запуск тестов:
```bash
python test_signup_with_fullname.py
```

## Совместимость

- ✅ Обратная совместимость: Нет (требует обязательное поле `full_name`)
- ✅ Auth-service: Поддерживает `full_name` в методе `sign_up`
- ✅ Kafka события: Включают `full_name`
- ✅ Валидация: Проверка на непустое значение

