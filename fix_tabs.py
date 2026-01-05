#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для замены всех табов на пробелы в файле handlers/rooms.py
"""
import sys

def fix_tabs_in_file(filename):
    """Заменяет все табы на 4 пробела в файле"""
    try:
        with open(filename, 'rb') as f:
            content = f.read()
        
        # Проверяем кодировку
        try:
            text = content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                text = content.decode('cp1251')
            except UnicodeDecodeError:
                text = content.decode('latin-1')
        
        # Заменяем табы на 4 пробела
        fixed_text = text.expandtabs(4)
        
        # Сохраняем обратно
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(fixed_text)
        
        print(f"Fixed tabs in {filename}")
        return True
    except Exception as e:
        print(f"Error fixing {filename}: {e}")
        return False

if __name__ == '__main__':
    fix_tabs_in_file('handlers/rooms.py')

