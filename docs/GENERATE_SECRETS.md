# Как получить значения для строк 14-17 в .env.example

## Строка 14: MNEMONIC (Мнемоническая фраза)

**Что это:** Мнемоническая фраза BIP39 для генерации Tron кошельков. Это корневой ключ для всех кошельков в системе.

**Как сгенерировать:**

### Вариант 1: Через Python (рекомендуется)

```python
from hdwallet import HDWallet
from hdwallet.cryptocurrencies import Tron

hdwallet = HDWallet(cryptocurrency=Tron)
hdwallet.from_entropy()  # Генерирует случайную мнемоническую фразу
mnemonic = hdwallet.mnemonic()
print(mnemonic)
```

**Команда для терминала:**
```bash
python -c "from hdwallet import HDWallet; from hdwallet.cryptocurrencies import Tron; hd = HDWallet(cryptocurrency=Tron); hd.from_entropy(); print(hd.mnemonic())"
```

### Вариант 2: Онлайн генератор (только для тестирования!)

⚠️ **ВНИМАНИЕ:** Для продакшена НЕ используйте онлайн генераторы! Используйте только локальную генерацию.

Можно использовать: https://iancoleman.io/bip39/ (выберите Tron в настройках)

### Вариант 3: Через готовый скрипт

Создайте файл `generate_mnemonic.py`:
```python
from hdwallet import HDWallet
from hdwallet.cryptocurrencies import Tron

hdwallet = HDWallet(cryptocurrency=Tron)
hdwallet.from_entropy()
print(f"MNEMONIC={hdwallet.mnemonic()}")
```

Запустите: `python generate_mnemonic.py`

**Пример результата:**
```
MNEMONIC=abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about
```

⚠️ **КРИТИЧЕСКИ ВАЖНО:**
- Мнемоническая фраза - это доступ ко ВСЕМ кошелькам системы
- Храните её в абсолютном секрете
- Никогда не коммитьте в Git
- Сделайте резервную копию в безопасном месте
- Потеря мнемонической фразы = потеря всех средств!

---

## Строка 15: TRON_API_KEY (API ключ TronGrid)

**Что это:** API ключ для доступа к TronGrid API (мониторинг транзакций, проверка балансов).

**Как получить:**

1. **Зарегистрируйтесь на TronGrid:**
   - Перейдите на https://www.trongrid.io/
   - Нажмите "Sign Up" или "Login"

2. **Создайте API ключ:**
   - После входа перейдите в раздел "API Keys" или "Dashboard"
   - Нажмите "Create API Key" или "Generate API Key"
   - Скопируйте сгенерированный ключ

3. **Вставьте в .env:**
   ```
   TRON_API_KEY=ваш-ключ-здесь
   ```

**Бесплатный план:**
- TronGrid предоставляет бесплатный план с ограничениями
- Для продакшена может потребоваться платный план при больших нагрузках

**Пример:**
```
TRON_API_KEY=12345678-abcd-1234-abcd-123456789abc
```

---

## Строка 17: ENCRYPTION_KEY (Ключ шифрования)

**Что это:** Ключ Fernet для шифрования приватных ключей кошельков в базе данных.

**Как сгенерировать:**

### Вариант 1: Через Python (рекомендуется)

```python
from cryptography.fernet import Fernet

key = Fernet.generate_key()
print(key.decode())  # Это ваш ENCRYPTION_KEY
```

**Команда для терминала:**
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Вариант 2: Через готовый скрипт

Создайте файл `generate_encryption_key.py`:
```python
from cryptography.fernet import Fernet

key = Fernet.generate_key()
print(f"ENCRYPTION_KEY={key.decode()}")
```

Запустите: `python generate_encryption_key.py`

**Пример результата:**
```
ENCRYPTION_KEY=abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ=
```

**Формат:**
- Base64-encoded строка
- Длина: 44 символа
- Содержит символы: A-Z, a-z, 0-9, +, /, =

⚠️ **ВАЖНО:**
- Ключ должен быть уникальным для каждого окружения
- Не используйте один и тот же ключ в разных проектах
- Храните в секрете
- Без этого ключа нельзя расшифровать приватные ключи из БД

---

## Быстрая генерация всех значений

Создайте файл `generate_all_secrets.py`:

```python
#!/usr/bin/env python3
"""
Скрипт для генерации всех секретных значений для .env файла
"""

from cryptography.fernet import Fernet
from hdwallet import HDWallet
from hdwallet.cryptocurrencies import Tron
import secrets

print("=" * 60)
print("ГЕНЕРАЦИЯ СЕКРЕТНЫХ ЗНАЧЕНИЙ ДЛЯ .ENV")
print("=" * 60)
print()

# 1. ENCRYPTION_KEY
encryption_key = Fernet.generate_key().decode()
print(f"ENCRYPTION_KEY={encryption_key}")
print()

# 2. SECRET_KEY (для JWT)
secret_key = secrets.token_urlsafe(32)
print(f"SECRET_KEY={secret_key}")
print()

# 3. MNEMONIC
hdwallet = HDWallet(cryptocurrency=Tron)
hdwallet.from_entropy()
mnemonic = hdwallet.mnemonic()
print(f"MNEMONIC={mnemonic}")
print()

print("=" * 60)
print("ВАЖНО:")
print("1. Сохраните эти значения в безопасном месте")
print("2. Вставьте их в ваш .env файл")
print("3. НИКОГДА не коммитьте .env в Git!")
print("4. Для TRON_API_KEY получите ключ на https://www.trongrid.io/")
print("=" * 60)
```

Запустите:
```bash
python generate_all_secrets.py
```

---

## Итоговый пример заполнения строк 14-17:

```env
# Строка 14
MNEMONIC=abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about

# Строка 15
TRON_API_KEY=your-api-key-from-trongrid-io

# Строка 16 (пустая)

# Строка 17
ENCRYPTION_KEY=abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ=
```

---

## Проверка после заполнения

После заполнения всех значений убедитесь:

1. ✅ `MNEMONIC` содержит 12 или 24 слова (разделены пробелами)
2. ✅ `TRON_API_KEY` не пустой (получен с https://www.trongrid.io/)
3. ✅ `ENCRYPTION_KEY` длиной 44 символа (base64)
4. ✅ Все значения уникальны и не используются в других проектах

---

## Безопасность

🔒 **КРИТИЧЕСКИ ВАЖНО:**

1. **Никогда не делитесь этими значениями** с кем-либо
2. **Не коммитьте .env файл** в Git (убедитесь, что он в .gitignore)
3. **Сделайте резервные копии** в безопасном месте (например, менеджер паролей)
4. **Для продакшена** используйте секреты из безопасного хранилища:
   - Docker Secrets
   - Kubernetes Secrets
   - AWS Secrets Manager
   - HashiCorp Vault
   - Azure Key Vault



