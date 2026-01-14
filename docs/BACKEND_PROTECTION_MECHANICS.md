# Документация для бекенда: Защитные механики игры

## Обзор

Данная документация описывает защитные механики игры, которые помогают игрокам избежать полной потери баланса и снизить риски во время игры. К ним относятся:

1. **Платный навык "Рандомный телепорт"** - мгновенное перемещение в безопасное место
2. **Режим "Последний шанс"** - бесплатный телепорт при низком балансе в супер игре
3. **Защитный щит** - временная неуязвимость
4. **Механика выхода** - возможность выйти из игры с частичным сохранением баланса (50% / 25%)

---

## 1. Рандомный телепорт (Платный навык)

### Описание

Платный навык, который позволяет игроку мгновенно телепортироваться в случайное безопасное место на карте. Стоимость составляет процент от текущего баланса игрока.

### WebSocket API

#### Событие: `activate_skill`

**Клиент → Сервер:**
```json
{
  "skill_type": "teleport"
}
```

#### Событие: `skill_activated`

**Сервер → Клиент (реализовано):**
```json
{
  "player_id": "string (UUID)",
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

**Важно:** Поле `new_position` всегда присутствует для телепорта и содержит новые координаты игрока после телепортации.

#### Событие: `skill_error`

**Сервер → Клиент:**
```json
{
  "error_code": "insufficient_balance" | "minimum_balance_required" | "skill_limit_reached" | "skill_on_cooldown" | "invalid_skill_type" | "game_not_active" | "player_not_in_game",
  "message": "string",
  "skill_type": "teleport"
}
```

### Параметры навыка

- **Стоимость:** 15% от текущего баланса
- **Cooldown:** 60 секунд
- **Длительность:** Мгновенное применение
- **Минимальный баланс:** $1.0 для активации любого навыка
- **Максимум использований:** 5 раз за игру

### Логика расчета стоимости

```python
base_cost_percentage = 0.15  # 15%

# Если был использован бесплатный телепорт (режим "Последний шанс")
if player.free_teleport_used:
    cost_percentage = base_cost_percentage * 1.05  # 15% * 1.05 = 15.75% ≈ 20%
else:
    cost_percentage = base_cost_percentage  # 15%

cost = player.balance * cost_percentage
```

### Валидация на бекенде

1. **Проверка авторизации:**
   - Игрок должен быть авторизован
   - Игрок должен быть в активной игре

2. **Проверка фазы игры:**
   - Игра должна быть активна
   - Игрок не должен быть выбывшим

3. **Проверка лимита активаций:**
   - `skills_used < 5`
   - Если достигнут лимит → ошибка `skill_limit_reached`

4. **Проверка cooldown:**
   - `cooldowns.teleport == 0`
   - Если на cooldown → ошибка `skill_on_cooldown`

5. **Проверка минимального баланса:**
   - `balance >= 1.0`
   - Если баланс < $1 → ошибка `minimum_balance_required`

6. **Расчет стоимости:**
   - Учесть штраф +5% если был использован бесплатный телепорт
   - Рассчитать: `cost = balance * cost_percentage`

7. **Проверка достаточности баланса:**
   - `balance >= cost`
   - Если недостаточно → ошибка `insufficient_balance`

### Применение эффекта

1. **Генерация новой позиции:**
   - Новая позиция должна быть внутри безопасной зоны (safe_zone)
   - Позиция должна быть случайной, но безопасной
   - Минимальное расстояние от края безопасной зоны: радиус игрока + 50 пикселей

2. **Списывание стоимости:**
   ```python
   player.balance -= cost
   game.bonus_fund += cost  # Добавляем в бонусный фонд
   player.skills_used += 1
   ```

3. **Установка cooldown:**
   ```python
   player.cooldowns["teleport"] = 60  # 60 секунд
   ```

4. **Обновление позиции:**
   ```python
   player.x = new_x
   player.y = new_y
   ```

5. **Отправка события:**
   - Отправить `skill_activated` с полем `new_position` игроку
   - Обновить `game_state` с новой позицией игрока для всех игроков

### Примеры

#### Пример 1: Успешная активация телепорта

```
Игрок: balance = $10.00, skills_used = 2, cooldowns.teleport = 0
Расчет: cost = $10.00 * 0.15 = $1.50
Результат: 
  - balance = $8.50
  - bonus_fund += $1.50
  - skills_used = 3
  - cooldowns.teleport = 60
  - Новая позиция: (x: 123.45, y: 678.90)
```

**Ответ сервера:**
```json
{
  "player_id": "uuid-here",
  "skill_type": "teleport",
  "cost": 1.5,
  "new_balance": 8.5,
  "cooldowns": {
    "teleport": 60,
    "shield": 0,
    "boost": 0
  },
  "skills_used": 3,
  "free_teleport_used": false,
  "new_position": {
    "x": 123.45,
    "y": 678.90
  }
}
```

#### Пример 2: Телепорт после использования бесплатного

```
Игрок: balance = $10.00, free_teleport_used = True
Расчет: cost = $10.00 * 0.20 = $2.00 (штраф +5%)
Результат:
  - balance = $8.00
  - bonus_fund += $2.00
```

---

## 2. Режим "Последний шанс" (Бесплатный телепорт)

### Описание

Специальный режим, который предоставляет игроку один бесплатный телепорт в супер игре, когда баланс игрока низкий и осталось мало времени до конца игры. Это защитная механика для предотвращения полной потери баланса.

### Условия активации

Режим "Последний шанс" доступен только если выполняются **все** следующие условия:

1. **Фаза игры:** `phase === "super"` (супер игра)
2. **Оставшееся время:** `120 <= super_game_time_remaining <= 180` секунд (2-3 минуты до конца)
3. **Баланс игрока:** `balance < 5.0` (меньше $5)
4. **Бесплатный телепорт не использован:** `free_teleport_used === false`
5. **Тип навыка:** `skill_type === "teleport"`

### Логика проверки

```python
def is_last_chance_eligible(player, game):
    # Проверка фазы игры
    if game.phase != "super":
        return False
    
    # Проверка времени (за 3 минуты до конца = 2-я минута из 5)
    time_remaining = game.super_game_time_remaining
    if time_remaining is None:
        return False
    if time_remaining > 180 or time_remaining < 120:  # Не в диапазоне 2-3 минуты
        return False
    
    # Проверка баланса
    if player.balance >= 5.0:
        return False
    
    # Проверка что бесплатный телепорт еще не использован
    if player.free_teleport_used:
        return False
    
    return True
```

### Применение бесплатного телепорта

Когда игрок активирует телепорт в режиме "Последний шанс":

1. **Стоимость = 0:**
   ```python
   cost = 0  # Бесплатно
   ```

2. **Установка флага:**
   ```python
   player.free_teleport_used = True
   ```

3. **Применение эффекта:**
   - Телепорт выполняется как обычно
   - Cooldown устанавливается: `cooldowns.teleport = 60`
   - Счетчик навыков увеличивается: `skills_used += 1`

4. **Штраф на будущие навыки:**
   - После использования бесплатного телепорта
   - Все последующие платные навыки стоят на **+5% больше**:
     - Телепорт: 15% → 20%
     - Щит: 10% → 15%
     - Ускорение: 5% → 10%

### Ответ сервера (реализовано)

**Сервер → Клиент (`skill_activated`):**
```json
{
  "player_id": "string (UUID)",
  "skill_type": "teleport",
  "cost": 0,
  "new_balance": 3.50,
  "cooldowns": {
    "teleport": 60,
    "shield": 0,
    "boost": 0
  },
  "skills_used": 1,
  "free_teleport_used": true,
  "is_last_chance": true,
  "new_position": {
    "x": 123.45,
    "y": 678.90
  }
}
```

**Важно:** 
- Поле `is_last_chance: true` присутствует только при использовании бесплатного телепорта
- Поле `cost: 0` указывает на бесплатное использование
- Поле `new_position` всегда присутствует для телепорта

### Примеры

#### Пример 1: Активация бесплатного телепорта

```
Условия:
  - phase = "super"
  - super_game_time_remaining = 150 секунд
  - balance = $3.50
  - free_teleport_used = false

Результат:
  - cost = $0.00 (бесплатно)
  - balance = $3.50 (не изменился)
  - free_teleport_used = true
  - cooldowns.teleport = 60
  - skills_used += 1
  - is_last_chance = true
```

**Ответ сервера:**
```json
{
  "player_id": "uuid-here",
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

#### Пример 2: Попытка использовать второй раз

```
Условия:
  - free_teleport_used = true

Результат:
  - Ошибка: бесплатный телепорт уже использован
  - Телепорт стоит 20% от баланса (штраф +5%)
```

---

## 3. Защитный щит

### Описание

Платный навык, который предоставляет игроку временную неуязвимость на 3 секунды. Игрок не получает урон от зоны и других игроков во время действия щита.

### WebSocket API

#### Событие: `activate_skill`

**Клиент → Сервер:**
```json
{
  "skill_type": "shield"
}
```

#### Событие: `skill_activated`

**Сервер → Клиент (реализовано):**
```json
{
  "player_id": "string (UUID)",
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

**Важно:** 
- Поля `shield_active` и `shield_duration` присутствуют только для навыка "shield"
- `shield_active: true` означает, что щит активен
- `shield_duration: 3` указывает длительность щита в секундах

### Параметры навыка

- **Стоимость:** 10% от текущего баланса (или 15% если был использован бесплатный телепорт)
- **Cooldown:** 30 секунд
- **Длительность:** 3 секунды
- **Минимальный баланс:** $1.0 для активации
- **Максимум использований:** 5 раз за игру

### Логика расчета стоимости

```python
base_cost_percentage = 0.10  # 10%

# Если был использован бесплатный телепорт
if player.free_teleport_used:
    cost_percentage = base_cost_percentage * 1.05  # 10% * 1.05 = 10.5% ≈ 15%
else:
    cost_percentage = base_cost_percentage  # 10%

cost = player.balance * cost_percentage
```

### Валидация на бекенде

Аналогично телепорту, но с проверкой:
- `cooldowns.shield == 0`
- `balance >= cost`

### Применение эффекта

1. **Активация щита:**
   ```python
   player.shield_active = True
   ```

2. **Списывание стоимости:**
   ```python
   player.balance -= cost
   game.bonus_fund += cost
   player.skills_used += 1
   ```

3. **Установка cooldown:**
   ```python
   player.cooldowns["shield"] = 30  # 30 секунд
   ```

4. **Таймер деактивации:**
   ```python
   # Через 3 секунды
   player.shield_active = False
   ```

5. **Защита от урона:**
   - Во время `shield_active = True` игрок не получает урон от:
     - Зоны (zone damage)
     - Других игроков (поглощение)
     - Бонусных зон (damage)

### Обновление состояния

Во время действия щита в `game_state`:
```json
{
  "players": [
    {
      "player_id": "string",
      "shield_active": true,
      ...
    }
  ]
}
```

### Примеры

#### Пример 1: Активация щита

```
Игрок: balance = $10.00, cooldowns.shield = 0
Расчет: cost = $10.00 * 0.10 = $1.00
Результат:
  - balance = $9.00
  - bonus_fund += $1.00
  - shield_active = true (на 3 секунды)
  - cooldowns.shield = 30
```

**Ответ сервера:**
```json
{
  "player_id": "uuid-here",
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

#### Пример 2: Щит после бесплатного телепорта

```
Игрок: balance = $10.00, free_teleport_used = True
Расчет: cost = $10.00 * 0.15 = $1.50 (штраф +5%)
Результат:
  - balance = $8.50
  - bonus_fund += $1.50
```

**Ответ сервера:**
```json
{
  "player_id": "uuid-here",
  "skill_type": "shield",
  "cost": 1.5,
  "new_balance": 8.5,
  "cooldowns": {
    "teleport": 0,
    "shield": 30,
    "boost": 0
  },
  "skills_used": 2,
  "free_teleport_used": true,
  "shield_active": true,
  "shield_duration": 3
}
```

---

## 4. Механика выхода из игры

### Описание

Игрок может выйти из игры досрочно, сохранив часть своего баланса. Существует два типа выхода с разными процентами сохранения баланса.

### Типы выхода

#### 4.1. Ранний выход (Early Exit) - 50% сохранения

**Условия:**
- Игрок выходит до достижения топ-10
- Фаза игры: `phase === "start"` (начальная фаза)

**Сохранение баланса:** 50%

**Формула:**
```python
final_balance = player.balance * 0.50  # 50% от текущего баланса
penalty = player.balance * 0.50  # 50% штраф
```

#### 4.2. Выход из супер игры (Super Exit) - 25% сохранения

**Условия:**
- Игрок выходит из супер игры (после достижения топ-10)
- Фаза игры: `phase === "super"` (супер игра)

**Сохранение баланса:** 25%

**Формула:**
```python
final_balance = player.balance * 0.25  # 25% от текущего баланса
penalty = player.balance * 0.75  # 75% штраф
```

### WebSocket API

#### Событие: `exit_game`

**Клиент → Сервер:**
```json
{
  "exit_type": "early" | "super"
}
```

**Параметры:**
- `exit_type: "early"` - ранний выход (до топ-10), сохранение 50%
- `exit_type: "super"` - выход из супер игры, сохранение 25%

#### Событие: `finished` (реализовано)

**Сервер → Клиент (отправляется игроку, который вышел):**
```json
{
  "player_id": "string (UUID)",
  "exit_type": "early" | "super",
  "original_balance": 10.0,
  "final_balance": 5.0,
  "penalty": 5.0,
  "message": "You left the game early. You saved 50% of your balance."
}
```

**Поля:**
- `player_id` - UUID игрока
- `exit_type` - тип выхода ("early" или "super")
- `original_balance` - баланс игрока до выхода
- `final_balance` - финальный баланс после выхода (сохраненная сумма)
- `penalty` - сумма штрафа (разница между original_balance и final_balance)
- `message` - текстовое сообщение для игрока

**Сообщения:**
- Для раннего выхода: `"You left the game early. You saved 50% of your balance."`
- Для выхода из супер игры: `"You left the super game. You saved 25% of your balance."`

#### Событие: `player_exited` (для других игроков)

**Сервер → Клиент (отправляется всем игрокам в комнате):**
```json
{
  "player_id": "string (UUID)",
  "exit_type": "early" | "super",
  "winnings": 5.0
}
```

### Валидация на бекенде

1. **Проверка авторизации:**
   - Игрок должен быть авторизован
   - Игрок должен быть в активной игре

2. **Проверка типа выхода:**
   - Если `exit_type === "early"`:
     - Проверить что фаза игры === "start"
   - Если `exit_type === "super"`:
     - Проверить что фаза игры === "super"
     - Игрок должен быть в супер игре

3. **Расчет финального баланса:**
   ```python
   original_balance = player.balance
   
   if exit_type == "early":
       final_balance = player.balance * 0.50
       penalty = player.balance * 0.50
   elif exit_type == "super":
       final_balance = player.balance * 0.25
       penalty = player.balance * 0.75
   ```

4. **Обновление баланса:**
   ```python
   # Штраф добавляется в бонусный фонд
   game.bonus_fund += penalty
   ```

5. **Удаление игрока из игры:**
   ```python
   game.remove_player(player_id)
   ```

6. **Отправка событий:**
   - Отправить `finished` игроку, который вышел (с полной информацией)
   - Отправить `player_exited` всем остальным игрокам в комнате
   - Обновить `game_state` для остальных игроков

### Примеры

#### Пример 1: Ранний выход (50%)

```
Игрок: balance = $10.00, phase = "start"
Расчет:
  - original_balance = $10.00
  - final_balance = $10.00 * 0.50 = $5.00
  - penalty = $10.00 * 0.50 = $5.00

Результат:
  - player.balance = $5.00 (кредитуется на счет)
  - bonus_fund += $5.00
  - player удаляется из игры
```

**Ответ сервера (finished):**
```json
{
  "player_id": "uuid-here",
  "exit_type": "early",
  "original_balance": 10.0,
  "final_balance": 5.0,
  "penalty": 5.0,
  "message": "You left the game early. You saved 50% of your balance."
}
```

#### Пример 2: Выход из супер игры (25%)

```
Игрок: balance = $10.00, phase = "super"
Расчет:
  - original_balance = $10.00
  - final_balance = $10.00 * 0.25 = $2.50
  - penalty = $10.00 * 0.75 = $7.50

Результат:
  - player.balance = $2.50 (кредитуется на счет)
  - bonus_fund += $7.50
  - player удаляется из игры
```

**Ответ сервера (finished):**
```json
{
  "player_id": "uuid-here",
  "exit_type": "super",
  "original_balance": 10.0,
  "final_balance": 2.5,
  "penalty": 7.5,
  "message": "You left the super game. You saved 25% of your balance."
}
```

#### Пример 3: Попытка выхода с неправильным типом

```
Игрок: phase = "start", exit_type = "super"

Результат:
  - Ошибка: "Invalid exit type or phase"
  - Событие: exit_error
```

---

## 5. Интеграция всех механик

### Взаимодействие механик

1. **Бесплатный телепорт → Штраф на навыки:**
   - После использования бесплатного телепорта
   - Все последующие платные навыки стоят +5% больше

2. **Навыки → Бонусный фонд:**
   - Стоимость всех навыков добавляется в `bonus_fund`
   - Это увеличивает награды для победителей

3. **Выход → Бонусный фонд:**
   - Штраф при выходе добавляется в `bonus_fund`
   - Это увеличивает награды для победителей

### Структура данных игрока

```python
class Player:
    player_id: str
    balance: float
    skills_used: int
    free_teleport_used: bool
    cooldowns: Dict[str, int]  # {"teleport": 60, "shield": 30, "boost": 15}
    shield_active: bool
    x: float
    y: float
    rank: int
    status: str  # "active", "exited", "eliminated"
```

### Структура данных игры

```python
class Game:
    game_id: str
    phase: str  # "start", "top10", "super", "finished"
    super_game_time_remaining: int | None
    bonus_fund: float
    zone_fund: float
    players: List[Player]
```

---

## 6. Дополнительные API эндпоинты

### 6.1. Загрузка аватарки

**Эндпоинт:** `POST /api/users/avatar`

**Авторизация:** Требуется (JWT токен)

**Content-Type:** `multipart/form-data`

**Параметры:**
- `avatar` (file) - файл изображения (jpg, jpeg, png, gif)
- Максимальный размер: 5MB

**Ответ (реализовано):**
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

**Ошибки:**
- `400 Bad Request` - файл не загружен или неверный тип
- `401 Unauthorized` - не авторизован

### 6.2. Обновление имени пользователя

**Эндпоинт:** `PATCH /api/users/username`

**Авторизация:** Требуется (JWT токен)

**Тело запроса:**
```json
{
  "username": "new_username"
}
```

**Ответ (реализовано):**
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

**Ошибки:**
- `400 Bad Request` - никнейм уже занят другим пользователем
- `401 Unauthorized` - не авторизован

### 6.3. Создание комнаты с выбором ставки

**WebSocket событие:** `create_room`

**Клиент → Сервер:**
```json
{
  "entry_fee": 10,
  "min_players": 2,
  "max_players": 50
}
```

**Параметры:**
- `entry_fee` (number, optional) - вступительный взнос (ставка). По умолчанию: 0
- `min_players` (number, optional) - минимальное количество игроков. По умолчанию: 2
- `max_players` (number, optional) - максимальное количество игроков. По умолчанию: 50

**Валидация (реализовано):**
- `entry_fee` нормализуется: если `null` или `undefined`, устанавливается 0
- `entry_fee` должен быть >= 0
- Значения автоматически преобразуются в числа

**Ответ (реализовано):**
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

**Важно:** При присоединении к комнате с `entry_fee > 0` баланс игрока автоматически списывается.

---

## 7. Требования к реализации

### Обязательные функции

1. **Валидация всех условий:**
   - Проверка фазы игры
   - Проверка баланса
   - Проверка cooldown
   - Проверка лимитов

2. **Корректный расчет стоимости:**
   - Учет штрафа после бесплатного телепорта
   - Правильный расчет процентов

3. **Синхронизация состояния:**
   - Обновление `game_state` для всех игроков
   - Отслеживание флагов (`free_teleport_used`, `shield_active`)

4. **Обработка времени:**
   - Отслеживание `super_game_time_remaining`
   - Таймеры для щита (3 секунды)
   - Cooldown для всех навыков

5. **Безопасность:**
   - Проверка прав доступа
   - Защита от дублирования активаций
   - Валидация всех входных данных

### Рекомендации

1. **Производительность:**
   - Кэширование расчетов стоимости
   - Оптимизация проверок условий

2. **Логирование:**
   - Логировать все активации навыков
   - Логировать выходы из игры
   - Отслеживать использование "Последний шанс"

3. **Тестирование:**
   - Тесты для всех условий активации
   - Тесты для расчета стоимости
   - Тесты для взаимодействия механик

---

## 8. Примеры полных сценариев

### Сценарий 1: Использование всех защитных механик

```
1. Игрок начинает игру: balance = $10.00

2. Активация щита:
   - cost = $1.00 (10%)
   - balance = $9.00
   - shield_active = true (3 сек)
   - Ответ: skill_activated с shield_active: true, shield_duration: 3

3. Активация телепорта:
   - cost = $1.35 (15%)
   - balance = $7.65
   - Телепорт в безопасное место
   - Ответ: skill_activated с new_position: {x, y}

4. Вход в супер игру:
   - phase = "super"
   - balance = $3.50
   - super_game_time_remaining = 150 сек

5. Активация бесплатного телепорта ("Последний шанс"):
   - cost = $0.00 (бесплатно)
   - balance = $3.50 (не изменился)
   - free_teleport_used = true
   - Ответ: skill_activated с is_last_chance: true, cost: 0, new_position: {x, y}

6. Активация щита (с штрафом):
   - cost = $0.53 (15% вместо 10%)
   - balance = $2.97
   - Ответ: skill_activated с shield_active: true, shield_duration: 3

7. Ранний выход:
   - exit_type = "early"
   - original_balance = $2.97
   - final_balance = $2.97 * 0.50 = $1.49
   - penalty = $1.48
   - Ответ: finished с полной информацией
```

### Сценарий 2: Выход из супер игры

```
1. Игрок в супер игре: balance = $20.00, rank = 5

2. Выход из супер игры:
   - exit_type = "super"
   - original_balance = $20.00
   - final_balance = $20.00 * 0.25 = $5.00
   - penalty = $15.00
   - bonus_fund += $15.00
   - Ответ: finished с полной информацией
```

---

## 9. Коды ошибок

| Код ошибки | Описание | Когда возникает |
|------------|----------|-----------------|
| `insufficient_balance` | Недостаточно баланса для активации навыка | `balance < cost` |
| `minimum_balance_required` | Баланс меньше минимального | `balance < 1.0` |
| `skill_limit_reached` | Достигнут лимит использований | `skills_used >= 5` |
| `skill_on_cooldown` | Навык на cooldown | `cooldowns[skill_type] > 0` |
| `free_teleport_used` | Бесплатный телепорт уже использован | Попытка использовать второй раз |
| `invalid_skill_type` | Неверный тип навыка | `skill_type` не существует |
| `game_not_active` | Игра не активна | Игра завершена или не начата |
| `player_not_in_game` | Игрок не в игре | Игрок не участвует в игре |
| `invalid_exit_type` | Неверный тип выхода | Несоответствие типа выхода фазе игры |

---

## 10. Структура ответов API (реализовано)

### skill_activated для телепорта (обычный)

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

### skill_activated для телепорта (бесплатный, последний шанс)

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

### skill_activated для щита

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

### finished (ранний выход)

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

### finished (выход из супер игры)

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

---

## Примечания

- Все проценты рассчитываются от **текущего баланса** на момент активации
- Штраф +5% применяется ко **всем** навыкам после использования бесплатного телепорта
- Бесплатный телепорт доступен **только один раз** за игру
- Выход из игры **необратим** - игрок не может вернуться
- Все изменения баланса должны быть **атомарными** (транзакции)
- Необходимо **логировать** все операции для аудита
- Поля в ответах `skill_activated` зависят от типа навыка:
  - Для `teleport`: всегда присутствует `new_position`
  - Для `teleport` с `is_last_chance: true`: присутствует `is_last_chance`
  - Для `shield`: всегда присутствуют `shield_active` и `shield_duration`
- Событие `finished` отправляется только игроку, который вышел из игры
- Событие `player_exited` отправляется всем остальным игрокам в комнате
