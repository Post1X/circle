## Интеграция фронтенда с realtime‑игрой

Этот документ описывает, как фронтенду работать с сокет‑ивентами игры, вести локальную игровую логику (поедание еды и рост игроков) и как отправлять итоговые результаты матча на бэкенд.

---

## 1. Общие принципы

- **Истина по состоянию матча (фазы, зона, список игроков, сессия)** — на бэке.
- **Локальная игровая механика (поедание еды, рост, визуальный счёт)** — на фронте.
- **Деньги и статистика в БД** — обновляются на бэке по одному клиентскому отчёту `match_result_report` на игрока.

---

## 2. Основные сокет‑ивенты

Используется namespace `'/'`, все ивенты идут через `RoomsGateway`.

### 2.1. Аутентификация

- **Событие:** `authenticate`
- **Payload (от фронта):**

```json
{
  "user_id": "uuid-пользователя"
}
```

- **Ответы:**
  - `authenticated` `{ user_id, wallet_address, username }`
  - `auth_error` `{ message }`

Фронт **обязан** успешно пройти `authenticate`, прежде чем создавать/входить в комнату и отправлять `match_result_report`.

### 2.2. Вход в игру

Вариант 1 — автоматический подбор комнаты:

- **Событие:** `join_game`
- **Payload (от фронта):**

```json
{
  "entry_fee": 0,
  "min_players": 1,
  "max_players": 50
}
```

Бэк найдёт подходящую комнату или создаст новую.

Вариант 2 — вход в конкретную комнату:

- **Событие:** `join_room`
- **Payload:**

```json
{
  "room_id": "uuid-комнаты"
}
```

### 2.3. Ответы по комнатам

- `joined_room`:

```json
{
  "players": [
    { "user_id": "…", "username": "…" }
  ],
  "room_id": "uuid-комнаты",
  "message": "Successfully joined room",
  "time_to_start": 30 | null
}
```

- При достижении минимального количества игроков:

  - `game_started`:

  ```json
  {
    "time_to_start": 30,
    "players": [
      { "user_id": "…", "username": "…", "avatar_url": "…" }
    ]
  }
  ```

После `game_started` через ~30 секунд запустится игровой цикл и начнут приходить `game_state`.

---

## 3. `game_state`: данные для рендера и логики фронта

- **Событие:** `game_state`
- **Направление:** бэк → фронт

Структура упрощённо (важные поля):

```json
{
  "map_info": {
    "radius": 1200,
    "player_count": 10,
    "expected_players": 50
  },
  "safe_zone": {
    "x": 0,
    "y": 0,
    "radius": 800,
    "scale": 0.75,
    "damage_per_second": 2,
    "time_to_next_shrink": 30,
    "game_time": 123.4
  },
  "foods": [
    { "x": 100, "y": -50, "mass": 2, "color": [255, 215, 0] }
  ],
  "players": [
    {
      "some-player-id-uuid": {
        "x": 10,
        "y": -20,
        "mass": 7.5,
        "money": 0,
        "color": [120, 200, 80],
        "shield_active": false,
        "speed_boost_active": false,
        "skills_used": 0,
        "zone_damage_taken": 1,
        "in_bonus_zone": false,
        "bonus_multiplier": 1,
        "outside_zone": true,
        "bonus_zone_collected": 0,
        "cooldowns": { "teleport": 0, "shield": 0, "boost": 0 },
        "username": "Player_1234",
        "teleport_effect_time": null,
        "shield_end_time": null,
        "speed_boost_end_time": null
      }
    }
  ],
  "game_phase": {
    "phase": "start" | "top10" | "super" | "finished",
    "voting_time_remaining": 12.3,
    "votes_submitted": 0,
    "votes_exit": 0,
    "votes_super": 0,
    "super_game_time_remaining": 0,
    "skill_costs_increased": false
  },
  "zone_fund": 200,
  "bonus_fund": 0
}
```

### 3.1. Что фронт **обязан** использовать из `game_state`

- `map_info.radius` — логический размер карты.
- `players[].x/y` — **логические координаты** игрока (одна система с едой, не экран!).
- `players[].mass` — серверный радиус игрока (можно использовать как базу).
- `foods[].x/y/mass` — логические координаты и размер еды.
- `game_phase.phase`, `safe_zone` и прочее — для UI фаз игры, зоны, индикаторов.

---

## 4. Игровая логика на фронте (поедание еды)

### 4.1. Локальное состояние HUD

Рекомендуется держать на фронте отдельное состояние:

- `clientPlayers[playerId]`:
  - `x, y` — можно брать из `game_state`, интерполировать при отрисовке.
  - `mass` — локальный радиус (для визуала), инициализировать `serverMass = gameState.mass`.
  - `money` — локальный счёт (для HUD).
- `clientFoods[]`:
  - копия `game_state.foods`;
  - флаг `eaten`/`visible` для локально съеденных шариков.

### 4.2. Алгоритм коллизий (фронт)

Псевдокод на каждый кадр или тик обновления:

```ts
for each player in clientPlayers:
  for each food in clientFoods:
    if food.eaten: continue

    const dx = player.x - food.x
    const dy = player.y - food.y
    const distance = Math.sqrt(dx*dx + dy*dy)

    const playerRadius = player.mass           // или server mass, или своя кривая
    const foodRadius = Math.max(1, food.mass)  // можно задать минимум

    if (distance <= playerRadius + foodRadius):
      food.eaten = true
      // визуальный рост/очки:
      const foodValue = food.mass
      player.money += foodValue / 20
      player.mass = calcRadiusFromMoney(player.money)
```

`calcRadiusFromMoney` можно взять по аналогии с серверным `get_radius`:

```ts
function calcRadiusFromMoney(money: number): number {
  if (money <= 0) return 5.0
  const mass = 5 + Math.log(money + 1) * 8
  return Math.min(100, Math.max(5, mass))
}
```

### 4.3. Спавн новой еды

При желании фронт может сам добавлять новую еду при поедании:

```ts
if (food.eaten) {
  clientFoods.push(randomFood(mapRadius))
}
```

Важно: логика спавна на бэке остаётся, но фронт может скрывать/добавлять еду локально для плотности, ориентируясь на `foods` из `game_state` как на базовый «слой» карты.

---

## 5. Завершение игры и `match_result_report`

### 5.1. Ивент `game_finished`

- **Событие:** `game_finished`
- **От бэка в комнату**, когда фаза игры становится `finished`.

Пример payload:

```json
{
  "early_exits": { "playerId1": 10.5 },
  "super_exits": { "playerId2": 5.0 },
  "finalists": ["playerId3", "playerId4"],
  "bonus_fund": 123.45,
  "zone_fund": 200,
  "final_winnings": {
    "playerId3": 50.0,
    "playerId4": 30.0
  }
}
```

Фронт использует это для экрана результатов, но **итоговую экономику и стату для конкретного игрока он формирует сам**.

### 5.2. Ивент `match_result_report` (фронт → бэк)

- **Событие:** `match_result_report`
- **Когда слать:** один раз на игрока, после получения `game_finished` и расчёта своих итогов.

#### Payload

```json
{
  "room_id": "uuid-комнаты",
  "final_winnings": 42.5,
  "final_rank": 1,
  "exit_type": "final",
  "stats": {
    "skills_used": 3,
    "free_teleport_used": true,
    "bonus_zone_collected": 5,
    "outside_zone_damage": 12.5,
    "teleport_uses": 1,
    "shield_uses": 1,
    "boost_uses": 1,
    "skills_cost_total": 7.5
  }
}
```

- `room_id` — должен совпадать с текущей комнатой игрока.
- `final_winnings` — сколько игрок реально заработал по твоей клиентской логике.
- `final_rank` — место игрока (1 — победитель), можно `null`.
- `exit_type`:
  - `'final'` — нормальное завершение игры.
  - `'early'` / `'super'` — если игрок вышел через механики выхода.
  - `'death'` — если игрок погиб и матч закончился не его победой.

#### Ответы от бэка

- При успехе:

```json
{
  "room_id": "uuid-комнаты",
  "final_winnings": 42.5,
  "final_rank": 1,
  "exit_type": "final"
}
```

Ивент: `match_result_accepted`.

- При ошибке:

```json
{ "message": "Authentication required" }
```

Ивент: `match_result_error`.

#### Что делает бэк

1. Валидация:
   - пользователь аутентифицирован и в этой комнате;
   - `exit_type` один из `'final' | 'early' | 'super' | 'death'`;
   - `final_winnings >= 0`;
   - есть `stats`.
2. Вызывает:
   - `GameStatsService.savePlayerGameStatsFromData()` → пишет все переданные статы в `game_player_stats` и обновляет `User.games_played` / `User.total_winnings`.
3. Если `final_winnings > 0`:
   - вызывает `WithdrawalService.creditUserBalance(userId, finalWinnings)` → начисляет выигрыш на баланс.

---

## 6. Типичный фронтовый флоу

1. Подключаемся к сокету, делаем `authenticate`.
2. Делаем `join_game` или `join_room`.
3. Слушаем:
   - `joined_room` → запоминаем `room_id`.
   - `game_started` → запускаем локальный игровой цикл (рендер, HUD).
   - `game_state` → обновляем карту/позиции, используем как источник данных.
4. В локальном стейте:
   - считаем коллизии игрок–еда;
   - обновляем свои `clientMoney`, `clientMass`, счётчики скиллов и т.д.
5. Когда приходит `game_finished`:
   - показываем экран результатов;
   - формируем свой объект результатов для текущего игрока.
6. Отправляем:

```ts
socket.emit('match_result_report', payload);
```

7. Ждём:
   - `match_result_accepted` → можно считать матч корректно сохранённым и деньги начисленными.
   - в случае `match_result_error` → показываем пользователю ошибку или пробуем ретрай.

---

## 7. Замечания по безопасности

- Бэк всё равно валидирует:
  - аутентификацию;
  - принадлежность к комнате;
  - типы/диапазоны значений.
- Но финальная сумма `final_winnings` и статистика **доверяются фронту**.  
  Если понадобится защита от читов, можно:
  - сохранять параллельно rough‑метрики на бэке и сравнивать с клиентскими;
  - вводить лимиты/аномалийные проверки (`final_winnings` не больше фонда комнаты и т.д.).

