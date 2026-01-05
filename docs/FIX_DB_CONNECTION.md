# Исправление подключения к БД

## Проблема
Пароль не совпадает или неправильный порт в `.env` файле.

## Решение

### 1. Пароль уже обновлен в БД ✅

### 2. Проверьте `.env` файл

Убедитесь, что в `.env` указаны **правильные значения**:

```env
DB_NAME=circlemafia
DB_USER=circlemafia_user
DB_PASS=kjhdsuiheuifbuwehfkisdh
DB_HOST=localhost
DB_PORT=5434
```

**ВАЖНО:** 
- Для Windows версии (`docker-compose.windows.yml`) используйте `DB_PORT=5434`
- Для обычной версии (`docker-compose.yml`) используйте `DB_PORT=5432`

### 3. Перезапустите приложение

После обновления `.env` файла:

1. Остановите приложение (Ctrl+C)
2. Перезапустите:
   ```bash
   npm run start:dev
   ```

### 4. Если проблема сохраняется

Проверьте подключение вручную:

```bash
# Проверить подключение из контейнера
docker-compose -f docker-compose.windows.yml exec db psql -U circlemafia_user -d circlemafia -c "SELECT version();"

# Проверить переменные окружения в контейнере
docker-compose -f docker-compose.windows.yml exec db env | grep POSTGRES
```

### 5. Альтернативное решение: Пересоздать контейнер

Если ничего не помогает, пересоздайте контейнер с правильными переменными:

```bash
# Остановить и удалить контейнер
docker-compose -f docker-compose.windows.yml down

# Удалить volume (ОСТОРОЖНО: удалит все данные!)
docker volume rm circle_mafia_backend_postgres_data_windows

# Запустить заново
docker-compose -f docker-compose.windows.yml up -d db redis
```

После этого база данных будет создана с правильными учетными данными из `.env` файла.

