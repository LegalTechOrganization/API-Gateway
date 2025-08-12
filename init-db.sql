-- Инициализация базы данных API Gateway
-- Этот файл выполняется при первом запуске PostgreSQL контейнера

-- Создание базы данных (если не существует)
-- CREATE DATABASE gateway_db;

-- Подключение к базе данных
\c gateway_db;

-- Создание расширений (если нужны)
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Создание схем (если нужны)
-- CREATE SCHEMA IF NOT EXISTS public;

-- Установка прав доступа
GRANT ALL PRIVILEGES ON DATABASE gateway_db TO user;
GRANT ALL PRIVILEGES ON SCHEMA public TO user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO user;

-- Установка прав на будущие объекты
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO user;

-- Вывод информации о созданной базе
SELECT 'Database gateway_db initialized successfully' as status;


