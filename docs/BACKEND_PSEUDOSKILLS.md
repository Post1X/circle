# Документация: Псевдонавыки (Кнопочные механики)

## Обзор

Помимо платных навыков в игре присутствуют две дополнительные кнопочные механики, которые по пользовательскому взаимодействию похожи на навыки, но не считаются навыками и работают по отдельным правилам.

---

## 1. Выход из игры (Cash Out)

### Описание

Игрок может добровольно выйти из игры с получением части текущего баланса. Механика не имеет стоимости активации, кулдауна и не учитывается в лимите навыков. Является экономическим решением игрока.

### Правила

#### До стадии топ-10 (Early Exit)
- **Сохранение баланса:** 50% от текущего баланса
- **Штраф:** 50% от текущего баланса (направляется в бонусный фонд)
- **Условия:** Фаза игры не "super_game" (включая игроков в топ-10, которые еще не в супер игре)

#### В супер игре (Super Exit)
- **Сохранение баланса:** 25% от текущего баланса
- **Штраф:** 75% от текущего баланса (направляется в бонусный фонд)
- **Условия:** Фаза игры === "super_game"

**Важно:** Cash Out всегда доступен. Если игрок в топ-10, но еще не в супер игре, он может выйти с 50% (early exit).

### WebSocket API

#### Событие: `cash_out`

**Клиент → Сервер:**
```json
{
  "exit_type": "early" | "super"
}
```

**Параметры:**
- `exit_type: "early"` - выход до топ-10, сохранение 50%
- `exit_type: "super"` - выход из супер игры, сохранение 25%

#### Событие: `cash_out_success`

**Сервер → Клиент:**
```json
{
  "player_id": "string (UUID)",
  "exit_type": "early" | "super",
  "original_balance": 10.0,
  "final_balance": 5.0,
  "penalty": 5.0,
  "message": "You cashed out. You saved 50% of your balance ($5.00)."
}
```

#### Событие: `cash_out_error`

**Сервер → Клиент:**
```json
{
  "message": "Cannot cash out: player not in game"
}
```

### Валидация на бекенде

1. **Проверка авторизации:**
   - Игрок должен быть авторизован
   - Игрок должен быть в активной игре

2. **Проверка типа выхода:**
   - Если `exit_type === "early"`:
     - Проверить что фаза игры не "super_game"
     - Игрок может быть в топ-10, но не в супер игре
   - Если `exit_type === "super"`:
     - Проверить что фаза игры === "super_game"
     - Игрок должен быть в супер игре

3. **Расчет финального баланса:**
   ```python
   if exit_type == "early":
       final_balance = player.balance * 0.50
       penalty = player.balance * 0.50
   elif exit_type == "super":
       final_balance = player.balance * 0.25
       penalty = player.balance * 0.75
   ```

4. **Обновление баланса:**
   ```python
   player.balance = final_balance
   # Штраф добавляется в бонусный фонд
   game.bonus_fund += penalty
   ```

5. **Удаление игрока из игры:**
   ```python
   player.status = "exited"
   game.remove_player(player_id)
   ```

6. **Отправка события:**
   - Отправить `cash_out_success` игроку
   - Обновить `game_state` для остальных игроков
   - Уведомить о выходе игрока через `player_left`

### Примеры

#### Пример 1: Ранний выход (50%)
```
Игрок: balance = $10.00, rank = 15, phase = "normal"
Расчет:
  - final_balance = $10.00 * 0.50 = $5.00
  - penalty = $10.00 * 0.50 = $5.00

Результат:
  - player.balance = $5.00
  - bonus_fund += $5.00
  - player.status = "exited"
```

#### Пример 2: Выход из супер игры (25%)
```
Игрок: balance = $10.00, rank = 5, phase = "super_game"
Расчет:
  - final_balance = $10.00 * 0.25 = $2.50
  - penalty = $10.00 * 0.75 = $7.50

Результат:
  - player.balance = $2.50
  - bonus_fund += $7.50
  - player.status = "exited"
```

---

## 2. Режим «Последний шанс»

### Описание

В супер игре, за 3 минуты до окончания, игрок с балансом менее $5 получает возможность однократно активировать бесплатный телепорт в безопасную зону. После использования «Последнего шанса» все последующие платные навыки для этого игрока стоят на +5% дороже. Механика не входит в лимит навыков и предназначена для поддержки слабых игроков.

### Правила

#### Условия доступности:
1. Фаза игры === "super_game"
2. Осталось времени до окончания супер игры: ≤ 180 секунд (3 минуты)
3. Баланс игрока < $5.00
4. Игрок еще не использовал "Последний шанс" (free_teleport_used === false)

#### Эффекты:
- **Бесплатный телепорт:** Игрок телепортируется в безопасную зону (аналогично обычному телепорту)
- **Штраф на навыки:** После использования все платные навыки стоят на +5% дороже
- **Однократное использование:** Можно использовать только один раз за игру
- **Не учитывается в лимите:** Не засчитывается в `skills_used` и не влияет на `max_uses`

### WebSocket API

#### Событие: `request_last_chance`

**Клиент → Сервер:**
```json
{}
```

**Параметры:** Нет параметров (определяется автоматически по игроку)

#### Событие: `last_chance_activated`

**Сервер → Клиент:**
```json
{
  "player_id": "string (UUID)",
  "skill_costs_increased": true,
  "new_position": {
    "x": 100.5,
    "y": 200.3
  },
  "message": "Last chance activated! You teleported to safe zone. All skills now cost +5% more."
}
```

#### Событие: `last_chance_error`

**Сервер → Клиент:**
```json
{
  "message": "Last chance unavailable: balance must be less than $5"
}
```

### Валидация на бекенде

1. **Проверка авторизации:**
   - Игрок должен быть авторизован
   - Игрок должен быть в активной игре

2. **Проверка фазы игры:**
   ```python
   if game.phase != "super_game":
       return error("Last chance available only in super game")
   ```

3. **Проверка времени:**
   ```python
   if game.super_game_time_remaining > 180:
       return error(f"Last chance available in {math.ceil((game.super_game_time_remaining - 180) / 60)} minutes")
   ```

4. **Проверка баланса:**
   ```python
   if player.balance >= 5.0:
       return error("Last chance available only for players with balance < $5")
   ```

5. **Проверка использования:**
   ```python
   if player.free_teleport_used:
       return error("Last chance already used")
   ```

6. **Активация телепорта:**
   ```python
   # Найти безопасную позицию в зоне
   safe_position = game.get_safe_position()
   
   # Телепортировать игрока
   player.x = safe_position.x
   player.y = safe_position.y
   
   # Установить флаг использования
   player.free_teleport_used = True
   
   # Установить флаг увеличения стоимости навыков
   player.skill_costs_increased = True
   ```

7. **Отправка события:**
   ```python
   emit("last_chance_activated", {
       "player_id": player.id,
       "skill_costs_increased": True,
       "new_position": {"x": player.x, "y": player.y},
       "message": "Last chance activated! You teleported to safe zone. All skills now cost +5% more."
   })
   ```

8. **Обновление стоимости навыков:**
   - При расчете стоимости навыков проверять `player.skill_costs_increased`
   - Если `True`, добавлять +5% к базовой стоимости навыка

### Примеры

#### Пример 1: Успешная активация
```
Игрок: balance = $3.50, phase = "super_game", 
       super_game_time_remaining = 150, free_teleport_used = False

Проверка:
  ✓ phase === "super_game"
  ✓ time_remaining (150) <= 180
  ✓ balance ($3.50) < $5.00
  ✓ free_teleport_used === False

Результат:
  - player.x = safe_position.x
  - player.y = safe_position.y
  - player.free_teleport_used = True
  - player.skill_costs_increased = True
  - Отправлено: last_chance_activated
```

#### Пример 2: Недоступно - баланс слишком высокий
```
Игрок: balance = $6.00, phase = "super_game", 
       super_game_time_remaining = 150, free_teleport_used = False

Проверка:
  ✓ phase === "super_game"
  ✓ time_remaining (150) <= 180
  ✗ balance ($6.00) >= $5.00

Результат:
  - Отправлено: last_chance_error
  - message: "Last chance available only for players with balance < $5"
```

#### Пример 3: Недоступно - уже использовано
```
Игрок: balance = $3.50, phase = "super_game", 
       super_game_time_remaining = 150, free_teleport_used = True

Проверка:
  ✓ phase === "super_game"
  ✓ time_remaining (150) <= 180
  ✓ balance ($3.50) < $5.00
  ✗ free_teleport_used === True

Результат:
  - Отправлено: last_chance_error
  - message: "Last chance already used"
```

#### Пример 4: Влияние на стоимость навыков
```
Игрок: balance = $10.00, skill_costs_increased = True

Расчет стоимости щита:
  - Базовая стоимость: $10.00 * 0.10 = $1.00
  - Штраф за последний шанс: +5% = $10.00 * 0.05 = $0.50
  - Итоговая стоимость: $1.00 + $0.50 = $1.50 (15% вместо 10%)
```

---

## 3. Интеграция с существующими механиками

### Взаимодействие с навыками

1. **Cash Out:**
   - Не влияет на лимит навыков (`skills_used`)
   - Не имеет кулдауна
   - Не требует баланса для активации (но уменьшает баланс при выходе)

2. **Last Chance:**
   - Не учитывается в `skills_used`
   - Не имеет кулдауна
   - Бесплатный (не требует баланса)
   - Влияет на стоимость всех последующих навыков (+5%)

### Взаимодействие с игровыми фазами

1. **Cash Out:**
   - Доступен в любой фазе (но с разными процентами)
   - В топ-10 до супер игры - недоступен (нужно дождаться супер игры)

2. **Last Chance:**
   - Доступен только в фазе "super_game"
   - Только за 3 минуты до окончания

### Обновление game_state

После активации любой из механик необходимо обновить `game_state`:
- Для Cash Out: удалить игрока из списка
- Для Last Chance: обновить `free_teleport_used` и `skill_costs_increased` в данных игрока

---

## 4. Рекомендации по реализации

### Проверка доступности на фронтенде

Фронтенд должен проверять доступность перед отправкой запроса:

**Cash Out:**
```typescript
const cashOutCheck = canCashOut(gamePhase, rank);
if (cashOutCheck.canActivate) {
  wsc.cashOut(cashOutCheck.exitType);
}
```

**Last Chance:**
```typescript
const lastChanceCheck = canActivateLastChance(
  gamePhase,
  superGameTimeRemaining,
  balance,
  freeTeleportUsed
);
if (lastChanceCheck.canActivate) {
  wsc.requestLastChance();
}
```

### Обработка ошибок

Всегда обрабатывайте ошибки на клиенте:
- Показывайте понятные сообщения пользователю
- Не блокируйте UI при ошибках
- Позволяйте повторную попытку (если условия изменились)

### Тестирование

Рекомендуется протестировать:
1. Cash Out до топ-10 (50%)
2. Cash Out в супер игре (25%)
3. Попытка Cash Out в топ-10 до супер игры (должна быть недоступна)
4. Last Chance в супер игре с балансом < $5
5. Last Chance с балансом >= $5 (должна быть недоступна)
6. Last Chance после использования (должна быть недоступна)
7. Влияние Last Chance на стоимость навыков

---

## 5. Изменения в существующем коде

### Обновление расчета стоимости навыков

Если игрок использовал Last Chance, нужно учитывать штраф:

```python
def calculate_skill_cost(player, skill_type):
    base_percentage = SKILL_COSTS[skill_type]  # например, 10% для щита
    
    if player.skill_costs_increased:
        base_percentage += 5  # +5% штраф
    
    return player.balance * (base_percentage / 100)
```

### Обновление game_state

В `game_state` для каждого игрока должно быть:
```python
{
    "player_id": "...",
    "free_teleport_used": False,  # или True
    "skill_costs_increased": False,  # или True
    ...
}
```

---

## 6. Примеры полных сценариев

### Сценарий 1: Игрок использует Cash Out до топ-10

```
1. Игрок: balance = $8.00, rank = 20, phase = "normal"
2. Игрок нажимает Cash Out
3. Фронтенд проверяет: canCashOut("normal", 20) → {canActivate: true, percentage: 50, exitType: "early"}
4. Фронтенд отправляет: cash_out({exit_type: "early"})
5. Бекенд проверяет условия
6. Бекенд рассчитывает: final_balance = $8.00 * 0.50 = $4.00, penalty = $4.00
7. Бекенд обновляет: player.balance = $4.00, bonus_fund += $4.00
8. Бекенд удаляет игрока из игры
9. Бекенд отправляет: cash_out_success
10. Фронтенд показывает финальный экран с результатами
```

### Сценарий 2: Игрок использует Last Chance

```
1. Игрок: balance = $3.00, phase = "super_game", 
          super_game_time_remaining = 150, free_teleport_used = False
2. Игрок нажимает Last Chance
3. Фронтенд проверяет: canActivateLastChance(...) → {canActivate: true}
4. Фронтенд отправляет: request_last_chance({})
5. Бекенд проверяет все условия
6. Бекенд находит безопасную позицию: safe_position = {x: 100, y: 200}
7. Бекенд телепортирует: player.x = 100, player.y = 200
8. Бекенд устанавливает флаги: free_teleport_used = True, skill_costs_increased = True
9. Бекенд отправляет: last_chance_activated
10. Фронтенд обновляет UI, показывает уведомление
11. При следующей активации навыка стоимость будет +5% больше
```

---

## Заключение

Обе механики являются важными элементами игрового процесса:
- **Cash Out** дает игрокам возможность зафиксировать прибыль в любой момент
- **Last Chance** поддерживает слабых игроков в критический момент игры

Важно правильно реализовать валидацию и обработку ошибок, чтобы обеспечить справедливый игровой процесс.
