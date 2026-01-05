# Circle Mafia Backend - NestJS

Проект мигрирован с Python (FastAPI) на NestJS (TypeScript).

## Структура проекта

```
src/
├── config/           # Конфигурация приложения
├── database/         # Модуль базы данных
├── entities/         # TypeORM entities (модели БД)
├── modules/         # Модули приложения
│   ├── auth/        # Аутентификация
│   ├── users/       # Пользователи
│   ├── rooms/       # Игровые комнаты (Socket.IO)
│   ├── game/        # Игровая логика
│   ├── admin/       # Административные функции
│   ├── withdrawal/  # Вывод средств
│   ├── public/      # Публичные эндпоинты
│   ├── beta-game/   # Бета-игра
│   └── skills/      # Навыки игроков
├── services/         # Сервисы
│   ├── token/       # Управление токенами
│   └── player-counter/ # Счетчик игроков
└── main.ts          # Точка входа

```

## Установка

```bash
npm install
```

## Настройка

Создайте файл `.env` в корне проекта со следующими переменными:

```env
DB_NAME=your_db_name
DB_PASS=your_db_password
DB_HOST=localhost
DB_PORT=5432
DB_USER=your_db_user

MODE=test  # или prod

ALGORITHM=HS256
SECRET_KEY=your_secret_key

REDIS_HOST=localhost
REDIS_PORT=6379

MNEMONIC=your_mnemonic_phrase
TRON_API_KEY=your_tron_api_key
ENCRYPTION_KEY=your_encryption_key
```

## Запуск

```bash
# Разработка
npm run start:dev

# Продакшн
npm run build
npm run start:prod
```

## Миграции

Проект использует существующие миграции Alembic из Python версии. TypeORM настроен с `synchronize: false`, поэтому структура БД управляется через миграции Alembic.

## Основные изменения при миграции

1. **FastAPI → NestJS**: Весь REST API переписан на NestJS контроллеры
2. **SQLAlchemy → TypeORM**: Модели БД переписаны на TypeORM entities
3. **Python Socket.IO → NestJS WebSocket Gateway**: Socket.IO логика перенесена в NestJS Gateway
4. **Pydantic → class-validator**: Валидация DTO через class-validator
5. **Python async/await → TypeScript async/await**: Асинхронная логика сохранена

## Скрипты Python

Скрипты на Python (например, `generate_mnemonic.py`, `generate_all_secrets.py`) остались без изменений и могут использоваться как есть.

## Дальнейшая разработка

1. **Игровая логика**: Модуль `game` требует полной реализации игровой логики из Python версии
2. **Socket.IO события**: Gateway в `rooms.gateway.ts` требует полной реализации всех событий
3. **Tron мониторинг**: Сервис мониторинга транзакций Tron требует реализации
4. **Withdrawal сервис**: Полная реализация вывода средств

## Примечания

- Проект использует ту же базу данных PostgreSQL
- Redis используется для кеширования и управления токенами
- Socket.IO настроен для real-time коммуникации
- Статические файлы обслуживаются через `/static`


