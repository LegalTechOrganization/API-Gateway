# API Gateway

API Gateway сервис для проксирования запросов к микросервисам с интеграцией Kafka для событий.

## Архитектура

- **FastAPI** - основной веб-фреймворк
- **PostgreSQL** - база данных
- **Kafka** - брокер сообщений для событий
- **Docker Compose** - оркестрация сервисов

## Запуск

### Предварительные требования

1. **Docker и Docker Compose** - должны быть установлены
2. **Python 3.11** (для локального запуска)

### Способ 1: Docker Compose (Рекомендуется)

```bash
# Клонирование репозитория
git clone <repository-url>
cd API-Gateway

# Запуск всех сервисов
docker-compose up --build

# Или в фоновом режиме
docker-compose up -d --build
```

### Способ 2: Локальный запуск

```bash
# Создание виртуального окружения
python -m venv venv

# Активация (Windows)
venv\Scripts\activate
# Активация (Linux/Mac)
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Настройка переменных окружения
export DATABASE_URL="postgresql+asyncpg://user:password@localhost:5455/gateway_db"
export AUTH_SERVICE_URL="http://localhost:8001"
export KAFKA_BOOTSTRAP_SERVERS="localhost:9092"

# Запуск приложения
uvicorn main:app --host 0.0.0.0 --port 8002 --reload
```

## Доступные сервисы

После запуска будут доступны:

- **API Gateway**: http://localhost:8002
- **Документация API**: http://localhost:8002/docs
- **PostgreSQL**: localhost:5455
- **Kafka**: localhost:9092
- **Zookeeper**: localhost:2181

## API Endpoints

### Auth Endpoints (проксирование к auth-service)

#### Публичные эндпоинты
- `POST /v1/client/sign-up` - Регистрация пользователя
- `POST /v1/client/sign-in/password` - Вход пользователя
- `POST /v1/client/refresh_token` - Обновление токена
- `POST /v1/client/logout` - Выход пользователя

#### Защищенные эндпоинты (требуют Bearer токен)
- `GET /v1/client/me` - Информация о текущем пользователе
- `PATCH /v1/client/switch-org` - Переключение активной организации

#### Organization эндпоинты
- `POST /v1/org` - Создание организации
- `GET /v1/org/{id}/members` - Список участников организации
- `POST /v1/org/{id}/invite` - Приглашение пользователя
- `POST /v1/invite/accept` - Принятие приглашения
- `DELETE /v1/org/{id}/member/{user_id}` - Удаление участника
- `PATCH /v1/org/{id}/member/{user_id}/role` - Обновление роли участника

#### Internal эндпоинты (для внутренних сервисов)
- `GET /auth/validate` - Валидация JWT токена
- `GET /auth/user/{id}` - Информация о пользователе
- `GET /auth/user/{id}/orgs` - Организации пользователя
- `GET /auth/org/{id}` - Информация об организации
- `GET /auth/org/{id}/members` - Участники организации

## Kafka Topics

Сервис отправляет события в следующие топики:

- **auth-events** - события аутентификации
  - `user_registered` - регистрация пользователя
  - `user_logged_in` - вход пользователя
  - `user_logged_out` - выход пользователя
  - `token_refreshed` - обновление токена
  - `token_validated` - валидация токена

- **user-events** - события пользователей
  - `user_info_requested` - запрос информации о пользователе
  - `organization_switched` - переключение организации
  - `user_detail_requested` - запрос детальной информации
  - `user_orgs_requested` - запрос организаций пользователя

- **organization-events** - события организаций
  - `organization_created` - создание организации
  - `user_invited` - приглашение пользователя
  - `invite_accepted` - принятие приглашения
  - `members_listed` - просмотр списка участников
  - `member_removed` - удаление участника
  - `member_role_updated` - обновление роли участника

## Переменные окружения

| Переменная | Описание | Значение по умолчанию |
|------------|----------|----------------------|
| `DATABASE_URL` | Строка подключения к PostgreSQL | `postgresql+asyncpg://user:password@db:5432/gateway_db` |
| `AUTH_SERVICE_URL` | URL auth-service | `http://auth-service:8001` |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka серверы | `kafka:29092` |
| `INTERNAL_SERVICE_KEY` | Секретный ключ для внутренних сервисов | `gateway-secret-key-2024` |

## Разработка

### Структура проекта

```
API-Gateway/
├── alembic/              # Миграции базы данных
├── models/               # Модели данных
├── routers/              # API роутеры
│   ├── auth.py          # Auth эндпоинты
│   ├── billing.py       # Billing эндпоинты
│   ├── chat.py          # Chat эндпоинты
│   ├── tpl.py           # Template эндпоинты
│   └── user.py          # User эндпоинты
├── services/             # Бизнес-логика
│   ├── auth_client.py   # Клиент для auth-service
│   ├── kafka_service.py # Сервис для работы с Kafka
│   └── microservice_client.py
├── main.py              # Точка входа приложения
├── db.py                # Конфигурация базы данных
├── docker-compose.yml   # Docker Compose конфигурация
├── Dockerfile           # Docker образ
└── requirements.txt     # Python зависимости
```

### Добавление нового микросервиса

1. Создайте клиент в `services/`
2. Добавьте роутер в `routers/`
3. Подключите роутер в `main.py`
4. Добавьте сервис в `docker-compose.yml`

### Логирование

Все события отправляются в Kafka для дальнейшей обработки и аналитики.

## Устранение неполадок

### Проблемы с Docker

```bash
# Остановка всех контейнеров
docker-compose down

# Удаление томов
docker-compose down -v

# Пересборка образов
docker-compose build --no-cache
```

### Проблемы с Kafka

```bash
# Проверка статуса Kafka
docker-compose ps kafka

# Просмотр логов Kafka
docker-compose logs kafka
```

### Проблемы с базой данных

```bash
# Подключение к PostgreSQL
docker-compose exec db psql -U user -d gateway_db

# Применение миграций
alembic upgrade head
```

## Лицензия

MIT License

