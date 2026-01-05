#!/usr/bin/env python3
"""
Скрипт для генерации всех секретных значений для .env файла
Использование: python generate_all_secrets.py
"""

from cryptography.fernet import Fernet
from hdwallet import HDWallet
from hdwallet.cryptocurrencies import Tron
import secrets

print("=" * 60)
print("ГЕНЕРАЦИЯ СЕКРЕТНЫХ ЗНАЧЕНИЙ ДЛЯ .ENV")
print("=" * 60)
print()

# 1. ENCRYPTION_KEY (строка 17)
encryption_key = Fernet.generate_key().decode()
print("Строка 17 - ENCRYPTION_KEY:")
print(f"ENCRYPTION_KEY={encryption_key}")
print()

# 2. SECRET_KEY (для JWT, если нужен)
secret_key = secrets.token_urlsafe(32)
print("SECRET_KEY (для JWT):")
print(f"SECRET_KEY={secret_key}")
print()

# 3. MNEMONIC (строка 14)
hdwallet = HDWallet(cryptocurrency=Tron)
hdwallet.from_entropy()
mnemonic = hdwallet.mnemonic()
print("Строка 14 - MNEMONIC:")
print(f"MNEMONIC={mnemonic}")
print()

print("=" * 60)
print("ИНСТРУКЦИИ:")
print("=" * 60)
print("1. Скопируйте ENCRYPTION_KEY в строку 17 вашего .env файла")
print("2. Скопируйте MNEMONIC в строку 14 вашего .env файла")
print("3. Для TRON_API_KEY (строка 15) получите ключ на https://www.trongrid.io/")
print("4. Сохраните эти значения в безопасном месте")
print("5. НИКОГДА не коммитьте .env в Git!")
print("=" * 60)








