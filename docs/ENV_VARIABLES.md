# Переменные окружения (.env)

Данный документ описывает все переменные окружения, используемые в проекте, их назначение и способы заполнения.

## Обязательные переменные

### База данных PostgreSQL

| Переменная | Описание | Где используется | Как заполнить |
|------------|----------|------------------|---------------|
| `DB_NAME` | Имя базы данных | `servises/config.py`, `docker-compose.yml` | Имя вашей PostgreSQL базы данных (например: `circle_mafia`) |
| `DB_USER` | Пользователь базы данных | `servises/config.py`, `docker-compose.yml` | Имя пользователя PostgreSQL (например: `postgres`) |
| `DB_PASS` | Пароль базы данных | `servises/config.py`, `docker-compose.yml` | Пароль пользователя PostgreSQL |
| `DB_HOST` | Хост базы данных | `servises/config.py`, `docker-compose.yml` | Адрес хоста (для Docker: `db`, для локальной разработки: `localhost`) |
| `DB_PORT` | Порт базы данных | `servises/config.py`, `docker-compose.yml` | Порт PostgreSQL (обычно `5432`) |

**Пример:**
```env
DB_NAME=circle_mafia
DB_USER=postgres
DB_PASS=your_secure_password
DB_HOST=db
DB_PORT=5432
```

### Redis

| Переменная | Описание | Где используется | Как заполнить |
|------------|----------|------------------|---------------|
| `REDIS_HOST` | Хост Redis | `servises/config.py`, `celery_config.py`, `main.py`, `servises/auth/token_service.py`, `servises/player_counter.py` | Адрес хоста Redis (для Docker: `redis`, для локальной разработки: `localhost`) |
| `REDIS_PORT` | Порт Redis | `servises/config.py`, `celery_config.py`, `main.py`, `servises/auth/token_service.py`, `servises/player_counter.py` | Порт Redis (обычно `6379`) |

**Пример:**
```env
REDIS_HOST=redis
REDIS_PORT=6379
```

### JWT аутентификация

| Переменная | Описание | Где используется | Как заполнить |
|------------|----------|------------------|---------------|
| `SECRET_KEY` | Секретный ключ для подписи JWT токенов | `servises/auth/auth.py`, `servises/auth/dependencies.py` | Случайная строка (минимум 32 символа). **ВАЖНО:** Используйте криптографически стойкий ключ! |
| `ALGORITHM` | Алгоритм шифрования JWT | `servises/auth/auth.py`, `servises/auth/dependencies.py` | Обычно `HS256` |

**Пример:**
```env
SECRET_KEY=your-very-long-and-secure-secret-key-minimum-32-characters-long
ALGORITHM=HS256
```

**Как сгенерировать SECRET_KEY:**
```python
# В Python:
import secrets
print(secrets.token_urlsafe(32))

# Или в терминале:
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Tron Blockchain

| Переменная | Описание | Где используется | Как заполнить |
|------------|----------|------------------|---------------|
| `mnemonic` | Мнемоническая фраза (seed phrase) для генерации кошельков | `servises/hot_wallet_init.py`, `servises/withdrawal_service.py`, `bd/actions/balance.py` | 12 или 24 слова BIP39 мнемонической фразы. **КРИТИЧЕСКИ ВАЖНО:** Храните в секрете! |
| `tron_api_key` | API ключ для TronGrid API | `servises/tron_monitor.py`, `servises/withdrawal_service.py` | Получите на https://www.trongrid.io/ (бесплатный план доступен) |
| `ENCRYPTION_KEY` | Ключ для шифрования приватных ключей кошельков | `servises/hot_wallet_init.py`, `servises/withdrawal_service.py` | Ключ Fernet (32 байта в base64). **ВАЖНО:** Используйте уникальный ключ! |

**Пример:**
```env
mnemonic=word1 word2 word3 ... word12
tron_api_key=your-trongrid-api-key-here
ENCRYPTION_KEY=your-fernet-encryption-key-here
```

**Как сгенерировать ENCRYPTION_KEY:**
```python
# В Python:
from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(key.decode())  # Это и есть ваш ENCRYPTION_KEY

# Или в терминале:
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**Как получить tron_api_key:**
1. Зарегистрируйтесь на https://www.trongrid.io/
2. Перейдите в раздел API Keys
3. Создайте новый API ключ
4. Скопируйте ключ в переменную окружения

**Как создать mnemonic:**
```python
# В Python (для тестирования):
from hdwallet import HDWallet
from hdwallet.cryptocurrencies import Tron
from hdwallet.mnemonics import BIP39Mnemonic

hdwallet = HDWallet(cryptocurrency=Tron)
hdwallet.from_entropy()
mnemonic = hdwallet.mnemonic()
print(mnemonic)
```

⚠️ **ВНИМАНИЕ:** Для продакшена используйте безопасно сгенерированную мнемоническую фразу и храните её в секрете!

### Режим работы

| Переменная | Описание | Где используется | Как заполнить |
|------------|----------|------------------|---------------|
| `mode` | Режим работы приложения | `servises/config.py`, `main.py` | `test` или `prod` (по умолчанию `prod`). В режиме `test` включен автоперезапуск при изменении кода |

**Пример:**
```env
mode=prod
# или
mode=test
```

## Полный пример .env файла

```env
# База данных PostgreSQL
DB_NAME=circle_mafia
DB_USER=postgres
DB_PASS=your_secure_password_here
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# JWT аутентификация
SECRET_KEY=your-very-long-and-secure-secret-key-minimum-32-characters-long-change-this-in-production
ALGORITHM=HS256

# Tron Blockchain
mnemonic=word1 word2 word3 word4 word5 word6 word7 word8 word9 word10 word11 word12
tron_api_key=your-trongrid-api-key-here
ENCRYPTION_KEY=your-fernet-encryption-key-base64-encoded-32-bytes

# Режим работы
mode=prod
```

## Где используются переменные

### База данных (PostgreSQL)
- `bd/database.py` - создание подключения к БД
- `migrations/env.py` - выполнение миграций
- `reboot_bd.py` - перезапуск БД

### Redis
- `celery_config.py` - конфигурация Celery (брокер и бэкенд)
- `main.py` - инициализация кеша FastAPI
- `servises/auth/token_service.py` - черный список токенов
- `servises/player_counter.py` - счетчик игроков

### JWT
- `servises/auth/auth.py` - создание токенов
- `servises/auth/dependencies.py` - проверка токенов

### Tron
- `servises/tron_monitor.py` - мониторинг депозитов
- `servises/withdrawal_service.py` - обработка выводов
- `servises/hot_wallet_init.py` - инициализация горячего кошелька
- `bd/actions/balance.py` - генерация адресов для депозитов

## Безопасность

⚠️ **КРИТИЧЕСКИ ВАЖНО:**

1. **Никогда не коммитьте .env файл в Git!** Убедитесь, что `.env` добавлен в `.gitignore`
2. **SECRET_KEY** - должен быть уникальным и случайным для каждого окружения
3. **ENCRYPTION_KEY** - должен быть уникальным и случайным
4. **mnemonic** - это ваш корневой ключ для всех кошельков. Потеря = потеря всех средств!
5. **DB_PASS** - используйте сильные пароли
6. В продакшене используйте секреты из безопасного хранилища (например, Docker secrets, Kubernetes secrets, AWS Secrets Manager)

## Проверка заполнения

После заполнения всех переменных, убедитесь что:
1. Все переменные заполнены (нет пустых значений)
2. `SECRET_KEY` и `ENCRYPTION_KEY` сгенерированы безопасным способом
3. `mnemonic` валидна (12 или 24 слова)
4. `tron_api_key` действителен (можно проверить через API)
5. Подключения к БД и Redis работают








