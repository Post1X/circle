# Решение проблемы с подключением к БД

## Проблема
```
error: password authentication failed for user "circlemafia_user"
```

## Причина
Несоответствие учетных данных между `.env` файлом и Docker контейнером PostgreSQL.

## Решение

### Вариант 1: Исправить .env файл (рекомендуется)

Убедитесь, что в `.env` файле указаны правильные учетные данные:

**Для обычного запуска (`npm run dev`):**
```env
DB_NAME=circle_mafia
DB_USER=postgres
DB_PASS=your_password_here
DB_HOST=localhost
DB_PORT=5432
```

**Для Windows (`npm run dev:windows`):**
```env
DB_NAME=circle_mafia
DB_USER=postgres
DB_PASS=your_password_here
DB_HOST=localhost
DB_PORT=5434
```

### Вариант 2: Пересоздать Docker volume

Если БД была создана с другими учетными данными, нужно пересоздать volume:

**Для обычного запуска:**
```bash
# Остановить контейнеры
docker-compose down

# Удалить volume с данными БД
docker volume rm circle_mafia_backend_postgres_data

# Запустить заново
docker-compose up -d db redis
```

**Для Windows:**
```bash
# Остановить контейнеры
docker-compose -f docker-compose.windows.yml down

# Удалить volume с данными БД
docker volume rm circle_mafia_backend_postgres_data_windows

# Запустить заново
docker-compose -f docker-compose.windows.yml up -d db redis
```

### Вариант 3: Использовать существующие учетные данные

Если БД уже существует с пользователем `circlemafia_user`, обновите `.env`:

```env
DB_USER=circlemafia_user
DB_PASS=your_existing_password
```

## Проверка подключения

После исправления `.env` файла:

1. **Остановите приложение** (Ctrl+C)

2. **Перезапустите Docker контейнеры:**
   ```bash
   # Для обычного запуска
   docker-compose restart db
   
   # Для Windows
   docker-compose -f docker-compose.windows.yml restart db
   ```

3. **Проверьте подключение:**
   ```bash
   # Для обычного запуска
   docker-compose exec db psql -U postgres -d circle_mafia
   
   # Для Windows
   docker-compose -f docker-compose.windows.yml exec db psql -U postgres -d circle_mafia
   ```

4. **Запустите приложение:**
   ```bash
   npm run start:dev
   ```

## Важные замечания

1. **DB_HOST:**
   - Если запускаете через Docker (`docker-compose up`), используйте `DB_HOST=db` или `DB_HOST=localhost`
   - Если запускаете NestJS локально, а Docker отдельно, используйте `DB_HOST=localhost`

2. **DB_PORT:**
   - Для обычного запуска: `DB_PORT=5432`
   - Для Windows (если 5432 занят): `DB_PORT=5434`

3. **Пароль:**
   - Убедитесь, что пароль в `.env` совпадает с тем, что используется в Docker
   - Пароль не должен содержать специальные символы, которые могут вызвать проблемы (или экранируйте их)

