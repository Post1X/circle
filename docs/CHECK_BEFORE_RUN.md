# Проверка перед запуском

## ✅ Что уже готово:

1. ✅ Все зависимости установлены (включая `fernet` для шифрования)
2. ✅ Все модули перенесены из Python в NestJS
3. ✅ Шифрование исправлено на Fernet (совместимо с Python)
4. ✅ Инициализация горячего кошелька добавлена
5. ✅ Все сервисы подключены в AppModule

## ⚠️ Что нужно проверить перед запуском:

### 1. Файл `.env` существует и заполнен

Проверьте наличие файла `.env` в корне проекта со следующими переменными:

```env
# База данных
DB_NAME=circle_mafia
DB_USER=postgres
DB_PASS=your_password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# JWT
SECRET_KEY=your_secret_key_min_32_chars
ALGORITHM=HS256

# Tron
MNEMONIC=word1 word2 ... word12
TRON_API_KEY=your_tron_api_key
ENCRYPTION_KEY=your_fernet_key_base64

# Режим
MODE=test
```

**Для Windows (если порт 5432 занят):**
```env
DB_PORT=5434
REDIS_PORT=6381
```

### 2. База данных и Redis запущены

**Обычный запуск:**
```bash
npm run docker:up
```

**Для Windows:**
```bash
npm run docker:up:windows
```

Проверьте статус:
```bash
docker-compose ps
```

### 3. Миграции применены

Если БД новая, примените миграции:
```bash
docker-compose up alembic
```

### 4. Запуск приложения

**Обычный запуск:**
```bash
npm run dev
```

**Для Windows:**
```bash
npm run dev:windows
```

## 🔍 Проверка работы:

1. **Health check:**
   ```bash
   curl http://localhost:8000/api/health
   ```

2. **Проверка логов:**
   - Приложение должно запуститься без ошибок
   - Должно быть сообщение о инициализации горячего кошелька (или что он уже существует)
   - TronMonitorService и WithdrawalProcessorService должны запуститься

3. **Возможные проблемы:**

   - **Ошибка подключения к БД:**
     - Проверьте, что Docker контейнеры запущены
     - Проверьте порты в `.env`
     - Проверьте логи: `npm run docker:logs`

   - **Ошибка шифрования:**
     - Убедитесь, что `ENCRYPTION_KEY` в формате base64 (32 байта)
     - Сгенерируйте новый ключ: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`

   - **Ошибка TronWeb:**
     - Убедитесь, что `MNEMONIC` заполнен
     - Проверьте интернет-соединение (нужен доступ к TronGrid API)

## 📝 Примечания:

- Если горячий кошелек не создан, приложение все равно запустится, но выводы будут отключены
- TronMonitorService и WithdrawalProcessorService запускаются автоматически при старте
- Все сервисы используют OnModuleInit для инициализации

