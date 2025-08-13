# HTTP-Only Cookies в API Gateway

## Обзор

API Gateway теперь поддерживает HTTP-Only cookies для аутентификации, аналогично auth сервису. Это обеспечивает дополнительный уровень безопасности и удобства для клиентов.

## Функциональность

### Поддерживаемые эндпоинты

Следующие эндпоинты теперь устанавливают HTTP-Only cookies:

- **`POST /v1/client/sign-up`** - Регистрация пользователя
- **`POST /v1/client/sign-in/password`** - Вход пользователя
- **`POST /v1/client/refresh_token`** - Обновление токена
- **`POST /v1/client/logout`** - Выход пользователя (очищает cookies)

### Поддерживаемые эндпоинты с cookies

Все защищенные эндпоинты теперь могут получать токен как из заголовка `Authorization`, так и из cookies:

- **`GET /v1/client/me`** - Получение профиля пользователя
- **`PATCH /v1/client/switch-org`** - Переключение организации
- **`POST /v1/org`** - Создание организации
- **`POST /v1/org/{id}/invite`** - Приглашение пользователя
- **`POST /v1/invite/accept`** - Принятие приглашения
- **`GET /v1/org/{id}/members`** - Список участников
- **`DELETE /v1/org/{id}/member/{user_id}`** - Удаление участника
- **`PATCH /v1/org/{id}/member/{user_id}/role`** - Обновление роли участника
- И все internal эндпоинты

## Настройка Cookies

### Access Token Cookie

```python
response.set_cookie(
    key="access_token",
    value=access_token,
    max_age=expires_in,  # Время жизни токена (обычно 300 секунд)
    httponly=True,       # HTTP-Only для безопасности
    secure=False,        # False для разработки (HTTP), True для продакшена (HTTPS)
    samesite="lax",      # lax для разработки, strict для продакшена
    path="/"             # Доступен для всех путей
)
```

### Refresh Token Cookie

```python
response.set_cookie(
    key="refresh_token", 
    value=refresh_token,
    max_age=7 * 24 * 60 * 60,  # 7 дней в секундах
    httponly=True,              # HTTP-Only для безопасности
    secure=False,               # False для разработки (HTTP), True для продакшена (HTTPS)
    samesite="lax",             # lax для разработки, strict для продакшена
    path="/v1/client/refresh_token"  # Доступен только для refresh endpoint
)
```

## Приоритет аутентификации

API Gateway использует следующий приоритет для получения токена:

1. **Заголовок Authorization** - `Bearer <token>`
2. **Cookie access_token** - HTTP-Only cookie

Если токен найден в заголовке, он используется. Если нет - проверяется cookie.

## Примеры использования

### Регистрация с получением cookies

```bash
curl -X POST "http://localhost:8002/v1/client/sign-up" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}' \
  -c cookies.txt
```

### Вход с получением cookies

```bash
curl -X POST "http://localhost:8002/v1/client/sign-in/password" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}' \
  -c cookies.txt
```

### Запрос с cookies (без заголовка Authorization)

```bash
curl -X GET "http://localhost:8002/v1/client/me" \
  -b cookies.txt
```

### Запрос с заголовком Authorization (приоритет)

```bash
curl -X GET "http://localhost:8002/v1/client/me" \
  -H "Authorization: Bearer <token>"
```

### Обновление токена с cookies

```bash
curl -X POST "http://localhost:8002/v1/client/refresh_token" \
  -b cookies.txt \
  -c cookies.txt
```

### Выход с очисткой cookies

```bash
curl -X POST "http://localhost:8002/v1/client/logout" \
  -b cookies.txt
```

## Безопасность

### HTTP-Only Cookies

- Cookies помечены как `httponly=True`, что предотвращает доступ к ним через JavaScript
- Это защищает от XSS атак

### SameSite

- Установлено значение `lax` для разработки
- Для продакшена рекомендуется `strict`

### Secure Flag

- Установлено `False` для разработки (HTTP)
- Для продакшена (HTTPS) должно быть `True`

### Path Restrictions

- `access_token` доступен для всех путей (`/`)
- `refresh_token` доступен только для `/v1/client/refresh_token`

## Тестирование

Для тестирования cookies используйте файл `test_cookies.py`:

```bash
python test_cookies.py
```

Тест проверяет:
- Установку cookies при регистрации/входе
- Использование cookies для аутентификации
- Обновление токенов через cookies
- Очистку cookies при выходе
- Смешанную аутентификацию (заголовок + cookies)

## Конфигурация для продакшена

Для продакшена измените настройки в `utils/cookie_utils.py`:

```python
# В функции set_auth_cookies
secure=True,      # True для HTTPS
samesite="strict" # strict для максимальной безопасности
```

## Совместимость

API Gateway полностью совместим с существующими клиентами:
- Клиенты могут продолжать использовать заголовок `Authorization`
- Новые клиенты могут использовать cookies
- Поддерживается смешанная аутентификация

## Файлы

- `utils/cookie_utils.py` - Утилиты для работы с cookies
- `routers/auth.py` - Обновленные эндпоинты с поддержкой cookies
- `test_cookies.py` - Тесты для проверки работы cookies
