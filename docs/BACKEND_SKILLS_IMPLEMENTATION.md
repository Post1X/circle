# Статус реализации навыков (Skills) на бекенде

## Анализ требований из концепции игры

### Требования к навыкам:

1. **Оплата:** Процент от текущего баланса
   - Телепорт: 15% от баланса
   - Щит: 10% от баланса
   - Ускорение: 5% от баланса

2. **Минимальный баланс:** $1 для активации любого навыка

3. **Лимит:** Максимум 5 активаций навыков на игрока за всю игру

4. **Списывание:** Деньги списываются из игры (не в бонусный фонд), но добавляются к бонусному фонду

5. **Режим "Последний шанс":**
   - В супер игре, за 3 минуты до конца (2-я минута)
   - Игрок с балансом < $5 получает бесплатный телепорт (1 раз за игру)
   - Штраф: следующий платный навык стоит +5%

---

## ❌ НЕ реализовано на бекенде:

### 1. WebSocket endpoint для активации навыка

**Текущее состояние:**
- Фронтенд отправляет: `socket.emit("activate_skill", { skill_type: skillType })`
- Ожидается событие: `skill_activated` или `skill_error`

**Что должно быть реализовано:**

#### Endpoint: `activate_skill` (WebSocket)

**Входные данные:**
```json
{
  "skill_type": "teleport" | "shield" | "boost"
}
```

**Валидация на бекенде:**

1. **Проверка авторизации:**
   - Игрок должен быть авторизован
   - Игрок должен быть в активной игре

2. **Проверка фазы игры:**
   - Игра должна быть активна
   - Игрок не должен быть выбывшим

3. **Проверка лимита активаций:**
   - Проверить что `skills_used < 5`
   - Если достигнут лимит → ошибка `skill_limit_reached`

4. **Проверка cooldown:**
   - Проверить что навык не на cooldown
   - Если на cooldown → ошибка `skill_on_cooldown`

5. **Проверка баланса:**
   - Проверить что баланс >= $1
   - Если баланс < $1 → ошибка `minimum_balance_required`

6. **Расчет стоимости:**
   - Получить текущий баланс игрока
   - Проверить флаг использования бесплатного телепорта
   - Если использован бесплатный телепорт → добавить +5% к стоимости
   - Рассчитать стоимость:
     - `teleport`: `balance * 0.15` (или `balance * 0.20` если был бесплатный)
     - `shield`: `balance * 0.10` (или `balance * 0.15` если был бесплатный)
     - `boost`: `balance * 0.05` (или `balance * 0.10` если был бесплатный)

7. **Проверка достаточности баланса:**
   - Проверить что `balance >= cost`
   - Если недостаточно → ошибка `insufficient_balance`

8. **Режим "Последний шанс":**
   - Проверить фазу игры (супер игра)
   - Проверить оставшееся время (<= 3 минуты до конца)
   - Проверить баланс игрока (< $5)
   - Проверить что бесплатный телепорт еще не использован
   - Если все условия выполнены и `skill_type === "teleport"` → стоимость = 0
   - Установить флаг использования бесплатного телепорта

9. **Списывание стоимости:**
   - Вычесть стоимость из баланса игрока
   - Добавить стоимость в бонусный фонд игры
   - Обновить счетчик использованных навыков: `skills_used += 1`

10. **Активация навыка:**
    - Применить эффект навыка (телепорт, щит, ускорение)
    - Установить cooldown для навыка
    - Отправить событие `skill_activated` всем игрокам

**Успешный ответ (`skill_activated`):**
```json
{
  "player_id": "user_123",
  "skill_type": "teleport",
  "cost": 1.5,
  "new_balance": 8.5,
  "skills_used": 1,
  "cooldowns": {
    "teleport": 60,
    "shield": 0,
    "boost": 0
  },
  "free_teleport_used": false
}
```

**Ошибки (`skill_error`):**
```json
{
  "error_code": "insufficient_balance" | "minimum_balance_required" | "skill_limit_reached" | "skill_on_cooldown" | "free_teleport_used" | "invalid_skill_type" | "game_not_active" | "player_not_in_game",
  "message": "Описание ошибки",
  "skill_type": "teleport"
}
```

---

### 2. API endpoint для получения стоимости навыка

**Текущее состояние:**
- Фронтенд вызывает: `GET /api/skills/cost/{skillType}`
- Но нет документации что должен возвращать

**Что должно быть реализовано:**

#### Endpoint: `GET /api/skills/cost/{skillType}`

**Параметры:**
- `skillType` (path) - тип навыка: "teleport", "shield", "boost"

**Headers:**
```
Authorization: Bearer {access_token}
```

**Валидация:**
- Проверка авторизации
- Проверка что игрок в активной игре
- Валидация skillType

**Response 200 OK:**
```json
{
  "skill_type": "teleport",
  "cost_percentage": 15,
  "cost_amount": 1.5,
  "current_balance": 10.0,
  "can_afford": true,
  "minimum_balance_met": true,
  "skills_remaining": 4,
  "is_free": false,
  "cooldown_remaining": 0
}
```

**Параметры ответа:**
- `skill_type` - тип навыка
- `cost_percentage` - процент от баланса (15, 10, 5)
- `cost_amount` - рассчитанная стоимость в долларах
- `current_balance` - текущий баланс игрока
- `can_afford` - достаточно ли баланса для активации
- `minimum_balance_met` - баланс >= $1
- `skills_remaining` - оставшиеся активации (5 - skills_used)
- `is_free` - доступен ли бесплатный телепорт ("Последний шанс")
- `cooldown_remaining` - оставшееся время cooldown в секундах

**Ошибки:**
- `401 Unauthorized` - не авторизован
- `400 Bad Request` - невалидный skillType
- `404 Not Found` - игрок не в игре

---

### 3. API endpoint для получения информации о навыках

**Текущее состояние:**
- Фронтенд вызывает: `GET /api/skills/info`
- Но нет документации что должен возвращать

**Что должно быть реализовано:**

#### Endpoint: `GET /api/skills/info`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response 200 OK:**
```json
{
  "skills": [
    {
      "type": "teleport",
      "name": "Телепорт",
      "description": "Мгновенное перемещение в безопасное место",
      "cost_percentage": 15,
      "cooldown": 60,
      "duration": 0
    },
    {
      "type": "shield",
      "name": "Защитный щит",
      "description": "3 секунды неуязвимости",
      "cost_percentage": 10,
      "cooldown": 30,
      "duration": 3
    },
    {
      "type": "boost",
      "name": "Ускорение",
      "description": "5 секунд повышенной скорости",
      "cost_percentage": 5,
      "cooldown": 15,
      "duration": 5
    }
  ],
  "max_uses": 5,
  "minimum_balance": 1.0,
  "last_chance": {
    "enabled": true,
    "conditions": {
      "phase": "super_game",
      "time_remaining": 180,
      "balance_threshold": 5.0
    },
    "penalty_percentage": 5
  }
}
```

---

### 4. Логика режима "Последний шанс"

**Что должно быть реализовано:**

1. **Определение условий:**
   ```python
   def is_last_chance_eligible(player, game):
       # Проверка фазы игры
       if game.phase != "super_game":
           return False
       
       # Проверка времени (за 3 минуты до конца = 2-я минута из 5)
       time_remaining = game.super_game_time_remaining
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

2. **Отслеживание использования:**
   - Флаг `free_teleport_used` в данных игрока
   - Устанавливается в `True` после использования бесплатного телепорта
   - Сохраняется на всю игру

3. **Применение штрафа:**
   - После использования бесплатного телепорта
   - Следующий платный навык стоит на 5% больше:
     - Телепорт: 15% → 20%
     - Щит: 10% → 15%
     - Ускорение: 5% → 10%

---

### 5. Интеграция с бонусным фондом

**Что должно быть реализовано:**

1. **Добавление стоимости навыков в бонусный фонд:**
   ```python
   # При активации навыка
   skill_cost = calculate_skill_cost(player, skill_type)
   player.balance -= skill_cost
   game.bonus_fund += skill_cost  # Добавляем в бонусный фонд
   ```

2. **Отслеживание в статистике:**
   - Общая сумма списанная на навыки
   - Количество активаций каждого типа навыка
   - Информация для финального распределения

---

### 6. Обновление данных игрока в реальном времени

**Что должно быть реализовано:**

1. **Отправка обновленного баланса:**
   - После активации навыка отправить обновленный баланс всем игрокам
   - Через событие `game_state` или отдельное событие `balance_updated`

2. **Отправка обновленного счетчика навыков:**
   - Обновить `skills_used` в данных игрока
   - Отправить через `leaderboard` или `game_state`

3. **Отправка cooldown:**
   - Установить cooldown для навыка
   - Отправлять оставшееся время через `game_state` или `player_data`

---

### 7. Валидация и обработка ошибок

**Что должно быть реализовано:**

1. **Все возможные ошибки:**
   - `insufficient_balance` - недостаточно баланса для активации
   - `minimum_balance_required` - баланс меньше $1
   - `skill_limit_reached` - достигнут лимит 5 активаций
   - `skill_on_cooldown` - навык еще на cooldown
   - `free_teleport_used` - бесплатный телепорт уже использован
   - `invalid_skill_type` - невалидный тип навыка
   - `game_not_active` - игра не активна
   - `player_not_in_game` - игрок не в игре
   - `not_authorized` - не авторизован

2. **Логирование:**
   - Логировать все активации навыков
   - Логировать ошибки с контекстом
   - Логировать использование бесплатного телепорта

---

### 8. Структура данных игрока

**Что должно быть в данных игрока:**

```python
class Player:
    player_id: str
    balance: float
    skills_used: int  # Счетчик использованных навыков (0-5)
    free_teleport_used: bool  # Флаг использования бесплатного телепорта
    cooldowns: {
        "teleport": int,  # Оставшееся время в секундах
        "shield": int,
        "boost": int
    }
    skill_cost_multiplier: float  # Множитель стоимости (1.0 или 1.05 после бесплатного телепорта)
```

---

## 📋 Чеклист реализации на бекенде:

### WebSocket события:
- [ ] Обработчик `activate_skill`
- [ ] Событие `skill_activated` с полными данными
- [ ] Событие `skill_error` с кодами ошибок
- [ ] Обновление `game_state` после активации навыка

### API endpoints:
- [ ] `GET /api/skills/info` - информация о навыках
- [ ] `GET /api/skills/cost/{skillType}` - стоимость навыка

### Логика:
- [ ] Расчет стоимости как процент от баланса
- [ ] Проверка минимального баланса ($1)
- [ ] Проверка лимита активаций (5)
- [ ] Проверка cooldown
- [ ] Режим "Последний шанс" (бесплатный телепорт)
- [ ] Штраф +5% после бесплатного телепорта
- [ ] Списывание стоимости из баланса
- [ ] Добавление стоимости в бонусный фонд

### Валидация:
- [ ] Проверка авторизации
- [ ] Проверка что игрок в игре
- [ ] Проверка фазы игры
- [ ] Валидация типа навыка
- [ ] Проверка достаточности баланса

### Данные:
- [ ] Хранение счетчика `skills_used`
- [ ] Хранение флага `free_teleport_used`
- [ ] Хранение cooldown для каждого навыка
- [ ] Хранение множителя стоимости

### Интеграция:
- [ ] Интеграция с бонусным фондом
- [ ] Обновление баланса в реальном времени
- [ ] Отправка обновленных данных игрокам

---

## 🔧 Пример реализации на Python (FastAPI + WebSocket):

```python
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict

class SkillService:
    SKILL_COSTS = {
        "teleport": 0.15,  # 15%
        "shield": 0.10,    # 10%
        "boost": 0.05      # 5%
    }
    
    SKILL_COOLDOWNS = {
        "teleport": 60,
        "shield": 30,
        "boost": 15
    }
    
    MINIMUM_BALANCE = 1.0
    MAX_SKILL_USES = 5
    LAST_CHANCE_TIME_RANGE = (120, 180)  # 2-3 минуты до конца
    LAST_CHANCE_BALANCE_THRESHOLD = 5.0
    PENALTY_MULTIPLIER = 1.05  # +5%
    
    async def activate_skill(
        self,
        player_id: str,
        skill_type: str,
        game: Game,
        player: Player
    ) -> Dict:
        # Валидация
        if skill_type not in self.SKILL_COSTS:
            raise ValueError("invalid_skill_type")
        
        if player.skills_used >= self.MAX_SKILL_USES:
            raise ValueError("skill_limit_reached")
        
        if player.balance < self.MINIMUM_BALANCE:
            raise ValueError("minimum_balance_required")
        
        # Проверка cooldown
        if player.cooldowns.get(skill_type, 0) > 0:
            raise ValueError("skill_on_cooldown")
        
        # Расчет стоимости
        cost_multiplier = self.PENALTY_MULTIPLIER if player.free_teleport_used else 1.0
        base_cost_percentage = self.SKILL_COSTS[skill_type]
        cost_percentage = base_cost_percentage * cost_multiplier
        
        # Режим "Последний шанс"
        is_free = False
        if (skill_type == "teleport" and 
            self._is_last_chance_eligible(player, game)):
            cost_percentage = 0
            is_free = True
            player.free_teleport_used = True
        
        cost = player.balance * cost_percentage
        
        if not is_free and player.balance < cost:
            raise ValueError("insufficient_balance")
        
        # Списывание
        player.balance -= cost
        game.bonus_fund += cost
        player.skills_used += 1
        
        # Установка cooldown
        player.cooldowns[skill_type] = self.SKILL_COOLDOWNS[skill_type]
        
        # Применение эффекта навыка
        await self._apply_skill_effect(player, skill_type)
        
        return {
            "player_id": player_id,
            "skill_type": skill_type,
            "cost": cost,
            "new_balance": player.balance,
            "skills_used": player.skills_used,
            "cooldowns": player.cooldowns,
            "free_teleport_used": player.free_teleport_used,
            "is_free": is_free
        }
    
    def _is_last_chance_eligible(self, player: Player, game: Game) -> bool:
        if game.phase != "super_game":
            return False
        
        time_remaining = game.super_game_time_remaining
        if not (self.LAST_CHANCE_TIME_RANGE[0] <= time_remaining <= self.LAST_CHANCE_TIME_RANGE[1]):
            return False
        
        if player.balance >= self.LAST_CHANCE_BALANCE_THRESHOLD:
            return False
        
        if player.free_teleport_used:
            return False
        
        return True
```

---

## Итог

**Основные проблемы:**
1. Нет обработки WebSocket события `activate_skill`
2. Нет расчета стоимости как процент от баланса
3. Нет проверки минимального баланса
4. Нет проверки лимита активаций
5. Нет режима "Последний шанс"
6. Нет штрафа после бесплатного телепорта
7. Нет списания стоимости в бонусный фонд
8. Нет API endpoints для получения стоимости и информации
9. Нет обновления данных в реальном времени

**Приоритет реализации:**
1. Высокий: WebSocket обработчик, расчет стоимости, списание баланса
2. Средний: Лимиты, валидация, API endpoints
3. Низкий: Режим "Последний шанс", штрафы, улучшения UX

