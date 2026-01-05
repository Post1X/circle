import socketio
import pygame
import sys
import threading
import time
import httpx

WIDTH, HEIGHT = 800, 600

sio = socketio.Client()

API_URL = "http://localhost:8000/api/users/create_simple"

player_wallet = None
player_id = None
room_id = None
state = {"players": {}, "foods": []}

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Agar.io Client")
clock = pygame.time.Clock()

user_action = None
input_room_id = None

def ask_user():
    global user_action, input_room_id
    print("1. Создать новую комнату")
    print("2. Подключиться к существующей комнате")
    choice = input("Выберите действие (1/2): ").strip()
    if choice == "1":
        user_action = "create"
    elif choice == "2":
        user_action = "join"
        input_room_id = input("Введите room_id для подключения: ").strip()
    else:
        print("Некорректный выбор!")
        sys.exit(1)

def create_simple_user():
    print("Создаём нового пользователя через API...")
    resp = httpx.post(API_URL)
    if resp.status_code == 200:
        data = resp.json()
        print(f"Создан пользователь: user_id={data['user_id']}, wallet_address={data['wallet_address']}")
        return data['user_id'], data['wallet_address']
    else:
        print("Ошибка при создании пользователя!", resp.text)
        sys.exit(1)

# --- Логика выбора пользователя ---
player_id = None
player_wallet = None
while not player_id:
    print("Введите user_id (или оставьте пустым для создания нового пользователя): ", end="")
    inp = input().strip()
    if inp:
        player_id = inp
        player_wallet = None
    else:
        player_id, player_wallet = create_simple_user()
        break

print(f"Вы играете за пользователя: user_id={player_id}, wallet_address={player_wallet}")
ask_user()

@sio.event
def connect():
    print("Connected to server")
    sio.emit("authenticate", {"user_id": player_id})

@sio.event
def auth_error(data):
    print(f"Ошибка авторизации: {data.get('message')}")
    print("Попробуйте создать нового пользователя!")
    new_id, new_wallet = create_simple_user()
    global player_id, player_wallet
    player_id, player_wallet = new_id, new_wallet
    print(f"Пробуем авторизоваться с новым user_id: {player_id}")
    sio.emit("authenticate", {"user_id": player_id})

@sio.event
def authenticated(data):
    print("Аутентификация успешна!")
    if user_action == "create":
        sio.emit("create_room", {"entry_fee": 0, "min_players": 2, "max_players": 10})
    elif user_action == "join":
        sio.emit("join_room", {"room_id": input_room_id})

@sio.event
def room_created(data):
    global room_id
    room_id = data["room_id"]
    print(f"Создана комната с room_id: {room_id}")
    sio.emit("join_room", {"room_id": room_id})

@sio.event
def joined_room(data):
    print(f"Joined room {data['room_id']}")
    sio.emit("start_game", {"room_id": data["room_id"]})

@sio.event
def game_started(data):
    print("Game started!")

@sio.event
def game_state(data):
    global state
    state = data

@sio.event
def disconnect():
    print("Disconnected from server")
    pygame.quit()
    sys.exit(0)

def send_move(dx, dy):
    sio.emit("move", {"dx": dx, "dy": dy})

def network_thread():
    sio.connect("http://localhost:8000", transports=['websocket'])
    sio.wait()

threading.Thread(target=network_thread, daemon=True).start()

def draw():
    screen.fill((0,0,0))
    for food in state.get("foods", []):
        pygame.draw.circle(screen, tuple(food["color"]), (int(food["x"]), int(food["y"])), food["mass"])
    for pid, p in state.get("players", {}).items():
        pygame.draw.circle(screen, tuple(p["color"]), (int(p["x"]), int(p["y"])), p["mass"])
    pygame.display.flip()

def mainloop():
    while True:
        dx = dy = 0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]: dx -= 5
        if keys[pygame.K_RIGHT]: dx += 5
        if keys[pygame.K_UP]: dy -= 5
        if keys[pygame.K_DOWN]: dy += 5
        if dx or dy:
            send_move(dx, dy)
        draw()
        clock.tick(60)

time.sleep(2)  # Ждём подключения к серверу
mainloop() 