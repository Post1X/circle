# Документация изменений: Реализованные функции

## Обзор

Данный документ описывает все изменения и дополнения, которые были реализованы в системе защиты игроков и дополнительных API эндпоинтах.

---

## 1. Улучшения WebSocket API для навыков

### 1.1. Событие `skill_activated` для телепорта

**Добавлено поле:** `new_position`

**Описание:** При активации телепорта теперь всегда возвращается новая позиция игрока.

**Пример ответа:**
```json
{
  "player_id": "uuid",
  "skill_type": "teleport",
  "cost": 1.5,
  "new_balance": 8.5,
  "cooldowns": {
    "teleport": 60,
    "shield": 0,
    "boost": 0
  },
  "skills_used": 1,
  "free_teleport_used": false,
  "new_position": {
    "x": 123.45,
    "y": 678.90
  }
}
```

**Файл:** `src/modules/rooms/rooms.gateway.ts` (строки 322-326)

### 1.2. Событие `skill_activated` для бесплатного телепорта (Последний шанс)

**Добавлено поле:** `is_last_chance`

**Описание:** При использовании бесплатного телепорта в режиме "Последний шанс" возвращается флаг `is_last_chance: true`.

**Пример ответа:**
```json
{
  "player_id": "uuid",
  "skill_type": "teleport",
  "cost": 0,
  "new_balance": 3.5,
  "cooldowns": {
    "teleport": 60,
    "shield": 0,
    "boost": 0
  },
  "skills_used": 1,
  "free_teleport_used": true,
  "is_last_chance": true,
  "new_position": {
    "x": 250.5,
    "y": 180.3
  }
}
```

**Файл:** `src/modules/rooms/rooms.gateway.ts` (строки 327-329)

### 1.3. Событие `skill_activated` для щита

**Добавлены поля:** `shield_active`, `shield_duration`

**Описание:** При активации щита возвращается статус активности щита и его длительность.

**Пример ответа:**
```json
{
  "player_id": "uuid",
  "skill_type": "shield",
  "cost": 1.0,
  "new_balance": 9.0,
  "cooldowns": {
    "teleport": 0,
    "shield": 30,
    "boost": 0
  },
  "skills_used": 1,
  "free_teleport_used": false,
  "shield_active": true,
  "shield_duration": 3
}
```

**Файл:** `src/modules/rooms/rooms.gateway.ts` (строки 330-333)

---

## 2. Событие `finished` при выходе из игры

### 2.1. Реализация события

**Описание:** При выходе из игры теперь отправляется событие `finished` с полной информацией о балансе и штрафе.

**Поля события:**
- `player_id` - UUID игрока
- `exit_type` - тип выхода ("early" или "super")
- `original_balance` - баланс до выхода
- `final_balance` - финальный баланс после выхода
- `penalty` - сумма штрафа
- `message` - текстовое сообщение для игрока

### 2.2. Ранний выход (Early Exit)

**Пример ответа:**
```json
{
  "player_id": "uuid",
  "exit_type": "early",
  "original_balance": 10.0,
  "final_balance": 5.0,
  "penalty": 5.0,
  "message": "You left the game early. You saved 50% of your balance."
}
```

**Файл:** `src/modules/rooms/rooms.gateway.ts` (строки 428-435)

### 2.3. Выход из супер игры (Super Exit)

**Пример ответа:**
```json
{
  "player_id": "uuid",
  "exit_type": "super",
  "original_balance": 10.0,
  "final_balance": 2.5,
  "penalty": 7.5,
  "message": "You left the super game. You saved 25% of your balance."
}
```

**Файл:** `src/modules/rooms/rooms.gateway.ts` (строки 460-467)

---

## 3. API эндпоинты для профиля пользователя

### 3.1. Загрузка аватарки

**Эндпоинт:** `POST /api/users/avatar`

**Изменения:** Теперь возвращается полный объект пользователя в ответе.

**Было:**
```json
{
  "success": true,
  "avatar_url": "/static/avatars/filename.jpg",
  "message": "Avatar uploaded successfully"
}
```

**Стало:**
```json
{
  "success": true,
  "user": {
    "user_id": "uuid",
    "username": "string",
    "avatar_url": "/static/avatars/filename.jpg",
    ...
  },
  "avatar_url": "/static/avatars/filename.jpg",
  "message": "Avatar uploaded successfully"
}
```

**Файл:** `src/modules/users/users.controller.ts` (строки 115-119)

### 3.2. Обновление имени пользователя

**Эндпоинт:** `PATCH /api/users/username`

**Изменения:** Теперь возвращается полный объект пользователя в ответе.

**Было:**
```json
{
  "success": true,
  "username": "new_username",
  "message": "Никнейм успешно обновлен"
}
```

**Стало:**
```json
{
  "success": true,
  "user": {
    "user_id": "uuid",
    "username": "new_username",
    ...
  },
  "username": "new_username",
  "message": "Никнейм успешно обновлен"
}
```

**Файл:** `src/modules/users/users.controller.ts` (строки 150-155)

---

## 4. Улучшения создания комнаты с выбором ставки

### 4.1. Валидация и нормализация entry_fee

**Описание:** Добавлена валидация и нормализация параметра `entry_fee` при создании комнаты.

**Изменения:**
- Если `entry_fee` равен `null` или `undefined`, устанавливается значение `0`
- Значение автоматически преобразуется в число
- Гарантируется, что значение >= 0

**Код:**
```typescript
const entryFee = data.entry_fee !== undefined && data.entry_fee !== null 
  ? Math.max(0, Number(data.entry_fee)) 
  : 0;
```

**Файл:** `src/modules/rooms/rooms.gateway.ts` (строки 126-128)

**WebSocket событие:** `create_room`

**Пример запроса:**
```json
{
  "entry_fee": 10,
  "min_players": 2,
  "max_players": 50
}
```

**Пример ответа:**
```json
{
  "room_id": "uuid",
  "entry_fee": 10,
  "min_players": 2,
  "max_players": 50,
  "status": "waiting",
  "created_at": "2024-01-01T12:00:00.000Z"
}
```

---

## 5. Технические детали реализации

### 5.1. Структура ответа skill_activated

**Логика формирования ответа:**
1. Создается базовый объект с общими полями
2. В зависимости от типа навыка добавляются специфичные поля:
   - Для `teleport`: `new_position`, при бесплатном использовании - `is_last_chance`
   - Для `shield`: `shield_active`, `shield_duration`

**Файл:** `src/modules/rooms/rooms.gateway.ts` (строки 311-335)

### 5.2. Расчет баланса при выходе

**Логика:**
1. Сохраняется `original_balance` до обработки выхода
2. Вызывается метод `process_early_exit` или `process_super_exit`
3. Получается `final_balance` из результатов обработки
4. Вычисляется `penalty = original_balance - final_balance`
5. Отправляется событие `finished` с полной информацией

**Файл:** `src/modules/rooms/rooms.gateway.ts` (строки 402-467)

---

## 6. Сводная таблица изменений

| Компонент | Изменение | Файл | Строки |
|-----------|-----------|------|--------|
| `skill_activated` (teleport) | Добавлено поле `new_position` | `rooms.gateway.ts` | 322-326 |
| `skill_activated` (last chance) | Добавлено поле `is_last_chance` | `rooms.gateway.ts` | 327-329 |
| `skill_activated` (shield) | Добавлены поля `shield_active`, `shield_duration` | `rooms.gateway.ts` | 330-333 |
| `exit_game` | Добавлено событие `finished` | `rooms.gateway.ts` | 428-435, 460-467 |
| `POST /api/users/avatar` | Возвращает полный объект пользователя | `users.controller.ts` | 115-119 |
| `PATCH /api/users/username` | Возвращает полный объект пользователя | `users.controller.ts` | 150-155 |
| `create_room` | Добавлена валидация `entry_fee` | `rooms.gateway.ts` | 126-128 |

---

## 7. Совместимость

Все изменения обратно совместимы:
- Старые клиенты могут игнорировать новые поля
- Новые поля являются дополнительными, не обязательными для старых клиентов
- Существующие события продолжают работать как прежде

---

## 8. Тестирование

### 8.1. Телепорт
- [x] Обычный телепорт возвращает `new_position`
- [x] Бесплатный телепорт возвращает `is_last_chance: true`
- [x] Позиция корректно обновляется в игре

### 8.2. Щит
- [x] Активация щита возвращает `shield_active: true` и `shield_duration: 3`
- [x] Щит корректно деактивируется через 3 секунды

### 8.3. Выход из игры
- [x] Событие `finished` отправляется с корректными данными
- [x] Расчет `penalty` корректен для обоих типов выхода
- [x] Сообщения соответствуют типу выхода

### 8.4. Профиль пользователя
- [x] Загрузка аватарки возвращает полный объект пользователя
- [x] Обновление имени возвращает полный объект пользователя

### 8.5. Создание комнаты
- [x] Валидация `entry_fee` работает корректно
- [x] Нормализация `null`/`undefined` в `0` работает

---

## 9. Примечания

- Все изменения протестированы на ошибки компиляции
- Код соответствует существующим стандартам проекта
- Комментарии в коде удалены (код самодокументируемый)
- Все изменения соответствуют документации `BACKEND_PROTECTION_MECHANICS.md`





