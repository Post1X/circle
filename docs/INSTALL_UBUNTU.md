# Установка на Ubuntu/Debian сервере

## Проблема: externally-managed-environment

Python 3.12+ в Ubuntu/Debian защищает системную установку от установки пакетов через pip. Это сделано для предотвращения конфликтов с системными пакетами.

## Решение 1: Использовать Docker (рекомендуется)

Этот проект настроен для работы через Docker Compose - это самый простой и надежный способ.

### Установка Docker и Docker Compose:

```bash
# Обновить пакеты
sudo apt update

# Установить Docker
sudo apt install -y docker.io docker-compose

# Запустить Docker
sudo systemctl start docker
sudo systemctl enable docker

# Добавить пользователя в группу docker (чтобы не использовать sudo)
sudo usermod -aG docker $USER
# Выйти и войти снова, чтобы изменения вступили в силу
```

### Запуск проекта:

```bash
# Перейти в директорию проекта
cd /opt/backend

# Убедиться, что .env файл заполнен
# Затем запустить
sudo docker-compose up -d

# Или без sudo, если пользователь в группе docker
docker-compose up -d
```

---

## Решение 2: Виртуальное окружение (если Docker не подходит)

### Установка необходимых пакетов:

```bash
# Установить python3-venv и python3-full
sudo apt install -y python3-venv python3-full python3-pip
```

### Создание и активация виртуального окружения:

```bash
# Перейти в директорию проекта
cd /opt/backend

# Создать виртуальное окружение
python3 -m venv venv

# Активировать виртуальное окружение
source venv/bin/activate

# Теперь pip будет работать внутри venv
pip install -r requirements.txt
```

### Запуск сервера:

```bash
# Убедиться, что виртуальное окружение активировано
source venv/bin/activate

# Запустить сервер
python main.py
```

### Автоматическая активация при входе (опционально):

Добавьте в `~/.bashrc`:
```bash
cd /opt/backend && source venv/bin/activate
```

---

## Решение 3: Использовать --break-system-packages (НЕ рекомендуется)

⚠️ **ВНИМАНИЕ:** Это может сломать системные пакеты Python!

```bash
pip install --break-system-packages -r requirements.txt
```

**Не используйте этот метод**, если не понимаете последствий!

---

## Рекомендация

**Используйте Docker Compose** - это:
- ✅ Изолированная среда
- ✅ Легко обновлять
- ✅ Не конфликтует с системными пакетами
- ✅ Включает все зависимости (БД, Redis)
- ✅ Уже настроено в проекте

---

## Дополнительные зависимости для Docker

Если Docker не установлен, установите:

```bash
# Установить зависимости для сборки Docker образов
sudo apt install -y \
    build-essential \
    cmake \
    python3-dev \
    pkg-config \
    git
```

---

## Проверка установки

После установки через Docker:

```bash
# Проверить статус контейнеров
docker-compose ps

# Проверить логи
docker-compose logs -f web

# Проверить health endpoint
curl http://localhost:8000/api/health
```

---

## Если нужно установить зависимости локально

Если все же нужно установить без Docker:

```bash
# 1. Установить системные зависимости
sudo apt install -y \
    python3.13 \
    python3.13-venv \
    python3.13-dev \
    postgresql-client \
    libpq-dev \
    redis-server \
    build-essential \
    cmake \
    pkg-config

# 2. Создать venv
python3.13 -m venv venv
source venv/bin/activate

# 3. Обновить pip
pip install --upgrade pip

# 4. Установить зависимости
pip install -r requirements.txt

# 5. Настроить .env для локальных БД
# DB_HOST=localhost
# REDIS_HOST=localhost

# 6. Запустить миграции
alembic upgrade head

# 7. Запустить сервер
python main.py
```

Но помните: **Docker проще и надежнее!**



