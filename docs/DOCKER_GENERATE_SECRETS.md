# Генерация секретов через Docker

## Способ 1: Через docker-compose (рекомендуется)

Если Docker Compose уже настроен и образ собран:

```bash
# Генерация мнемонической фразы
docker-compose run --rm web python generate_mnemonic.py

# Генерация всех секретов
docker-compose run --rm web python generate_all_secrets.py
```

**Параметры:**
- `--rm` - автоматически удаляет контейнер после выполнения
- `web` - имя сервиса из docker-compose.yml
- Скрипт выполнится внутри контейнера с установленными зависимостями

## Способ 2: Через docker run

Если нужно собрать образ и запустить:

```bash
# Сначала соберите образ (если еще не собран)
docker build -t circle_mafia .

# Запустите скрипт генерации мнемонической фразы
docker run --rm -v "$(pwd):/app" circle_mafia python generate_mnemonic.py

# Или генерацию всех секретов
docker run --rm -v "$(pwd):/app" circle_mafia python generate_all_secrets.py
```

**Параметры:**
- `--rm` - удаляет контейнер после выполнения
- `-v "$(pwd):/app"` - монтирует текущую директорию в контейнер (чтобы увидеть результат)
- `circle_mafia` - имя образа

## Способ 3: Интерактивный режим

Если нужно запустить Python интерактивно:

```bash
# Через docker-compose
docker-compose run --rm web python

# Через docker run
docker run --rm -it -v "$(pwd):/app" circle_mafia python
```

Затем в Python:
```python
from hdwallet import HDWallet
from hdwallet.cryptocurrencies import Tron
hd = HDWallet(cryptocurrency=Tron)
hd.from_entropy()
print(hd.mnemonic())
```

## Способ 4: Одной командой (без сохранения скрипта)

```bash
# Генерация мнемонической фразы
docker-compose run --rm web python -c "from hdwallet import HDWallet; from hdwallet.cryptocurrencies import Tron; hd = HDWallet(cryptocurrency=Tron); hd.from_entropy(); print('MNEMONIC=' + hd.mnemonic())"

# Генерация ENCRYPTION_KEY
docker-compose run --rm web python -c "from cryptography.fernet import Fernet; print('ENCRYPTION_KEY=' + Fernet.generate_key().decode())"

# Генерация SECRET_KEY
docker-compose run --rm web python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
```

## Пример полного запуска

```bash
# 1. Перейдите в директорию проекта
cd /path/to/circle_mafia-main

# 2. Убедитесь, что Docker запущен
docker ps

# 3. Запустите генерацию (если образ уже собран)
docker-compose run --rm web python generate_mnemonic.py

# Или соберите образ сначала
docker-compose build web
docker-compose run --rm web python generate_mnemonic.py
```

## Вывод результата

Результат будет выведен в консоль. Пример:

```
============================================================
GENERATED MNEMONIC PHRASE
============================================================

MNEMONIC=abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about

============================================================
INSTRUCTIONS:
============================================================
1. Copy the MNEMONIC value above
2. Paste it into line 14 of your .env file
3. Save this phrase in a secure place!
4. NEVER share this phrase with anyone!
============================================================
```

## Сохранение результата в файл

```bash
# Сохранить только мнемоническую фразу
docker-compose run --rm web python generate_mnemonic.py > mnemonic_output.txt

# Сохранить все секреты
docker-compose run --rm web python generate_all_secrets.py > secrets_output.txt
```

## На удаленном сервере

Если вы работаете на удаленном сервере через SSH:

```bash
# 1. Подключитесь к серверу
ssh user@your-server.com

# 2. Перейдите в директорию проекта
cd /path/to/circle_mafia-main

# 3. Запустите генерацию
docker-compose run --rm web python generate_mnemonic.py

# 4. Скопируйте результат и вставьте в .env файл
```

## Устранение проблем

### Ошибка: "Cannot connect to the Docker daemon"
```bash
# Проверьте, запущен ли Docker
sudo systemctl status docker

# Запустите Docker (если не запущен)
sudo systemctl start docker
```

### Ошибка: "No such service: web"
```bash
# Убедитесь, что вы в правильной директории с docker-compose.yml
ls -la docker-compose.yml

# Проверьте имя сервиса в docker-compose.yml
cat docker-compose.yml | grep -A 5 "services:"
```

### Ошибка: "Module not found"
```bash
# Пересоберите образ с зависимостями
docker-compose build web
docker-compose run --rm web python generate_mnemonic.py
```

### Ошибка: "Permission denied"
```bash
# На Linux может потребоваться sudo
sudo docker-compose run --rm web python generate_mnemonic.py

# Или добавьте пользователя в группу docker
sudo usermod -aG docker $USER
# Затем перелогиньтесь
```

## Безопасность

⚠️ **ВАЖНО:**
- Результаты генерации содержат критические секреты
- Не сохраняйте результаты в публичные места
- Удалите временные файлы после использования:
  ```bash
  rm -f mnemonic_output.txt secrets_output.txt
  ```
- Убедитесь, что .env файл в .gitignore

