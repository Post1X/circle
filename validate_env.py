#!/usr/bin/env python3
"""
Скрипт для проверки корректности заполнения .env файла
Использование: python validate_env.py
"""

import sys
import os

# Устанавливаем UTF-8 кодировку для Windows
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')
    sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

try:
    from servises.config import config
except ImportError as e:
    print("ERROR: Failed to import config module.")
    print(f"Details: {e}")
    print("\nMake sure you are in the project root directory.")
    sys.exit(1)
except Exception as e:
    print("ERROR: Failed to load configuration from .env file.")
    print(f"Details: {e}")
    print("\nCheck that .env file exists and all required variables are set.")
    sys.exit(1)

def validate_string(value, name, min_length=1):
    """Проверка строковой переменной"""
    if not value or len(value.strip()) < min_length:
        return False, f"{name} is empty or too short (minimum {min_length} characters)"
    return True, "OK"

def validate_int(value, name, min_value=1):
    """Проверка целочисленной переменной"""
    try:
        int_val = int(value)
        if int_val < min_value:
            return False, f"{name} must be at least {min_value}"
        return True, "OK"
    except (ValueError, TypeError):
        return False, f"{name} is not a valid integer"

def validate_mnemonic(mnemonic):
    """Проверка мнемонической фразы"""
    if not mnemonic:
        return False, "MNEMONIC is empty"
    
    words = mnemonic.strip().split()
    if len(words) not in [12, 24]:
        return False, f"MNEMONIC must contain 12 or 24 words, found {len(words)}"
    
    return True, f"OK ({len(words)} words)"

def validate_encryption_key(key):
    """Проверка ключа шифрования Fernet"""
    if not key:
        return False, "ENCRYPTION_KEY is empty"
    
    try:
        from cryptography.fernet import Fernet
        # Попытка создать Fernet объект для проверки формата
        Fernet(key.encode())
        if len(key) != 44:
            return False, f"ENCRYPTION_KEY length should be 44 characters, found {len(key)}"
        return True, "OK"
    except Exception as e:
        return False, f"ENCRYPTION_KEY is not a valid Fernet key: {str(e)}"

def validate_secret_key(key):
    """Проверка секретного ключа"""
    if not key:
        return False, "SECRET_KEY is empty"
    
    if len(key) < 32:
        return False, f"SECRET_KEY should be at least 32 characters, found {len(key)}"
    
    return True, "OK"

print("=" * 60)
print("VALIDATING .ENV FILE")
print("=" * 60)
print()

errors = []
warnings = []

# Проверка базы данных
print("Database Configuration:")
db_name_ok, db_name_msg = validate_string(config.db_name, "DB_NAME")
print(f"  DB_NAME: {db_name_msg}")
if not db_name_ok:
    errors.append("DB_NAME")

db_user_ok, db_user_msg = validate_string(config.db_user, "DB_USER")
print(f"  DB_USER: {db_user_msg}")
if not db_user_ok:
    errors.append("DB_USER")

db_pass_ok, db_pass_msg = validate_string(config.db_pass, "DB_PASS", min_length=8)
print(f"  DB_PASS: {db_pass_msg}")
if not db_pass_ok:
    errors.append("DB_PASS")
elif len(config.db_pass) < 12:
    warnings.append("DB_PASS is less than 12 characters - consider using a stronger password")

db_host_ok, db_host_msg = validate_string(config.db_host, "DB_HOST")
print(f"  DB_HOST: {db_host_msg}")
if not db_host_ok:
    errors.append("DB_HOST")

db_port_ok, db_port_msg = validate_int(config.db_port, "DB_PORT", min_value=1)
print(f"  DB_PORT: {db_port_msg}")
if not db_port_ok:
    errors.append("DB_PORT")

print()

# Проверка Redis
print("Redis Configuration:")
redis_host_ok, redis_host_msg = validate_string(config.REDIS_HOST, "REDIS_HOST")
print(f"  REDIS_HOST: {redis_host_msg}")
if not redis_host_ok:
    errors.append("REDIS_HOST")

redis_port_ok, redis_port_msg = validate_int(config.REDIS_PORT, "REDIS_PORT", min_value=1)
print(f"  REDIS_PORT: {redis_port_msg}")
if not redis_port_ok:
    errors.append("REDIS_PORT")

print()

# Проверка JWT
print("JWT Configuration:")
secret_key_ok, secret_key_msg = validate_secret_key(config.SECRET_KEY)
print(f"  SECRET_KEY: {secret_key_msg}")
if not secret_key_ok:
    errors.append("SECRET_KEY")

algorithm_ok, algorithm_msg = validate_string(config.ALGORITHM, "ALGORITHM")
print(f"  ALGORITHM: {algorithm_msg}")
if not algorithm_ok:
    errors.append("ALGORITHM")
elif config.ALGORITHM.upper() not in ['HS256', 'HS384', 'HS512']:
    warnings.append(f"ALGORITHM '{config.ALGORITHM}' is not a standard JWT algorithm")

print()

# Проверка Tron
print("Tron Blockchain Configuration:")
mnemonic_ok, mnemonic_msg = validate_mnemonic(config.mnemonic)
print(f"  MNEMONIC: {mnemonic_msg}")
if not mnemonic_ok:
    errors.append("MNEMONIC")

tron_api_key_ok, tron_api_key_msg = validate_string(config.tron_api_key, "TRON_API_KEY")
print(f"  TRON_API_KEY: {tron_api_key_msg}")
if not tron_api_key_ok:
    errors.append("TRON_API_KEY")

encryption_key_ok, encryption_key_msg = validate_encryption_key(config.ENCRYPTION_KEY)
print(f"  ENCRYPTION_KEY: {encryption_key_msg}")
if not encryption_key_ok:
    errors.append("ENCRYPTION_KEY")

print()

# Проверка режима
print("Application Mode:")
print(f"  MODE: {config.mode}")
if config.mode not in ['test', 'prod']:
    errors.append("MODE")
elif config.mode == 'test':
    warnings.append("Running in TEST mode - auto-reload is enabled")

print()

# Итоговый результат
print("=" * 60)
if errors:
    print("VALIDATION FAILED!")
    print(f"Errors found in: {', '.join(errors)}")
    print("Please fix these issues before running the application.")
    sys.exit(1)
else:
    print("VALIDATION SUCCESSFUL!")
    print("All required environment variables are set correctly.")
    
    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"  - {warning}")
    
    print("\nYour .env file is ready to use!")
    print("=" * 60)
    sys.exit(0)

