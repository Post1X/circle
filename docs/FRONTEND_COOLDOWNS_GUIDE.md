# Руководство по обработке Cooldowns на фронтенде

## Структура данных

Cooldowns приходят в следующем формате:

```typescript
interface Cooldowns {
  teleport: number;  // в секундах, округлено до 1 знака (например: 60.0, 59.9, 59.8...)
  shield: number;    // в секундах, округлено до 1 знака
  boost: number;     // в секундах, округлено до 1 знака
}

interface PlayerData {
  // ... другие поля
  cooldowns: Cooldowns;
}
```

## GameCanvas (WebSocket версия)

### 1. Обработка события `game_state`

При получении события `game_state` обновляйте cooldowns из данных игрока:

```typescript
socket.on('game_state', (gameState) => {
  const playerId = getCurrentPlayerId(); // ваш ID игрока
  const playerData = gameState.players[playerId];
  
  if (playerData && playerData.cooldowns) {
    // Обновляйте состояние cooldowns
    setCooldowns({
      teleport: playerData.cooldowns.teleport,
      shield: playerData.cooldowns.shield,
      boost: playerData.cooldowns.boost,
    });
  }
});
```

### 2. Обработка события `skill_activated` (опционально)

Событие `skill_activated` также содержит cooldowns, но основным источником должен быть `game_state`:

```typescript
socket.on('skill_activated', (data) => {
  if (data.cooldowns) {
    // Можно обновить cooldowns, но game_state придет сразу после
    setCooldowns(data.cooldowns);
  }
});
```

### 3. Отображение таймера

Таймер должен отображаться постоянно, пока cooldown > 0:

```typescript
// Пример отображения таймера
{cooldowns.teleport > 0 && (
  <div className="cooldown-timer">
    Teleport: {cooldowns.teleport.toFixed(1)}s
  </div>
)}
// Важно: проверяйте cooldowns.teleport > 0, а не cooldowns.teleport >= 0
// чтобы таймер скрывался только когда cooldown полностью закончился

{cooldowns.shield > 0 && (
  <div className="cooldown-timer">
    Shield: {cooldowns.shield.toFixed(1)}s
  </div>
)}

{cooldowns.boost > 0 && (
  <div className="cooldown-timer">
    Boost: {cooldowns.boost.toFixed(1)}s
  </div>
)}
```

**Важно:** Таймер должен обновляться при каждом получении `game_state` (каждые ~50мс), а не только при активации скилла.

## DemoGame (REST API версия)

### 1. Опрос состояния игры

Регулярно опрашивайте эндпоинт `GET /api/beta-game/state/{game_id}`:

```typescript
const pollGameState = async () => {
  const response = await fetch(`/api/beta-game/state/${gameId}`);
  const gameState = await response.json();
  
  const playerId = getCurrentPlayerId();
  const playerData = gameState.players[playerId];
  
  if (playerData && playerData.cooldowns) {
    setCooldowns({
      teleport: playerData.cooldowns.teleport,
      shield: playerData.cooldowns.shield,
      boost: playerData.cooldowns.boost,
    });
  }
};

// Опрашивайте каждые 50-100мс
setInterval(pollGameState, 50);
```

### 2. Обработка ответа `activate_skill`

После активации скилла ответ содержит cooldowns в `data.cooldowns`:

```typescript
const activateSkill = async (skillType: string) => {
  const response = await fetch('/api/beta-game/skill', {
    method: 'POST',
    body: JSON.stringify({ game_id: gameId, player_id: playerId, skill_type: skillType }),
  });
  
  const result = await response.json();
  
  if (result.success && result.data?.cooldowns) {
    // Обновить cooldowns из ответа
    setCooldowns(result.data.cooldowns);
  }
  
  // Продолжайте опрашивать game_state для актуальных данных
};
```

### 3. Отображение таймера

Аналогично GameCanvas - показывайте таймер, пока cooldown > 0, и обновляйте при каждом опросе состояния.

## Ключевые моменты

1. **Основной источник данных:** `game_state` (WebSocket) или `GET /api/beta-game/state/{game_id}` (REST)
2. **Частота обновления:** каждые ~50мс (20 FPS)
3. **Отображение:** таймер должен быть виден постоянно, пока `cooldown > 0`
4. **Формат:** значения в секундах, округлены до 1 знака после запятой (например: 60.0, 59.9, 0.1, 0.0)
5. **Не полагайтесь только на `skill_activated`:** всегда используйте `game_state` как основной источник истины

## Пример полной реализации (React)

```typescript
const [cooldowns, setCooldowns] = useState({
  teleport: 0,
  shield: 0,
  boost: 0,
});

useEffect(() => {
  // WebSocket версия
  socket.on('game_state', (gameState) => {
    const playerData = gameState.players[playerId];
    if (playerData?.cooldowns) {
      setCooldowns(playerData.cooldowns);
    }
  });

  return () => {
    socket.off('game_state');
  };
}, [playerId]);

// Отображение
return (
  <div>
    {cooldowns.teleport > 0 && (
      <div>Teleport: {cooldowns.teleport.toFixed(1)}s</div>
    )}
    {cooldowns.shield > 0 && (
      <div>Shield: {cooldowns.shield.toFixed(1)}s</div>
    )}
    {cooldowns.boost > 0 && (
      <div>Boost: {cooldowns.boost.toFixed(1)}s</div>
    )}
  </div>
);
```

