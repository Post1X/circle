# Socket.IO API для фронтенда

Документация по всем Socket.IO событиям, которые поддерживает бэкенд на NestJS.

## Подключение

```javascript
import { io } from 'socket.io-client';

const socket = io('http://93.183.106.254:8000', {
  transports: ['websocket', 'polling'],
  reconnection: true,
  reconnectionDelay: 1000,
  reconnectionAttempts: 5,
});
```

## События подключения/отключения

### `connect`
Автоматически вызывается при успешном подключении.

**Ответ от сервера:**
```json
{
  "sid": "socket-session-id"
}
```

**Пример:**
```javascript
socket.on('connect', (data) => {
  console.log('Connected:', data.sid);
});
```

### `disconnect`
Вызывается при отключении от сервера.

**Пример:**
```javascript
socket.on('disconnect', (reason) => {
  console.log('Disconnected:', reason);
});
```

### `connected`
Сервер отправляет это событие сразу после подключения.

**Данные:**
```json
{
  "sid": "socket-session-id"
}
```

---

## Аутентификация

### Отправить: `authenticate`

**Формат:**
```javascript
socket.emit('authenticate', {
  user_id: 'uuid-пользователя'
});
```

**Ответы:**

**Успех: `authenticated`**
```json
{
  "user_id": "uuid",
  "wallet_address": "T...",
  "username": "sasha"
}
```

**Ошибка: `auth_error`**
```json
{
  "message": "User not found"
}
```

**Пример:**
```javascript
socket.emit('authenticate', { user_id: '4c6762a2-16db-4008-b443-730951858ea5' });

socket.on('authenticated', (data) => {
  console.log('Authenticated:', data.username);
});

socket.on('auth_error', (error) => {
  console.error('Auth error:', error.message);
});
```

---

## Комнаты и матчмейкинг

### Отправить: `join_game` ⭐ (Рекомендуется)

Автоматически находит свободную комнату или создаёт новую, затем подключает игрока.

**Формат:**
```javascript
socket.emit('join_game', {
  entry_fee: 0,        // Вступительный взнос (по умолчанию 0)
  min_players: 1,      // Минимум игроков для старта (по умолчанию 1)
  max_players: 100     // Максимум игроков (по умолчанию 50)
});
```

**Ответы:**

**Успех: `joined_room`**
```json
{
  "players": [
    {
      "user_id": "uuid",
      "username": "sasha"
    }
  ],
  "room_id": "uuid-комнаты",
  "message": "Successfully joined room",
  "time_to_start": 30  // null, если игроков недостаточно
}
```

**Ошибка: `error`**
```json
{
  "message": "Authentication required"
}
```

**Важно:** Сохрани `room_id` из `joined_room` для реконнектов и дальнейших операций!

**Пример:**
```javascript
let currentRoomId = null;

socket.emit('join_game', {
  entry_fee: 0,
  min_players: 1,
  max_players: 100
});

socket.on('joined_room', (data) => {
  currentRoomId = data.room_id;
  console.log('Joined room:', data.room_id);
  console.log('Players:', data.players);
  if (data.time_to_start) {
    console.log('Game starts in:', data.time_to_start, 'seconds');
  }
});
```

### Отправить: `create_room`

Создаёт новую комнату (обычно не нужно, используй `join_game`).

**Формат:**
```javascript
socket.emit('create_room', {
  entry_fee: 0,
  min_players: 2,
  max_players: 50
});
```

**Ответ: `room_created`**
```json
{
  "room_id": "uuid",
  "entry_fee": 0,
  "min_players": 2,
  "max_players": 50,
  "status": "waiting",
  "created_at": "2026-01-14T20:55:02.233Z"
}
```

### Отправить: `join_room`

Подключиться к конкретной комнате по `room_id` (для реконнектов).

**Формат:**
```javascript
socket.emit('join_room', {
  room_id: 'uuid-комнаты'
});
```

**Ответы:** Те же, что у `join_game` (`joined_room` или `error`).

### Отправить: `leave_room`

Выйти из комнаты.

**Формат:**
```javascript
socket.emit('leave_room', {
  room_id: 'uuid-комнаты'
});
```

**Ответ: `left_room`**
```json
{
  "room_id": "uuid",
  "message": "Successfully left room"
}
```

### Отправить: `get_rooms`

Получить список всех доступных комнат.

**Формат:**
```javascript
socket.emit('get_rooms');
```

**Ответ: `rooms_list`**
```json
{
  "rooms": [
    {
      "room_id": "uuid",
      "entry_fee": 0,
      "min_players": 1,
      "max_players": 100,
      "status": "waiting",
      "created_at": "2026-01-14T20:55:02.233Z"
    }
  ]
}
```

---

## Игровые события

### `game_started`

Игра скоро начнётся (когда набралось достаточно игроков).

**Данные:**
```json
{
  "time_to_start": 30
}
```

**Пример:**
```javascript
socket.on('game_started', (data) => {
  console.log('Game starts in:', data.time_to_start, 'seconds');
  // Покажи таймер обратного отсчёта
});
```

### `game_state`

Текущее состояние игры (отправляется регулярно в игровом цикле).

**Данные:**
```json
{
  "map_info": {
    "radius": 400,
    "player_count": 10,
    "expected_players": 50
  },
  "safe_zone": {
    "x": 0,
    "y": 0,
    "radius": 320,
    "scale": 0.8,
    "damage_per_second": 2.5,
    "time_to_next_shrink": 45.2,
    "game_time": 120.5
  },
  "players": [
    {
      "player-id": {
        "x": 150,
        "y": 200,
        "mass": 25.5,
        "money": 50.3,
        "color": [255, 100, 50],
        "shield_active": false,
        "speed_boost_active": false,
        "skills_used": 2,
        "in_bonus_zone": false,
        "bonus_multiplier": 1,
        "cooldowns": {
          "teleport": 45.2,
          "shield": 0,
          "boost": 10.5
        },
        "username": "sasha"
      }
    }
  ],
  "foods": [
    {
      "x": 100,
      "y": 150,
      "mass": 2,
      "color": [255, 255, 0]
    }
  ],
  "bonus_zones": [
    {
      "x": 200,
      "y": 300,
      "radius": 80,
      "multiplier": 2,
      "remaining_time": 25.5,
      "funds_collected": 50,
      "max_funds": 40
    }
  ],
  "game_phase": {
    "phase": "start"
  },
  "zone_fund": 100,
  "bonus_fund": 500
}
```

**Пример:**
```javascript
socket.on('game_state', (state) => {
  // Обновляй игровое поле, позиции игроков, еду, зоны
  renderGame(state);
});
```

### `leaderboard`

Лидерборд игры (отправляется автоматически раз в 10 секунд + по запросу).

**Данные:**
```json
{
  "current_players": [
    {
      "player_id": "uuid",
      "mass": 25.5,
      "x": 150,
      "y": 200,
      "r": 255,
      "g": 100,
      "b": 50,
      "skills_used": 2,
      "bonus_zone_collected": 5,
      "outside_zone_damage": 10.5,
      "in_bonus_zone": false,
      "bonus_multiplier": 1,
      "rank": 1,
      "username": "sasha"
    }
  ],
  "total_players": 10,
  "game_phase": {
    "phase": "start",
    "players_count": 10,
    "bonus_fund": 500,
    "zone_fund": 100
  },
  "game_time": 120.5,
  "safe_zone_scale": 0.8,
  "zone_fund": 100,
  "bonus_fund": 500,
  "early_exits": [
    {
      "player_id": "uuid",
      "winnings": 50.5,
      "exit_type": "early",
      "percentage": 50
    }
  ],
  "super_exits": [...],
  "finalists": [...]
}
```

**Пример:**
```javascript
socket.on('leaderboard', (leaderboard) => {
  // Обновляй таблицу лидеров
  updateLeaderboard(leaderboard.current_players);
});
```

### Отправить: `get_leaderboard`

Запросить актуальный лидерборд вручную.

**Формат:**
```javascript
socket.emit('get_leaderboard');
```

**Ответы:**

**Успех: `leaderboard`** (та же структура, что выше)

**Ошибка: `leaderboard_error`**
```json
{
  "message": "Not in game"
}
```

---

## Движение и управление

### Отправить: `move`

Отправить движение игрока.

**Формат:**
```javascript
socket.emit('move', {
  dx: 5,   // Смещение по X (-5 до 5)
  dy: -3   // Смещение по Y (-5 до 5)
});
```

**Ответ:** Нет (движение применяется на сервере, обновления приходят через `game_state`).

**Пример:**
```javascript
// При нажатии клавиш
document.addEventListener('keydown', (e) => {
  let dx = 0, dy = 0;
  if (e.key === 'ArrowLeft') dx = -5;
  if (e.key === 'ArrowRight') dx = 5;
  if (e.key === 'ArrowUp') dy = -5;
  if (e.key === 'ArrowDown') dy = 5;
  
  if (dx !== 0 || dy !== 0) {
    socket.emit('move', { dx, dy });
  }
});
```

---

## Скиллы

### Отправить: `activate_skill`

Активировать навык (телепорт, щит, ускорение).

**Формат:**
```javascript
socket.emit('activate_skill', {
  skill_type: 'teleport'  // 'teleport' | 'shield' | 'boost'
});
```

**Ответы:**

**Успех: `skill_activated`**
```json
{
  "player_id": "uuid",
  "skill_type": "teleport",
  "cost": 0,              // Сейчас скиллы бесплатные
  "new_balance": 50.3,
  "skills_used": 3,
  "cooldowns": {
    "teleport": 60.0,
    "shield": 0,
    "boost": 0
  },
  "free_teleport_used": false,
  "new_position": {        // Только для teleport
    "x": 250,
    "y": 300
  },
  "shield_active": true,   // Только для shield
  "shield_duration": 3,   // Только для shield
  "is_last_chance": false  // Только для teleport в last_chance
}
```

**Ошибка: `skill_error`**
```json
{
  "error_code": "skill_on_cooldown",
  "message": "Skill is on cooldown",
  "skill_type": "teleport"
}
```

**Возможные коды ошибок:**
- `minimum_balance_required` - Минимум $1 нужен для скиллов
- `skill_limit_reached` - Достигнут лимит (5 скиллов за игру)
- `skill_on_cooldown` - Скилл на кулдауне
- `insufficient_balance` - Недостаточно баланса
- `player_not_in_game` - Игрок не в игре
- `game_not_active` - Игра не активна
- `invalid_skill_type` - Неверный тип скилла

**Пример:**
```javascript
socket.emit('activate_skill', { skill_type: 'teleport' });

socket.on('skill_activated', (data) => {
  console.log('Skill activated:', data.skill_type);
  if (data.new_position) {
    console.log('Teleported to:', data.new_position);
  }
  updateCooldowns(data.cooldowns);
});

socket.on('skill_error', (error) => {
  console.error('Skill error:', error.message);
});
```

### `player_used_skill`

Уведомление о том, что кто-то использовал скилл (для всех в комнате).

**Данные:**
```json
{
  "player_id": "uuid",
  "skill_type": "teleport"
}
```

### `last_chance_activated`

Активирован "последний шанс" в супер-игре (бесплатный телепорт).

**Данные:**
```json
{
  "player_id": "uuid",
  "skill_costs_increased": false
}
```

### Отправить: `request_last_chance`

Запросить "последний шанс" в супер-игре.

**Формат:**
```javascript
socket.emit('request_last_chance');
```

**Ответы:**

**Успех: `last_chance_activated`** (отправляется всем в комнате)

**Ошибка: `last_chance_error`**
```json
{
  "message": "Cannot activate last chance"
}
```

---

## Фазы игры

### `phase_changed`

Смена фазы игры.

**Данные:**

**Фаза "top10":**
```json
{
  "new_phase": "top10",
  "voting_time_remaining": 30.0,
  "message": "Голосование в топ-10 началось!"
}
```

**Фаза "super":**
```json
{
  "new_phase": "super",
  "super_game_time_remaining": 300.0,
  "message": "Супер игра началась!"
}
```

**Фаза "finished":**
```json
{
  "new_phase": "finished",
  "message": "Игра завершена!"
}
```

**Пример:**
```javascript
socket.on('phase_changed', (data) => {
  console.log('Phase changed to:', data.new_phase);
  if (data.new_phase === 'top10') {
    showVotingUI(data.voting_time_remaining);
  }
});
```

### Отправить: `get_game_phase`

Запросить информацию о текущей фазе игры.

**Формат:**
```javascript
socket.emit('get_game_phase');
```

**Ответы:**

**Успех: `game_phase_info`**
```json
{
  "phase": "start"
}
// или для top10:
{
  "phase": "top10",
  "voting_time_remaining": 25.5,
  "votes_submitted": 8,
  "votes_exit": 3,
  "votes_super": 5
}
// или для super:
{
  "phase": "super",
  "super_game_time_remaining": 180.5,
  "skill_costs_increased": false
}
```

**Ошибка: `game_phase_error`**
```json
{
  "message": "Not in game"
}
```

---

## Голосование (топ-10)

### Отправить: `submit_vote`

Проголосовать в топ-10 (за выход или супер-игру).

**Формат:**
```javascript
socket.emit('submit_vote', {
  vote: 'exit'  // 'exit' | 'super'
});
```

**Ответы:**

**Успех: `vote_submitted`**
```json
{
  "vote": "exit",
  "voting_time_remaining": 25.5
}
```

**Ошибка: `vote_error`**
```json
{
  "message": "Invalid vote"
}
```

### `vote_update`

Обновление голосования (отправляется всем в комнате при новом голосе).

**Данные:**
```json
{
  "votes_submitted": 8,
  "votes_exit": 3,
  "votes_super": 5
}
```

### `voting_warning`

Предупреждение о скором окончании голосования (когда осталось ≤10 секунд).

**Данные:**
```json
{
  "time_remaining": 8.5,
  "votes_submitted": 8,
  "votes_exit": 3,
  "votes_super": 5
}
```

---

## Выход из игры

### Отправить: `exit_game`

Выйти из игры (ранний выход или выход из супер-игры).

**Формат:**
```javascript
socket.emit('exit_game', {
  exit_type: 'early'  // 'early' (до топ-10) | 'super' (из супер-игры)
});
```

**Ответы:**

**Успех: `finished`**
```json
{
  "player_id": "uuid",
  "exit_type": "early",
  "original_balance": 100.0,
  "final_balance": 50.0,
  "penalty": 50.0,
  "message": "You left the game early. You saved 50% of your balance."
}
```

**Ошибка: `exit_error`**
```json
{
  "message": "Invalid exit type or phase"
}
```

### `player_exited`

Уведомление о выходе игрока (для всех в комнате).

**Данные:**
```json
{
  "player_id": "uuid",
  "exit_type": "early",
  "winnings": 50.0
}
```

---

## Бонусные зоны

### Отправить: `get_bonus_zones_info`

Получить информацию о бонусных зонах.

**Формат:**
```javascript
socket.emit('get_bonus_zones_info');
```

**Ответ: `bonus_zones_info`**
```json
{
  "active_zones": [
    {
      "x": 200,
      "y": 300,
      "radius": 80,
      "multiplier": 2,
      "remaining_time": 25.5,
      "funds_collected": 50,
      "max_funds": 40,
      "is_active": true
    }
  ],
  "zone_fund": 100,
  "bonus_fund": 500,
  "time_to_next_zone": 45.2,
  "zone_settings": {
    "spawn_interval_seconds": 180.0,
    "zone_duration_seconds": 30.0,
    "funds_per_zone": 20
  }
}
```

### `bonus_zone_spawned`

Появилась новая бонусная зона.

**Данные:**
```json
{
  "x": 200,
  "y": 300,
  "radius": 80,
  "multiplier": 2,
  "duration": 30.0,
  "zone_fund": 100
}
```

### `bonus_zone_expired`

Бонусная зона истекла.

**Данные:**
```json
{
  "x": 200,
  "y": 300,
  "multiplier": 2,
  "funds_collected": 50
}
```

---

## Зона и урон

### `zone_shrunk`

Безопасная зона уменьшилась.

**Данные:**
```json
{
  "new_scale": 0.7,
  "damage_per_second": 2.5,
  "time_to_next_shrink": 120.0
}
```

### `super_game_warning`

Предупреждение в супер-игре (когда осталось ≤60 секунд).

**Данные:**
```json
{
  "time_remaining": 45.5,
  "players_remaining": 5
}
```

---

## Результаты игры

### Отправить: `get_game_results`

Получить результаты игры.

**Формат:**
```javascript
socket.emit('get_game_results');
```

**Ответ: `game_results`**
```json
{
  "early_exits": {
    "player-id": 50.5
  },
  "super_exits": {
    "player-id": 25.3
  },
  "finalists": ["player-id-1", "player-id-2"],
  "bonus_fund": 500,
  "zone_fund": 100,
  "final_winnings": {
    "player-id-1": 1000.5,
    "player-id-2": 500.3
  }
}
```

**Ошибка: `results_error`**
```json
{
  "message": "Not in game"
}
```

### `game_finished`

Игра завершена (отправляется всем в комнате).

**Данные:** Та же структура, что у `game_results`.

---

## Другие события

### Отправить: `get_players`

Получить список всех игроков в игре.

**Формат:**
```javascript
socket.emit('get_players', {
  room_id: 'uuid-комнаты'
});
```

**Ответ: `all_players`**
```json
{
  "player-id-1": { /* данные игрока */ },
  "player-id-2": { /* данные игрока */ }
}
```

### `player_joined`

Игрок присоединился к комнате (для всех в комнате).

**Данные:**
```json
{
  "players": [
    {
      "user_id": "uuid",
      "username": "sasha"
    }
  ],
  "room_id": "uuid"
}
```

### `player_left`

Игрок покинул комнату (для всех в комнате).

**Данные:**
```json
{
  "user_id": "uuid",
  "room_id": "uuid"
}
```

### `error`

Общая ошибка.

**Данные:**
```json
{
  "message": "Error description"
}
```

---

## Типичный флоу игры

```javascript
// 1. Подключение
const socket = io('http://93.183.106.254:8000');

socket.on('connect', () => {
  // 2. Аутентификация
  socket.emit('authenticate', { user_id: 'your-user-id' });
});

socket.on('authenticated', (data) => {
  // 3. Присоединиться к игре
  socket.emit('join_game', {
    entry_fee: 0,
    min_players: 1,
    max_players: 100
  });
});

socket.on('joined_room', (data) => {
  const roomId = data.room_id;
  console.log('Joined room:', roomId);
  
  if (data.time_to_start) {
    // Игра скоро начнётся
    startCountdown(data.time_to_start);
  }
});

socket.on('game_started', (data) => {
  // Игра начнётся через 30 секунд
  startCountdown(data.time_to_start);
});

// 4. Игра началась - слушаем game_state
socket.on('game_state', (state) => {
  renderGame(state);
});

// 5. Лидерборд обновляется автоматически раз в 10 секунд
socket.on('leaderboard', (leaderboard) => {
  updateLeaderboard(leaderboard);
});

// 6. Движение
setInterval(() => {
  const { dx, dy } = getMovementInput();
  if (dx !== 0 || dy !== 0) {
    socket.emit('move', { dx, dy });
  }
}, 50);

// 7. Скиллы
document.getElementById('teleport-btn').onclick = () => {
  socket.emit('activate_skill', { skill_type: 'teleport' });
};

// 8. Выход из игры
document.getElementById('exit-btn').onclick = () => {
  socket.emit('exit_game', { exit_type: 'early' });
};

socket.on('finished', (data) => {
  console.log('Game finished:', data);
  showResults(data);
});
```

---

## Важные замечания

1. **Всегда аутентифицируйся** перед `join_game` или другими игровыми событиями.
2. **Сохраняй `room_id`** из `joined_room` для реконнектов.
3. **Лидерборд обновляется автоматически** раз в 10 секунд, но можно запросить вручную через `get_leaderboard`.
4. **Скиллы сейчас бесплатные** (`cost: 0`), но есть кулдауны и лимит 5 скиллов за игру.
5. **`game_state`** приходит регулярно (каждые 50мс в игровом цикле) — используй его для рендеринга игры.
6. **Обрабатывай ошибки** — все события могут вернуть `error` или `*_error` с описанием проблемы.

---

## Полный список событий

### События, которые отправляет клиент (emit):
- `authenticate`
- `join_game` ⭐
- `create_room`
- `join_room`
- `leave_room`
- `get_rooms`
- `move`
- `activate_skill`
- `get_leaderboard`
- `get_game_phase`
- `submit_vote`
- `request_last_chance`
- `get_bonus_zones_info`
- `get_game_results`
- `exit_game`
- `get_players`

### События, которые отправляет сервер (on):
- `connect` / `connected`
- `disconnect`
- `authenticated` / `auth_error`
- `joined_room`
- `left_room`
- `room_created`
- `rooms_list`
- `player_joined`
- `player_left`
- `game_started`
- `game_state`
- `leaderboard` / `leaderboard_error`
- `skill_activated` / `skill_error`
- `player_used_skill`
- `last_chance_activated` / `last_chance_error`
- `phase_changed`
- `game_phase_info` / `game_phase_error`
- `vote_submitted` / `vote_error`
- `vote_update`
- `voting_warning`
- `finished` / `exit_error`
- `player_exited`
- `bonus_zones_info`
- `bonus_zone_spawned`
- `bonus_zone_expired`
- `zone_shrunk`
- `super_game_warning`
- `game_results` / `results_error`
- `game_finished`
- `all_players`
- `error`

