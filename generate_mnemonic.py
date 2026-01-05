#!/usr/bin/env python3
"""
Скрипт для генерации мнемонической фразы (MNEMONIC)
Использование: python generate_mnemonic.py
"""

import sys
import os

# Устанавливаем UTF-8 кодировку для Windows
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')
    sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

try:
    from hdwallet import HDWallet
    from hdwallet.cryptocurrencies import Tron
except ImportError as e:
    print("ERROR: Failed to import required libraries.")
    print(f"Details: {e}")
    print("\nInstall dependencies:")
    print("pip install hdwallet")
    sys.exit(1)

try:
    # Генерируем мнемоническую фразу
    hdwallet = HDWallet(cryptocurrency=Tron)
    hdwallet.from_entropy()  # Генерирует случайную энтропию и создает мнемоническую фразу
    mnemonic = hdwallet.mnemonic()
    
    if not mnemonic:
        raise ValueError("Не удалось сгенерировать мнемоническую фразу")
    
    print("=" * 60)
    print("GENERATED MNEMONIC PHRASE")
    print("=" * 60)
    print()
    print(f"MNEMONIC={mnemonic}")
    print()
    print("=" * 60)
    print("INSTRUCTIONS:")
    print("=" * 60)
    print("1. Copy the MNEMONIC value above")
    print("2. Paste it into line 14 of your .env file")
    print("3. Save this phrase in a secure place!")
    print("4. NEVER share this phrase with anyone!")
    print("=" * 60)
    
except Exception as e:
    print("ERROR generating mnemonic phrase:")
    print(f"{type(e).__name__}: {e}")
    sys.exit(1)



