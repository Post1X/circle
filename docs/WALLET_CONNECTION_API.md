# API для подключения кошельков

## Поддерживаемые типы кошельков

### Tron блокчейн:
- `tronlink` - TronLink
- `safepal` - SafePal

### Solana блокчейн:
- `solflare` - Solflare
- `phantom` - Phantom
- `solong` - Solong

### Ethereum/BSC/Polygon:
- `metamask` - MetaMask
- `ledger` - Ledger
- `torus` - Torus

---

## Endpoints

### 1. Получить nonce для подписи

**POST** `/api/users/nonce`

Получает одноразовый nonce для подписи сообщения кошельком.

**Request Body:**
```json
{
  "address": "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
  "wallet_type": "tronlink"  // опционально
}
```

**Response:**
```json
{
  "nonce": "a1b2c3d4e5f6..."
}
```

**Пример запроса:**
```bash
curl -X POST http://localhost:8000/api/users/nonce \
  -H "Content-Type: application/json" \
  -d '{
    "address": "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
    "wallet_type": "tronlink"
  }'
```

---

### 2. Подключить кошелек (первый вход)

**POST** `/api/users/wallet-connect`

Подключает кошелек к системе. Если пользователя с таким адресом нет, создается новый пользователь.

**Request Body:**
```json
{
  "address": "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
  "signature": "0x1234...",
  "nonce": "a1b2c3d4e5f6...",
  "message": "Sign this message to connect your wallet: a1b2c3d4e5f6...",
  "wallet_type": "tronlink"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Wallet connected successfully",
  "wallet_address": "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
  "wallet_type": "tronlink",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "user_abc123",
  "balance": 0,
  "games_played": 0,
  "total_winnings": 0,
  "leaderboard_rank": 0,
  "is_admin": false,
  "avatar_url": null
}
```

**Пример запроса:**
```bash
curl -X POST http://localhost:8000/api/users/wallet-connect \
  -H "Content-Type: application/json" \
  -d '{
    "address": "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
    "signature": "0x1234...",
    "nonce": "a1b2c3d4e5f6...",
    "message": "Sign this message to connect your wallet: a1b2c3d4e5f6...",
    "wallet_type": "tronlink"
  }'
```

---

### 3. Привязать дополнительный кошелек (требует авторизации)

**POST** `/api/users/wallet/bind`

Привязывает дополнительный кошелек к существующему аккаунту.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "address": "TXYZabc123...",
  "signature": "0x5678...",
  "message": "Sign this message to bind your wallet: nonce123",
  "wallet_type": "phantom"
}
```

**Response:**
```json
{
  "id": 2,
  "address": "TXYZabc123...",
  "network": "solana",
  "wallet_type": "phantom",
  "is_primary": false,
  "created_at": "2025-12-31T17:00:00.000Z"
}
```

**Пример запроса:**
```bash
curl -X POST http://localhost:8000/api/users/wallet/bind \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -d '{
    "address": "TXYZabc123...",
    "signature": "0x5678...",
    "message": "Sign this message to bind your wallet: nonce123",
    "wallet_type": "phantom"
  }'
```

---

### 4. Получить список привязанных кошельков

**GET** `/api/users/wallets`

Получает список всех кошельков, привязанных к текущему пользователю.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
[
  {
    "id": 1,
    "address": "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
    "network": "tron",
    "wallet_type": "tronlink",
    "is_primary": true,
    "created_at": "2025-12-31T16:00:00.000Z"
  },
  {
    "id": 2,
    "address": "TXYZabc123...",
    "network": "solana",
    "wallet_type": "phantom",
    "is_primary": false,
    "created_at": "2025-12-31T17:00:00.000Z"
  }
]
```

**Пример запроса:**
```bash
curl -X GET http://localhost:8000/api/users/wallets \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

### 5. Установить primary кошелек

**POST** `/api/users/wallet/:id/primary`

Устанавливает указанный кошелек как основной (primary).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "id": 2,
  "address": "TXYZabc123...",
  "network": "solana",
  "wallet_type": "phantom",
  "is_primary": true,
  "created_at": "2025-12-31T17:00:00.000Z"
}
```

**Пример запроса:**
```bash
curl -X POST http://localhost:8000/api/users/wallet/2/primary \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

### 6. Отвязать кошелек

**DELETE** `/api/users/wallet/:id`

Отвязывает кошелек от аккаунта.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "message": "Wallet unbound successfully"
}
```

**Пример запроса:**
```bash
curl -X DELETE http://localhost:8000/api/users/wallet/2 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

## Процесс подключения кошелька (клиентская часть)

### Шаг 1: Получить nonce
```javascript
const response = await fetch('http://localhost:8000/api/users/nonce', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    address: walletAddress,
    wallet_type: 'tronlink'
  })
});
const { nonce } = await response.json();
```

### Шаг 2: Создать сообщение для подписи
```javascript
const message = `Sign this message to connect your wallet: ${nonce}`;
```

### Шаг 3: Подписать сообщение кошельком
```javascript
// Для TronLink
const signature = await window.tronWeb.trx.signMessage(message);

// Для MetaMask
const signature = await window.ethereum.request({
  method: 'personal_sign',
  params: [message, walletAddress]
});

// Для Phantom (Solana)
const encodedMessage = new TextEncoder().encode(message);
const signedMessage = await window.solana.signMessage(encodedMessage, 'utf8');
const signature = Buffer.from(signedMessage.signature).toString('base64');
```

### Шаг 4: Отправить запрос на подключение
```javascript
const response = await fetch('http://localhost:8000/api/users/wallet-connect', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    address: walletAddress,
    signature: signature,
    nonce: nonce,
    message: message,
    wallet_type: 'tronlink' // или 'metamask', 'phantom', и т.д.
  })
});

const data = await response.json();
// Сохранить access_token для дальнейших запросов
localStorage.setItem('access_token', data.access_token);
```

---

## Примеры для разных кошельков

### TronLink (Tron)
```javascript
// 1. Получить nonce
const nonceResponse = await fetch('http://localhost:8000/api/users/nonce', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    address: window.tronWeb.defaultAddress.base58,
    wallet_type: 'tronlink'
  })
});
const { nonce } = await nonceResponse.json();

// 2. Подписать сообщение
const message = `Sign this message to connect your wallet: ${nonce}`;
const signature = await window.tronWeb.trx.signMessage(message);

// 3. Подключить кошелек
const connectResponse = await fetch('http://localhost:8000/api/users/wallet-connect', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    address: window.tronWeb.defaultAddress.base58,
    signature: signature,
    nonce: nonce,
    message: message,
    wallet_type: 'tronlink'
  })
});
```

### MetaMask (Ethereum/BSC/Polygon)
```javascript
// 1. Получить nonce
const nonceResponse = await fetch('http://localhost:8000/api/users/nonce', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    address: accounts[0],
    wallet_type: 'metamask'
  })
});
const { nonce } = await nonceResponse.json();

// 2. Подписать сообщение
const message = `Sign this message to connect your wallet: ${nonce}`;
const signature = await window.ethereum.request({
  method: 'personal_sign',
  params: [message, accounts[0]]
});

// 3. Подключить кошелек
const connectResponse = await fetch('http://localhost:8000/api/users/wallet-connect', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    address: accounts[0],
    signature: signature,
    nonce: nonce,
    message: message,
    wallet_type: 'metamask'
  })
});
```

### Phantom (Solana)
```javascript
// 1. Получить nonce
const nonceResponse = await fetch('http://localhost:8000/api/users/nonce', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    address: publicKey.toBase58(),
    wallet_type: 'phantom'
  })
});
const { nonce } = await nonceResponse.json();

// 2. Подписать сообщение
const message = `Sign this message to connect your wallet: ${nonce}`;
const encodedMessage = new TextEncoder().encode(message);
const signedMessage = await window.solana.signMessage(encodedMessage, 'utf8');
const signature = Buffer.from(signedMessage.signature).toString('base64');

// 3. Подключить кошелек
const connectResponse = await fetch('http://localhost:8000/api/users/wallet-connect', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    address: publicKey.toBase58(),
    signature: signature,
    nonce: nonce,
    message: message,
    wallet_type: 'phantom'
  })
});
```

---

## Важные замечания

1. **Проверка подписи**: Все запросы на подключение/привязку кошелька проверяют подпись для безопасности
2. **Nonce**: Каждый nonce можно использовать только один раз
3. **Primary кошелек**: Первый привязанный кошелек автоматически становится primary
4. **Множественные кошельки**: Пользователь может привязать несколько кошельков разных типов
5. **Автоматическое создание пользователя**: При первом подключении кошелька создается новый пользователь с случайным username

