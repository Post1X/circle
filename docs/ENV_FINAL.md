# Финальный .env файл для NestJS версии

## Создание .env файла

Скопируйте `.env.example` в `.env`:

```bash
cp .env.example .env
```

## Полный пример .env файла

```env
# ============================================
# База данных PostgreSQL
# ============================================
DB_NAME=circle_mafia
DB_USER=postgres
DB_PASS=your_secure_password_here
DB_HOST=db
DB_PORT=5432

# ============================================
# Redis
# ============================================
REDIS_HOST=redis
REDIS_PORT=6379

# ============================================
# JWT Аутентификация
# ============================================
SECRET_KEY=your-very-long-and-secure-secret-key-minimum-32-characters-long
ALGORITHM=HS256

# ============================================
# Режим работы
# ============================================
MODE=test

# ============================================
# Tron Blockchain
# ============================================
MNEMONIC=word1 word2 word3 word4 word5 word6 word7 word8 word9 word10 word11 word12
TRON_API_KEY=your-trongrid-api-key-here
ENCRYPTION_KEY=your-fernet-encryption-key-base64-encoded-32-bytes
```

## Генерация секретных ключей

### SECRET_KEY

```bash
# Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('base64'))"
```

### ENCRYPTION_KEY

```bash
# Python
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### MNEMONIC

```bash
# Используйте скрипт из проекта
python generate_mnemonic.py
```

## Настройки для разных окружений

### Docker (рекомендуется)

```env
DB_HOST=db
REDIS_HOST=redis
```

### Локальная разработка (без Docker)

```env
DB_HOST=localhost
REDIS_HOST=localhost
```

### Продакшен

```env
MODE=prod
DB_HOST=your-production-db-host
REDIS_HOST=your-production-redis-host
DB_SSL=true
```

## Проверка переменных

После создания `.env` файла проверьте, что все переменные заполнены:

```bash
# Python скрипт для проверки
python validate_env.py
```

## Безопасность

⚠️ **ВАЖНО:**

1. Никогда не коммитьте `.env` в Git (уже в `.gitignore`)
2. Используйте уникальные ключи для каждого окружения
3. В продакшене используйте секреты из безопасного хранилища
4. `MNEMONIC` - это корневой ключ, храните в секрете!


