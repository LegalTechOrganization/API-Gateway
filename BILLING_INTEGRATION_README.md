# Billing Service Integration

## Обзор

API Gateway интегрирован с Billing Tarrification сервисом для обработки операций с балансом пользователей. Все запросы к billing сервису автоматически включают токен пользователя в заголовке `X-User-Data`.

## Конфигурация

### URL сервиса
Billing сервис доступен по адресу: `http://host.docker.internal:8001`

### Заголовок аутентификации
Все запросы к billing сервису включают заголовок `X-User-Data` в формате:
```json
{"jwt_token":"<access_token>"}
```

## Endpoints

### 1. Проверка баланса
**POST** `/billing/quota/check`

Проверяет, достаточно ли средств для выполнения операции.

**Запрос:**
```json
{
    "units": 10.0
}
```

**Ответ:**
```json
{
    "allowed": true,
    "balance": 100.0
}
```

### 2. Получение баланса
**POST** `/billing/balance`

Возвращает текущий баланс пользователя и информацию о плане.

**Запрос:** Без тела запроса

**Ответ:**
```json
{
    "balance": 100.0,
    "plan": {
        "plan_code": "basic",
        "status": "active",
        "expires_at": "2024-01-15T00:00:00Z"
    }
}
```

### 3. Списание средств
**POST** `/billing/quota/debit`

Списывает средства с баланса пользователя.

**Запрос:**
```json
{
    "units": 5.0,
    "reason": "Использование API",
    "ref": "optional-reference-id"
}
```

**Ответ:**
```json
{
    "balance": 95.0,
    "tx_id": "transaction-id-123"
}
```

### 4. Пополнение баланса
**POST** `/billing/quota/credit`

Пополняет баланс пользователя.

**Запрос:**
```json
{
    "units": 20.0,
    "reason": "Пополнение счета",
    "source_service": "gateway",
    "ref": "optional-reference-id"
}
```

**Ответ:**
```json
{
    "balance": 115.0,
    "tx_id": "transaction-id-456"
}
```

### 5. Применение плана
**POST** `/billing/plan/apply`

Применяет тарифный план к пользователю.

**Запрос:**
```json
{
    "plan_code": "premium",
    "auto_renew": true,
    "ref": "optional-reference-id"
}
```

**Ответ:**
```json
{
    "plan_id": "plan-123",
    "new_balance": 100.0
}
```

## Аутентификация

Все endpoints требуют аутентификации. Токен может быть передан:

1. **В заголовке Authorization:**
   ```
   Authorization: Bearer <access_token>
   ```

2. **В HTTP-Only cookie:**
   ```
   access_token=<access_token>
   ```

## Логирование

API Gateway логирует все запросы к billing сервису, включая:
- URL запроса
- Метод HTTP
- Данные запроса
- Заголовки (включая X-User-Data)
- Статус ответа
- Тело ответа

## Обработка ошибок

При ошибках billing сервиса API Gateway возвращает соответствующий HTTP статус код и детали ошибки.

### Примеры ошибок:
- `401 Unauthorized` - Неверный токен
- `403 Forbidden` - Недостаточно средств
- `404 Not Found` - План не найден
- `500 Internal Server Error` - Ошибка сервиса

## Тестирование

Для тестирования интеграции используйте файл `test_billing_integration.py`:

```bash
python test_billing_integration.py
```

Тест проверяет:
- Формат токена в заголовке X-User-Data
- Работу всех billing endpoints
- Обработку ошибок

## Примеры использования

### cURL
```bash
# Проверка баланса
curl -X POST "http://localhost:8000/billing/quota/check" \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{"units": 10.0}'

# Получение баланса
curl -X POST "http://localhost:8000/billing/balance" \
  -H "Authorization: Bearer <your-token>"
```

### Python
```python
import httpx

async def check_balance(token: str, units: float):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/billing/quota/check",
            headers={"Authorization": f"Bearer {token}"},
            json={"units": units}
        )
        return response.json()
```

## Безопасность

- Все токены передаются в заголовке `X-User-Data` в зашифрованном виде
- Используется HTTP-Only cookies для дополнительной безопасности
- Все запросы логируются для аудита
- Валидация входных данных на уровне API Gateway



