# Система навыков (Skills) - Документация

## Обзор

Система навыков позволяет игрокам использовать специальные способности во время игры за процент от текущего баланса. Все данные о использовании скиллов сохраняются для аналитики и статистики.

## Архитектура

### Компоненты системы

1. **Player класс** (`src/game/player.ts`) - хранит состояние игрока в памяти
2. **Game класс** (`src/game/game.ts`) - управляет логикой игры и активацией скиллов
3. **RoomsGateway** (`src/modules/rooms/rooms.gateway.ts`) - WebSocket обработчик
4. **SkillsService** (`src/modules/skills/skills.service.ts`) - API для получения информации о скиллах
5. **SkillStatsService** (`src/services/skill-stats/skill-stats.service.ts`) - сохранение статистики в Redis
6. **GameStatsService** (`src/services/game-stats/game-stats.service.ts`) - сохранение итоговой статистики в БД
7. **GameTrackerService** (`src/services/game-tracker/game-tracker.service.ts`) - отслеживание игроков в игре

## Типы навыков

### 1. Телепорт (Teleport)
- **Стоимость**: 15% от баланса (20% после бесплатного телепорта)
- **Cooldown**: 60 секунд
- **Эффект**: Мгновенное перемещение в случайное безопасное место
- **Длительность эффекта**: 1 секунда

### 2. Защитный щит (Shield)
- **Стоимость**: 10% от баланса (15% после бесплатного телепорта)
- **Cooldown**: 30 секунд
- **Эффект**: 3 секунды неуязвимости
- **Длительность эффекта**: 3 секунды

### 3. Ускорение (Boost)
- **Стоимость**: 5% от баланса (10% после бесплатного телепорта)
- **Cooldown**: 15 секунд
- **Эффект**: 5 секунд повышенной скорости (x2)
- **Длительность эффекта**: 5 секунд

## Правила использования

### Ограничения

1. **Минимальный баланс**: $1 для активации любого навыка
2. **Лимит активаций**: Максимум 5 использований навыков за игру
3. **Cooldown**: Каждый навык имеет свой период восстановления
4. **Достаточность баланса**: Баланс должен быть >= стоимости навыка

### Режим "Последний шанс"

**Условия активации:**
- Фаза игры: `super_game`
- Время до конца: 2-3 минуты (120-180 секунд)
- Баланс игрока: < $5
- Бесплатный телепорт еще не использован
- Тип навыка: `teleport`

**Эффект:**
- Телепорт становится бесплатным (стоимость = 0)
- Устанавливается флаг `free_teleport_used = true`
- Следующие платные навыки стоят на 5% больше

## Поток данных

### 1. Активация навыка (WebSocket)

```
Клиент → WebSocket: activate_skill
  ↓
RoomsGateway.handleActivateSkill()
  ↓
Game.activate_skill()
  ├─ Проверка условий (баланс, лимит, cooldown)
  ├─ Расчет стоимости
  ├─ Проверка "Последний шанс"
  ├─ Списывание баланса
  ├─ Добавление в bonus_fund
  ├─ Активация эффекта
  └─ Обновление счетчиков
  ↓
SkillStatsService.recordSkillUsage() → Redis
  ↓
Отправка событий клиентам
```

### 2. Сохранение статистики

#### В момент использования (Redis)
```typescript
SkillStatsService.recordSkillUsage()
  → Redis: skill_stats:{sessionId}:{userId}
  → Данные: { skill_type, cost, balance_before, balance_after, is_free, created_at }
```

#### После окончания игры (БД)
```typescript
GameStatsService.savePlayerGameStats()
  ├─ Получение статистики из Redis
  ├─ Подсчет использования каждого типа скилла
  ├─ Сохранение в game_player_stats
  └─ Обновление user (games_played++, total_winnings)
```

## Структура базы данных

### Таблица: `skill_usage`

Детальная статистика каждого использования навыка.

```sql
CREATE TABLE skill_usage (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL,
  session_id UUID NOT NULL,
  skill_type VARCHAR(20) NOT NULL,
  cost DECIMAL(18,6) NOT NULL,
  balance_before DECIMAL(18,6) NOT NULL,
  balance_after DECIMAL(18,6) NOT NULL,
  is_free BOOLEAN DEFAULT false,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES user(user_id),
  FOREIGN KEY (session_id) REFERENCES game_session(session_id)
);
```

**Назначение**: Аналитика использования навыков, паттерны поведения игроков.

### Таблица: `game_player_stats`

Итоговая статистика игрока за игру.

```sql
CREATE TABLE game_player_stats (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL,
  session_id UUID NOT NULL,
  skills_used_total INT DEFAULT 0,
  skills_cost_total DECIMAL(18,6) DEFAULT 0,
  final_winnings DECIMAL(18,6) DEFAULT 0,
  final_rank INT,
  game_duration_seconds INT DEFAULT 0,
  exit_type VARCHAR(20) NOT NULL,
  teleport_uses INT DEFAULT 0,
  shield_uses INT DEFAULT 0,
  boost_uses INT DEFAULT 0,
  free_teleport_used BOOLEAN DEFAULT false,
  bonus_zone_collected DECIMAL(18,6) DEFAULT 0,
  outside_zone_damage DECIMAL(18,6) DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES user(user_id),
  FOREIGN KEY (session_id) REFERENCES game_session(session_id)
);
```

**Назначение**: История игр игрока, статистика по играм.

**Типы выхода (`exit_type`):**
- `early` - ранний выход (фаза START)
- `super` - выход из супер игры (фаза SUPER)
- `death` - смерть в игре (столкновение или деньги = 0)
- `final` - финалист (игра завершена)

## Redis структура

### Ключи для статистики скиллов

```
skill_stats:{sessionId}:{userId}
  → Массив объектов использования скиллов
  → TTL: 86400 секунд (24 часа)

skill_stats:{sessionId}:keys
  → Массив ключей для быстрого доступа
  → TTL: 86400 секунд
```

### Ключи для отслеживания игроков

```
player:room:{userId}
  → roomId (ID комнаты/сессии)
  → TTL: 3600 секунд (1 час)

room:players:{roomId}
  → Set пользователей в комнате
  → TTL: 3600 секунд
```

## API Endpoints

### GET `/api/skills/info`

Получить информацию о всех навыках.

**Ответ:**
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

**Кэширование**: Redis, TTL 1 час

### GET `/api/skills/cost/:skill_type`

Получить стоимость навыка для текущего игрока.

**Требования:**
- Авторизация: JWT токен
- Игрок должен быть в активной игре (опционально)

**Параметры:**
- `skill_type` - тип навыка: `teleport`, `shield`, `boost`

**Ответ:**
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

**Логика:**
1. Если игрок в игре → данные из игры (актуальные)
2. Если игрок не в игре → данные из БД пользователя (баланс)

## WebSocket события

### Отправка: `activate_skill`

Активировать навык.

**Данные:**
```json
{
  "skill_type": "teleport" | "shield" | "boost"
}
```

**Валидация:**
1. Игрок авторизован
2. Игрок в активной игре
3. Игра активна (не END)
4. Игрок не выбыл (`to_remove = false`)
5. Баланс >= $1
6. Лимит не достигнут (`skills_used < 5`)
7. Навык не на cooldown
8. Баланс >= стоимости

**Обработка:**
1. Проверка режима "Последний шанс"
2. Расчет стоимости (с учетом штрафа)
3. Списывание баланса
4. Добавление в `bonus_fund`
5. Активация эффекта
6. Установка cooldown
7. Увеличение `skills_used`
8. Сохранение в Redis
9. Отправка событий

### Получение: `skill_activated`

Успешная активация навыка.

**Данные:**
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

### Получение: `skill_error`

Ошибка активации навыка.

**Данные:**
```json
{
  "error_code": "insufficient_balance" | "minimum_balance_required" | "skill_limit_reached" | "skill_on_cooldown" | "free_teleport_used" | "invalid_skill_type" | "game_not_active" | "player_not_in_game",
  "message": "Описание ошибки",
  "skill_type": "teleport"
}
```

**Коды ошибок:**
- `minimum_balance_required` - баланс < $1
- `skill_limit_reached` - достигнут лимит 5 активаций
- `skill_on_cooldown` - навык на cooldown
- `insufficient_balance` - недостаточно баланса для активации
- `player_not_in_game` - игрок не в игре
- `game_not_active` - игра не активна
- `invalid_skill_type` - невалидный тип навыка
- `free_teleport_used` - бесплатный телепорт уже использован

### Получение: `player_used_skill`

Уведомление всем игрокам о использовании навыка.

**Данные:**
```json
{
  "player_id": "user_123",
  "skill_type": "teleport"
}
```

### Получение: `game_state`

Обновленное состояние игры (включая балансы игроков).

**Отправляется:** Всем игрокам в комнате после активации навыка

## Сохранение данных

### Момент использования (Redis)

При каждом использовании навыка данные сохраняются в Redis:

```typescript
await skillStatsService.recordSkillUsage(
  userId,
  sessionId,
  skillType,
  cost,
  balanceBefore,
  balanceAfter,
  isFree,
);
```

**Структура данных в Redis:**
```json
[
  {
    "user_id": "user_123",
    "session_id": "session_456",
    "skill_type": "teleport",
    "cost": 1.5,
    "balance_before": 10.0,
    "balance_after": 8.5,
    "is_free": false,
    "created_at": "2026-01-07T17:00:00.000Z"
  }
]
```

### После окончания игры (БД)

Статистика сохраняется в БД в следующих случаях:

#### 1. Ранний выход (`exit_game` с `exit_type: "early"`)
```typescript
await gameStatsService.savePlayerGameStats(
  userId,
  sessionId,
  player,
  'early',
  gameStartTime,
  null,
);
```

#### 2. Выход из супер игры (`exit_game` с `exit_type: "super"`)
```typescript
await gameStatsService.savePlayerGameStats(
  userId,
  sessionId,
  player,
  'super',
  gameStartTime,
  null,
);
```

#### 3. Смерть в игре (`to_remove = true`)
```typescript
// В игровом цикле после game.update()
await gameStatsService.savePlayerGameStats(
  playerId,
  roomId,
  removedPlayer,
  'death',
  gameStartTime,
  null,
);
```

#### 4. Финалист (игра завершена)
```typescript
await gameStatsService.savePlayerGameStats(
  playerId,
  roomId,
  player,
  'final',
  gameStartTime,
  finalRank, // 1, 2, 3, ...
);
```

### Обновление статистики пользователя

При сохранении статистики автоматически обновляется:

```typescript
user.games_played += 1;
user.total_winnings += final_winnings;
```

## Состояние игрока (Player класс)

### Поля, обнуляющиеся каждую игру

```typescript
player.reset_for_new_game() {
  skills_used = 0;
  free_teleport_used = false;
  
  shield_active = false;
  shield_end_time = 0;
  speed_boost_active = false;
  speed_boost_end_time = 0;
  teleport_effect_time = 0;
  
  teleport_cooldown = 0;
  shield_cooldown = 0;
  boost_cooldown = 0;
  
  outside_zone_damage = 0;
  last_zone_damage_time = 0;
  
  in_bonus_zone = false;
  current_bonus_multiplier = 1;
  bonus_zone_collected = 0;
  
  final_winnings = 0;
  target_x = null;
  target_y = null;
  to_remove = false;
}
```

### Поля, сохраняющиеся между играми

- `money` - устанавливается при старте игры
- `x, y` - позиция (устанавливается при старте)
- `username, color, player_id` - постоянные данные

## Расчет стоимости

### Базовая стоимость

```typescript
const baseCosts = {
  teleport: 0.15,  // 15%
  shield: 0.10,   // 10%
  boost: 0.05     // 5%
};
```

### С учетом штрафа

Если использован бесплатный телепорт (`free_teleport_used = true`):

```typescript
const costPercentage = baseCosts[skillType] + 0.05; // +5%
```

### Финальная стоимость

```typescript
const costAmount = player.money * costPercentage;
```

## Интеграция с бонусным фондом

При активации навыка:

```typescript
player.money -= cost;
game.bonus_fund += cost;
```

**Важно**: Стоимость навыков добавляется в бонусный фонд игры и распределяется между финалистами.

## Отслеживание игроков в игре

### GameTrackerService

Отслеживает, какие игроки находятся в каких играх:

```typescript
// При старте игры
await gameTrackerService.setPlayerInRoom(userId, roomId);

// При выходе/смерти
await gameTrackerService.removePlayerFromRoom(userId, roomId);

// Проверка
const roomId = await gameTrackerService.getPlayerRoom(userId);
const isInGame = await gameTrackerService.isPlayerInGame(userId);
```

**Использование:**
- Определение, в игре ли игрок для API `/api/skills/cost`
- Получение актуальных данных из игры вместо БД

## Примеры использования

### Пример 1: Активация телепорта

```
1. Игрок отправляет: { "skill_type": "teleport" }
2. Проверка: баланс = $10, skills_used = 0, cooldown = 0
3. Расчет: cost = $10 * 0.15 = $1.5
4. Списывание: balance = $10 - $1.5 = $8.5
5. Добавление: bonus_fund += $1.5
6. Активация: телепорт в случайное место
7. Cooldown: teleport_cooldown = 60
8. Счетчик: skills_used = 1
9. Сохранение в Redis
10. Отправка событий
```

### Пример 2: Режим "Последний шанс"

```
1. Фаза: super_game
2. Время до конца: 150 секунд (в диапазоне 120-180)
3. Баланс: $3 (< $5)
4. free_teleport_used: false
5. Навык: teleport
6. Результат: cost = 0 (бесплатно)
7. free_teleport_used = true
8. Следующий навык: +5% к стоимости
```

### Пример 3: Сохранение статистики

```
1. Игрок выходит из игры (exit_type: "super")
2. Получение статистики из Redis
3. Подсчет: teleport_uses = 2, shield_uses = 1, boost_uses = 0
4. Расчет: skills_cost_total = $1.5 + $1.0 + $0.5 = $3.0
5. Сохранение в game_player_stats
6. Обновление user: games_played++, total_winnings += winnings
```

## Производительность

### Оптимизации

1. **Redis для частых операций**
   - Статистика использования скиллов хранится в Redis
   - Батч-запись в БД после окончания игры
   - Не нагружает БД во время игры

2. **Кэширование**
   - `/api/skills/info` кэшируется в Redis (TTL 1 час)
   - Статическая информация не запрашивается из БД

3. **Отслеживание игроков**
   - Маппинг `userId -> roomId` в Redis
   - Быстрый доступ O(1) для определения, в игре ли игрок

### Масштабируемость

- Redis позволяет работать с несколькими инстансами сервера
- Статистика в Redis автоматически очищается через TTL
- БД используется только для финальной статистики

## Логирование

Все операции логируются через Winston:

- Активация навыков
- Ошибки активации
- Сохранение статистики
- Использование бесплатного телепорта

## Миграции

Для применения миграций:

```bash
python -m alembic upgrade head
```

**Миграции:**
- `2026_01_07_0000` - создание таблицы `skill_usage`
- `2026_01_07_0001` - создание таблицы `game_player_stats`

## Тестирование

### Проверка активации навыка

1. Создать игрока с балансом > $1
2. Отправить `activate_skill` с валидным типом
3. Проверить списание баланса
4. Проверить добавление в bonus_fund
5. Проверить сохранение в Redis
6. Проверить отправку событий

### Проверка сохранения статистики

1. Завершить игру (выход/смерть/финал)
2. Проверить сохранение в `game_player_stats`
3. Проверить обновление `user.games_played`
4. Проверить обновление `user.total_winnings`

## Troubleshooting

### Проблема: Навык не активируется

**Проверка:**
1. Баланс >= $1?
2. Лимит не достигнут?
3. Cooldown истек?
4. Игрок в игре?
5. Игра активна?

### Проблема: Статистика не сохраняется

**Проверка:**
1. Redis доступен?
2. БД доступна?
3. Миграции применены?
4. Логи ошибок?

### Проблема: Неправильная стоимость

**Проверка:**
1. Использован бесплатный телепорт?
2. Баланс актуален?
3. Правильный тип навыка?

