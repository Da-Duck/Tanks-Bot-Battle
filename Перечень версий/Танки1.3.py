import tkinter as tk
from tkinter import ttk
import time
import math
import random
import json
import socket
import threading


# КОНФИГУРАЦИЯ ИГРЫ - Все настройки и параметры в одном месте

CONFIG = {
    'window': {
        'width': 1280,
        'height': 720,
        'title': "Танки. Битва ботов",
        'bg': "#228B22"
    },

    'tank': {
        'size_w': 24,
        'size_h': 16,
        'inner_w': 20,
        'inner_h': 12,
        'speed': 4,
        'rotation_speed': 0.1,
        'max_hp': 3,
        'shoot_cooldown': 400,
        'fov': 260,
    },

    'bullet': {
        'speed': 10,
        'size': 4,
        'range': 260,
    },

    'obstacles': {
        'wall_count': 15,
        'water_count': 5,
        'destructible_count': 10,
        'min_size': 50,
        'max_size': 120,
        'obstacle_multiplier': 1.0,
    },

    'colors': {
        'wall_fill': "#8B4513",
        'wall_outline': "#654321",
        'water_fill': "#1E90FF",
        'water_outline': "#0000CD",
        'destructible_fill': "#DC143C",
        'destructible_outline': "#8B0000",
        'tank_colors': ["#0066CC", "#CC0000", "#FFD700", "#00FF00", "#FF00FF", "#00FFFF", "#FF6600", "#00FF66"],
        'bullet_fill': "#FFD700",
        'bullet_outline': "#FF8C00",
        'fov_outline': "#FF4444",
        'hp_bg': "black",
        'hp_outline': "white",
        'hp_full': "green",
        'hp_mid': "orange",
        'hp_low': "red",
    },

    'game': {
        'tank_count': 4,
        'fps': 50,
        'game_mode': 'ffa',
        'total_games': 1,
        'show_gui_after': True,
    },

    'network': {
        'ip': '127.0.0.1',
        'port': 5000,
        'enabled': False,
        'update_interval': 100,
    }
}


# ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ

w = None                    # Главное окно приложения
game_canvas = None          # Canvas для рисования игры
game_paused = False         # Состояние паузы
current_game = 1            # Текущий номер игры
total_games = 1             # Всего игр
game_speed = 1.0            # Множитель скорости игры

# Список препятствий
WALLS = []                  # Стены (непроходимые)
WATER = []                  # Вода (непроходимая)
DESTRUCTIBLES = []          # Разрушаемые блоки

# Список игровых объектов
TANKS = []                  # Все танки в игре
BULLETS = []                # Все пули в игре

# Состояние ввода
KEYS = set()                # Нажатые клавиши

# Состояние игры
game_over = False           # Флаг окончания игры
btn_pause = None            # Кнопка паузы
btn_exit = None             # Кнопка выхода
btn_new_game = None         # Кнопка новой игры
label_pause = None          # Метка "ПАУЗА"

# Статистика
stats_log = []              # Лог событий
TANK_STATS = {}             # Статистика каждого танка {tank_id: {kills, deaths}}
TANK_WINS = {}              # Количество побед каждого танка



# КЛАСС ТАНКА - Основной класс для игрока и ботов

class Tank:
    # Инициализация танка с позицией, цветом и AI
    def __init__(self, x, y, color_idx, tank_id, ai=True, team=0):
        self.x = x                              # X позиция
        self.y = y                              # Y позиция
        self.hp = CONFIG['tank']['max_hp']      # Здоровье
        self.angle = 0                          # Угол поворота
        self.last_shot = 0                      # Время последнего выстрела
        self.color_idx = color_idx              # Индекс цвета танка
        self.tank_id = tank_id                  # ID танка
        self.ai = ai                            # Это бот?
        self.team = team                        # Команда (0 или 1)

        # Инициализация статистики если этого еще нет
        if tank_id not in TANK_STATS:
            TANK_STATS[tank_id] = {'kills': 0, 'deaths': 0}
        if tank_id not in TANK_WINS:
            TANK_WINS[tank_id] = 0

    # Возвращает цвет танка по индексу
    def get_color(self):
        return CONFIG['colors']['tank_colors'][self.color_idx % len(CONFIG['colors']['tank_colors'])]

    # Сохранить танка в JSON формате
    def to_json(self):
        return {
            'tank_id': self.tank_id,
            'x': self.x,
            'y': self.y,
            'hp': self.hp,
            'angle': self.angle,
            'color_idx': self.color_idx,
            'team': self.team,
        }

    # Обновить позицию танка (вызывается каждый кадр)
    def update_position(self, keys, walls, water, tanks, destructibles):
        if self.ai:
            self.bot_think(tanks, walls, water, destructibles)
        else:
            self.player_think(keys, walls, water, tanks, destructibles)

    # Логика управления игроком: WASD для движения, AD для поворота
    def player_think(self, keys, walls, water, tanks, destructibles):
        if 'a' in keys:
            self.angle -= CONFIG['tank']['rotation_speed']
        if 'd' in keys:
            self.angle += CONFIG['tank']['rotation_speed']

        speed = CONFIG['tank']['speed']
        if 'w' in keys:
            self.try_move(speed, walls, water, tanks, destructibles)
        if 's' in keys:
            self.try_move(-speed, walls, water, tanks, destructibles)

    # Логика ИИ для ботов: ищет врага и атакует
    def bot_think(self, tanks, walls, water, destructibles):
        if len(tanks) < 2:
            return

        # Найти всех врагов
        enemies = [t for t in tanks if t != self]
        if not enemies:
            return

        # Выбрать ближайшего врага
        enemy = min(enemies, key=lambda t: math.hypot(t.x - self.x, t.y - self.y))

        # Рассчитать угол на врага
        dx = enemy.x - self.x
        dy = enemy.y - self.y
        target_angle = math.atan2(dy, dx)
        angle_diff = (target_angle - self.angle + math.pi) % (2 * math.pi) - math.pi

        # Повернуться на врага или двигаться к нему
        if abs(angle_diff) > 0.05:
            self.angle += CONFIG['tank']['rotation_speed'] * (1 if angle_diff > 0 else -1) / 2
        else:
            speed = CONFIG['tank']['speed'] * 0.75
            self.try_move(speed, walls, water, tanks, destructibles)

        # Выстрелить если враг в поле зрения
        dist = math.hypot(dx, dy)
        if dist < CONFIG['tank']['fov']:
            self.try_shoot(self)

    # Попытка переместить танк с проверкой коллизий
    def try_move(self, speed, walls, water, tanks, destructibles):
        nx = self.x + math.cos(self.angle) * speed
        ny = self.y + math.sin(self.angle) * speed

        if self.is_valid_position(nx, ny, walls, water, tanks, destructibles):
            self.x = nx
            self.y = ny

    # Проверить валидность позиции (нет коллизий, в пределах карты)
    def is_valid_position(self, x, y, walls, water, tanks, destructibles):
        sz = CONFIG['tank']['size_w']

        # Проверка границ карты
        if not (20 < x < CONFIG['window']['width'] - 20 and 20 < y < CONFIG['window']['height'] - 20):
            return False

        # Проверка коллизий со стенами и водой
        if check_collision(x, y, sz, walls) or check_collision(x, y, sz, water):
            return False

        # Проверка коллизий с разрушаемыми блоками
        for d_rect, d_obj in destructibles:
            if d_rect[0] < x < d_rect[2] and d_rect[1] < y < d_rect[3]:
                return False

        # Проверка коллизий с другими танками
        for t in tanks:
            if t != self:
                if abs(x - t.x) < sz and abs(y - t.y) < sz:
                    return False

        return True

    # Выстрелить пулей с ограничением по времени
    def try_shoot(self, owner):
        now = time.time() * 1000
        if now - self.last_shot > CONFIG['tank']['shoot_cooldown']:
            # Рассчитать направление пули
            dx = math.cos(self.angle) * CONFIG['bullet']['speed']
            dy = math.sin(self.angle) * CONFIG['bullet']['speed']
            bx = self.x + dx * 2
            by = self.y + dy * 2

            # Создать пулю на canvas
            bullet = game_canvas.create_oval(
                bx - CONFIG['bullet']['size'],
                by - CONFIG['bullet']['size'],
                bx + CONFIG['bullet']['size'],
                by + CONFIG['bullet']['size'],
                fill=CONFIG['colors']['bullet_fill'],
                outline=CONFIG['colors']['bullet_outline'],
                width=2
            )

            # Добавить в список пуль [x, y, dx, dy, canvas_id, owner]
            BULLETS.append([bx, by, dx, dy, bullet, owner])
            self.last_shot = now



# ФУНКЦИИ ДЛЯ ПРЕПЯТСТВИЙ


# Проверить пересечение двух прямоугольников
def intersects(r1, r2):
    return not (r1[2] <= r2[0] or r1[0] >= r2[2] or r1[3] <= r2[1] or r1[1] >= r2[3])


# Создать все препятствия на карте (стены, вода, блоки)
def create_obstacles():
    global WALLS, WATER, DESTRUCTIBLES
    WALLS.clear()
    WATER.clear()
    DESTRUCTIBLES.clear()
    areas = []  # Уже занятые области

    # Множитель для сложности
    mult = CONFIG['obstacles']['obstacle_multiplier']
    wall_count = max(1, int(CONFIG['obstacles']['wall_count'] * mult))
    water_count = max(1, int(CONFIG['obstacles']['water_count'] * mult))
    dest_count = max(1, int(CONFIG['obstacles']['destructible_count'] * mult))

    # Создать стены
    for _ in range(wall_count):
        rect = generate_obstacle(areas, WALLS, 'wall_fill', 'wall_outline')
        if rect:
            areas.append(rect)

    # Создать воду
    for _ in range(water_count):
        rect = generate_obstacle(areas, WATER, 'water_fill', 'water_outline')
        if rect:
            areas.append(rect)

    # Создать разрушаемые блоки
    for _ in range(dest_count):
        sz = random.randint(20, 30)
        x1 = random.randint(100, max(101, CONFIG['window']['width'] - 100 - sz))
        y1 = random.randint(80, max(81, CONFIG['window']['height'] - 80 - sz))
        x2 = x1 + sz
        y2 = y1 + sz
        rect = (x1, y1, x2, y2)

        # Проверить пересечение с существующими
        if any(intersects(rect, a) for a in areas):
            continue

        areas.append(rect)
        obj = game_canvas.create_rectangle(
            x1, y1, x2, y2,
            fill=CONFIG['colors']['destructible_fill'],
            outline=CONFIG['colors']['destructible_outline'],
            width=2
        )
        DESTRUCTIBLES.append([rect, obj])


# Генерировать случайное препятствие
def generate_obstacle(areas, obstacle_list, fill_key, outline_key):
    x1 = random.randint(100, max(101, CONFIG['window']['width'] - 200))
    y1 = random.randint(80, max(81, CONFIG['window']['height'] - 200))
    w = random.randint(CONFIG['obstacles']['min_size'], CONFIG['obstacles']['max_size'])
    h = random.randint(CONFIG['obstacles']['min_size'], CONFIG['obstacles']['max_size'])
    x2 = min(x1 + w, CONFIG['window']['width'] - 50)
    y2 = min(y1 + h, CONFIG['window']['height'] - 50)
    rect = (x1, y1, x2, y2)

    # Проверить пересечение с другими
    if any(intersects(rect, a) for a in areas):
        return None

    # Рисовать на canvas
    game_canvas.create_rectangle(
        x1, y1, x2, y2,
        fill=CONFIG['colors'][fill_key],
        outline=CONFIG['colors'][outline_key],
        width=3
    )
    obstacle_list.append(rect)
    return rect



# ФУНКЦИИ ДЛЯ РИСОВАНИЯ ТАНКОВ


# Полная функция рисования танка со всеми компонентами
def draw_tank(tank):
    if tank.hp <= 0:
        return

    fov = CONFIG['tank']['fov']
    # Рисовать поле зрения
    game_canvas.create_oval(
        tank.x - fov, tank.y - fov, tank.x + fov, tank.y + fov,
        outline=CONFIG['colors']['fov_outline'],
        width=2,
        tags="tank"
    )

    draw_tank_body(tank)
    draw_tank_turret(tank)
    draw_tank_barrel(tank)
    draw_tank_hp(tank)


# Рисовать корпус танка (повернутый прямоугольник)
def draw_tank_body(tank):
    w, h = CONFIG['tank']['size_w'], CONFIG['tank']['size_h']
    corners = [(-w/2, -h/2), (w/2, -h/2), (w/2, h/2), (-w/2, h/2)]
    body_points = []

    # Повернуть углы на угол танка
    for cx, cy in corners:
        rx = tank.x + cx * math.cos(tank.angle) - cy * math.sin(tank.angle)
        ry = tank.y + cx * math.sin(tank.angle) + cy * math.cos(tank.angle)
        body_points.extend([rx, ry])

    game_canvas.create_polygon(body_points, fill="#2F4F2F", outline="black", width=2, tags="tank")

    # Внутренняя часть корпуса (цветная)
    w2, h2 = CONFIG['tank']['inner_w'], CONFIG['tank']['inner_h']
    corners2 = [(-w2/2, -h2/2), (w2/2, -h2/2), (w2/2, h2/2), (-w2/2, h2/2)]
    inner_points = []

    for cx, cy in corners2:
        rx = tank.x + cx * math.cos(tank.angle) - cy * math.sin(tank.angle)
        ry = tank.y + cx * math.sin(tank.angle) + cy * math.cos(tank.angle)
        inner_points.extend([rx, ry])

    game_canvas.create_polygon(inner_points, fill=tank.get_color(), outline="black", width=2, tags="tank")


# Рисовать башню танка (круг)
def draw_tank_turret(tank):
    game_canvas.create_oval(
        tank.x - 6, tank.y - 6, tank.x + 6, tank.y + 6,
        fill=tank.get_color(),
        outline="black",
        width=2,
        tags="tank"
    )


# Рисовать дуло танка (линия)
def draw_tank_barrel(tank):
    dx = math.cos(tank.angle)
    dy = math.sin(tank.angle)
    game_canvas.create_line(
        tank.x, tank.y, tank.x + 20 * dx, tank.y + 20 * dy,
        fill="black",
        width=4,
        tags="tank"
    )


# Рисовать полоску здоровья над танком
def draw_tank_hp(tank):
    # Выбрать цвет полоски в зависимости от здоровья
    hp_color = CONFIG['colors']['hp_full'] if tank.hp == 3 else CONFIG['colors']['hp_mid'] if tank.hp == 2 else CONFIG['colors']['hp_low']

    # Фоновая полоска
    game_canvas.create_rectangle(
        tank.x - 12, tank.y - 18, tank.x + 12, tank.y - 14,
        fill=CONFIG['colors']['hp_bg'],
        outline=CONFIG['colors']['hp_outline'],
        tags="tank"
    )

    # Заполненная часть полоски
    bar_width = int((tank.hp / CONFIG['tank']['max_hp']) * 24)
    game_canvas.create_rectangle(
        tank.x - 12, tank.y - 18, tank.x - 12 + bar_width, tank.y - 14,
        fill=hp_color,
        tags="tank"
    )

    # Текст с количеством HP
    game_canvas.create_text(
        tank.x, tank.y - 25,
        text=f"HP: {tank.hp}",
        font=("Segoe UI", 10, "bold"),
        fill="white",
        tags="tank"
    )



# ФУНКЦИИ ВВОДА-ВЫВОДА


# Обработка нажатия клавиши
def key_press(event):
    KEYS.add(event.keysym.lower())


# Обработка отпускания клавиши
def key_release(event):
    KEYS.discard(event.keysym.lower())



# ФУНКЦИИ ДЛЯ ПУЛЬ И КОЛЛИЗИЙ

# Проверить коллизию круга (точки) с препятствиями
def check_collision(x, y, size, obstacles):
    for ox1, oy1, ox2, oy2 in obstacles:
        if x - size / 2 < ox2 and x + size / 2 > ox1 and y - size / 2 < oy2 and y + size / 2 > oy1:
            return True
    return False


# Обновить все пули: движение, проверка коллизий, удаление
def update_bullets():
    global game_over

    # Обновить каждую пулю
    for b in BULLETS[:]:
        # Переместить пулю
        b[0] += b[2]
        b[1] += b[3]
        game_canvas.coords(b[4], b[0] - CONFIG['bullet']['size'], b[1] - CONFIG['bullet']['size'],
                 b[0] + CONFIG['bullet']['size'], b[1] + CONFIG['bullet']['size'])

        # Проверить условия удаления пули
        out_of_bounds = b[0] < 0 or b[0] > CONFIG['window']['width'] or b[1] < 0 or b[1] > CONFIG['window']['height']
        hit_wall = check_collision(b[0], b[1], 1, WALLS)
        hit_water = check_collision(b[0], b[1], 1, WATER)
        hit_fov = math.hypot(b[0] - b[5].x, b[1] - b[5].y) > CONFIG['tank']['fov']

        # Проверить попадание в разрушаемые блоки
        hit_dest = False
        for d_rect, d_obj in DESTRUCTIBLES:
            if d_rect[0] < b[0] < d_rect[2] and d_rect[1] < b[1] < d_rect[3]:
                hit_dest = True
                game_canvas.delete(d_obj)
                DESTRUCTIBLES.remove([d_rect, d_obj])
                break

        # Удалить пулю если она вышла за пределы
        if out_of_bounds or hit_wall or hit_water or hit_dest or hit_fov:
            game_canvas.delete(b[4])
            BULLETS.remove(b)
            continue

        # Проверить попадание в танки
        for t in TANKS:
            if t != b[5] and abs(b[0] - t.x) < CONFIG['tank']['size_w'] and abs(b[1] - t.y) < CONFIG['tank']['size_h']:
                t.hp = max(t.hp - 1, 0)
                game_canvas.delete(b[4])
                BULLETS.remove(b)

                # Обновить статистику
                TANK_STATS[b[5].tank_id]['kills'] += 1

                if t.hp <= 0:
                    TANK_STATS[t.tank_id]['deaths'] += 1
                    check_game_over()
                break


# Проверить окончание игры (остался 1 или 0 танков живых)
def check_game_over():
    global game_over
    alive = [t for t in TANKS if t.hp > 0]
    if len(alive) <= 1:
        game_over = True
        winner = alive[0] if alive else None
        show_game_over(winner)



# ФУНКЦИИ ОТРИСОВКИ ЭКРАНА


# Проверить видимость точки в поле зрения (круг)
def is_visible(x, y, cx, cy, r):
    return (x - cx) ** 2 + (y - cy) ** 2 <= r ** 2


# Отрисовать всю игру: карта, препятствия, танки
def update_display():
    game_canvas.delete("tank")

    fov = CONFIG['tank']['fov']
    visible_obstacles = set()

    # Найти видимые препятствия для всех танков
    for t in TANKS:
        if t.hp > 0:
            for w in WALLS:
                if is_visible((w[0] + w[2]) / 2, (w[1] + w[3]) / 2, t.x, t.y, fov):
                    visible_obstacles.add(('wall', w))

            for w in WATER:
                if is_visible((w[0] + w[2]) / 2, (w[1] + w[3]) / 2, t.x, t.y, fov):
                    visible_obstacles.add(('water', w))

            for d, o in DESTRUCTIBLES:
                if is_visible((d[0] + d[2]) / 2, (d[1] + d[3]) / 2, t.x, t.y, fov):
                    visible_obstacles.add(('destructible', d))

    # Нарисовать видимые препятствия
    for obs_type, obs in visible_obstacles:
        if obs_type == 'wall':
            game_canvas.create_rectangle(obs[0], obs[1], obs[2], obs[3],
                             fill=CONFIG['colors']['wall_fill'],
                             outline=CONFIG['colors']['wall_outline'],
                             width=3, tags="tank")
        elif obs_type == 'water':
            game_canvas.create_rectangle(obs[0], obs[1], obs[2], obs[3],
                             fill=CONFIG['colors']['water_fill'],
                             outline=CONFIG['colors']['water_outline'],
                             width=3, tags="tank")
        elif obs_type == 'destructible':
            game_canvas.create_rectangle(obs[0], obs[1], obs[2], obs[3],
                             fill=CONFIG['colors']['destructible_fill'],
                             outline=CONFIG['colors']['destructible_outline'],
                             width=2, tags="tank")

    # Нарисовать все танки
    for t in TANKS:
        draw_tank(t)


# Нарисовать статистику в левом верхнем углу
def draw_stats():
    y_offset = 10
    game_canvas.create_text(10, y_offset, anchor="nw", text="🎮 СТАТИСТИКА 🎮", font=("Segoe UI", 12, "bold"), fill="white")
    y_offset += 25

    # Нарисовать статистику каждого танка
    for tank_id in sorted(TANK_STATS.keys()):
        kills = TANK_STATS[tank_id]['kills']
        deaths = TANK_STATS[tank_id]['deaths']
        wins = TANK_WINS.get(tank_id, 0)
        color = CONFIG['colors']['tank_colors'][tank_id % len(CONFIG['colors']['tank_colors'])]

        text = f"🚀 Танк {tank_id + 1}: 💀{deaths} ⚔️{kills} 🏆{wins}"
        game_canvas.create_text(10, y_offset, anchor="nw", text=text, font=("Segoe UI", 10), fill=color)
        y_offset += 20

    # Нарисовать информацию о текущей игре
    game_canvas.create_text(10, CONFIG['window']['height'] - 30, anchor="nw", 
                 text=f"🎯 Игра {current_game}/{total_games}", 
                 font=("Segoe UI", 11, "bold"), fill="yellow")



# ФУНКЦИИ УПРАВЛЕНИЯ ИГРОЙ


# Переключить паузу
def toggle_pause():
    global game_paused, label_pause
    game_paused = not game_paused

    if game_paused:
        label_pause = tk.Label(w, text="⏸️  ПАУЗА  ⏸️", font=("Segoe UI", 36, "bold"), fg="red", bg="#228B22")
        label_pause.place(x=CONFIG['window']['width']//2 - 150, y=CONFIG['window']['height']//2 - 60, width=300, height=120)
        btn_pause.config(text="▶️  Продолжить  ▶️")
    else:
        if label_pause:
            label_pause.destroy()
        btn_pause.config(text="⏸️  Пауза  ⏸️")


# Выход из игры
def exit_game():
    global game_over
    game_over = True


# Перезагрузить игру
def restart_game():
    global TANKS, BULLETS, KEYS, game_over, btn_pause, btn_exit, btn_new_game, label_pause
    global WALLS, WATER, DESTRUCTIBLES, stats_log, game_speed, game_canvas

    # Очистить все списки
    TANKS = []
    BULLETS = []
    KEYS = set()
    game_over = False
    WALLS = []
    WATER = []
    DESTRUCTIBLES = []
    stats_log = []
    game_speed = 1.0

    # Создать танки и препятствия
    spawn_tanks()
    create_obstacles()

    # Очистить кнопки если они были
    if btn_pause:
        btn_pause.destroy()
        btn_pause = None
    if btn_exit:
        btn_exit.destroy()
        btn_exit = None
    if btn_new_game:
        btn_new_game.destroy()
        btn_new_game = None
    if label_pause:
        label_pause.destroy()

    game_canvas.delete("all")

    create_game_buttons()

    game_loop()


# Создать кнопки паузы и выхода
def create_game_buttons():
    global btn_pause, btn_exit
    btn_pause = tk.Button(w, text="⏸️  Пауза  ⏸️", font=("Segoe UI", 9, "bold"), command=toggle_pause, bg="#0066CC", fg="white")
    btn_pause.place(x=10, y=CONFIG['window']['height'] - 40, width=150, height=35)

    btn_exit = tk.Button(w, text="🚪  Выход  🚪", font=("Segoe UI", 9, "bold"), command=exit_game, bg="#DD0000", fg="white")
    btn_exit.place(x=170, y=CONFIG['window']['height'] - 40, width=150, height=35)


# Спозиционировать танки на карте в разных местах
def spawn_tanks():
    global TANKS
    positions = [
        (100, 100),
        (CONFIG['window']['width'] - 100, CONFIG['window']['height'] - 100),
        (100, CONFIG['window']['height'] - 100),
        (CONFIG['window']['width'] - 100, 100),
        (CONFIG['window']['width'] // 2, 100),
        (CONFIG['window']['width'] // 2, CONFIG['window']['height'] - 100),
        (100, CONFIG['window']['height'] // 2),
        (CONFIG['window']['width'] - 100, CONFIG['window']['height'] // 2),
    ]

    for i in range(CONFIG['game']['tank_count']):
        x, y = positions[i % len(positions)]
        team = 0 if i < CONFIG['game']['tank_count'] // 2 else 1
        TANKS.append(Tank(x, y, i, tank_id=i, ai=True, team=team))


# Показать экран окончания игры
def show_game_over(winner):
    global game_over, btn_pause, btn_exit, btn_new_game, label_pause

    # Удалить кнопки
    if btn_pause:
        btn_pause.destroy()
        btn_pause = None
    if btn_exit:
        btn_exit.destroy()
        btn_exit = None
    if label_pause:
        label_pause.destroy()
        label_pause = None

    game_over = True
    game_canvas.delete("all")

    # Показать победителя
    if winner:
        text = f"🏆 ПОБЕДИТЕЛЬ: Танк {winner.color_idx + 1}! 🏆"
        TANK_WINS[winner.tank_id] += 1
    else:
        text = "⚔️ НИЧЬЯ! ⚔️"

    label = tk.Label(w, text=text, font=("Segoe UI", 28, "bold"), fg="#FFD700", bg="#111111", relief="solid", bd=2)
    label.place(x=250, y=280, width=780, height=80)

    btn_new_game = tk.Button(w, text="🎮  НОВАЯ ИГРА  🎮", font=("Segoe UI", 13, "bold"), 
                             command=handle_new_game, bg="#00AA00", fg="#FFFFFF", relief="flat", bd=0)
    btn_new_game.place(x=350, y=400, width=580, height=50)


# Обработчик для новой игры
def handle_new_game():
    global current_game
    close_game_window()
    current_game = 1
    open_settings_gui()



# ОСНОВНОЙ ИГРОВОЙ ЦИКЛ


# Основной цикл игры (вызывается каждый кадр)
def game_loop():
    global game_over, current_game, total_games

    # Если игра закончилась
    if game_over:
        w.after(2000, lambda: handle_game_end())
        return

    # Обновить позиции танков и пуль если игра не на паузе
    if not game_paused:
        # Обновить каждый танк
        for t in TANKS:
            if t.hp > 0:
                t.update_position(KEYS, WALLS, WATER, TANKS, DESTRUCTIBLES)
                if 'space' in KEYS and not t.ai:
                    t.try_shoot(t)

        # Обновить пули
        update_bullets()

    # Отрисовать игру
    update_display()
    draw_stats()

    # Вызвать себя через некоторое время
    if not game_over:
        delay = int((1000 / CONFIG['game']['fps']) / game_speed)
        w.after(delay, game_loop)


# Обработчик конца игры
def handle_game_end():
    global current_game, total_games, game_over

    # Если еще остались игры
    current_game += 1
    if current_game <= total_games:
        restart_game()
    else:
        close_game_window()
        open_settings_gui()


# Закрыть окно игры и вернуть меню
def close_game_window():
    global game_canvas, btn_pause, btn_exit, btn_new_game, label_pause

    # Удалить все кнопки
    if btn_pause:
        btn_pause.destroy()
        btn_pause = None
    if btn_exit:
        btn_exit.destroy()
        btn_exit = None
    if btn_new_game:
        btn_new_game.destroy()
        btn_new_game = None
    if label_pause:
        label_pause.destroy()
        label_pause = None

    # Удалить canvas
    if game_canvas:
        game_canvas.destroy()
        game_canvas = None

    # Скрыть окно
    w.withdraw()


# Открыть окно игры
def open_game_window():
    global game_canvas

    w.state('zoomed')
    w.geometry(f"{CONFIG['window']['width']}x{CONFIG['window']['height']}")
    w.deiconify()

    game_canvas = tk.Canvas(w, width=CONFIG['window']['width'], height=CONFIG['window']['height'], 
                           bg=CONFIG['window']['bg'], highlightthickness=0)
    game_canvas.pack()

    restart_game()


# КЛАСС МЕНЮ НАСТРОЕК

class SettingsGUI:
    # Инициализация окна настроек
    def __init__(self, root):
        self.root = root
        self.window = tk.Toplevel(root)
        self.window.title("⚙️ Танки. Битва ботов")
        self.window.geometry("500x720")
        self.window.resizable(False, False)
        self.window.config(bg="#111111")

        # Центрировать окно на экране
        screen_w = self.window.winfo_screenwidth()
        screen_h = self.window.winfo_screenheight()
        x = (screen_w - 500) // 2
        y = (screen_h - 720) // 2
        self.window.geometry(f"500x720+{x}+{y}")

        self.build_ui()

    # Установить значение в Spinbox
    def set_spinbox_value(self, spinbox, value):
        spinbox.delete(0, tk.END)
        spinbox.insert(0, str(value))

    # Построить UI меню
    def build_ui(self):
        frm = tk.Frame(self.window, bg="#111111")
        frm.pack(fill="both", expand=True, padx=0, pady=0)

        row = 0

        # Заголовок
        title = tk.Label(
            frm, text="⚙️ ТАНКИ. БИТВА БОТОВ ⚙️",
            font=("Segoe UI", 16, "bold"), fg="#FFD700", bg="#111111"
        )
        title.grid(row=row, column=0, columnspan=2, pady=20)
        row += 1

        # Список параметров с метаданными: (текст, атрибут, минимум, максимум, текущее значение)
        items = [
            ("🎮 Кол-во танков(2-8):", "tc", 2, 8, CONFIG['game']['tank_count']),
            ("🎯 Кол-во игр:", "gc", 2, 8, CONFIG['game']['total_games']),
            ("📏 Ширина поля:", "wd", 800, 1280, CONFIG['window']['width']),
            ("📏 Высота поля:", "ht", 600, 720, CONFIG['window']['height']),
            ("❤  Здоровье танка:", "hp", 1, 10, CONFIG['tank']['max_hp']),
            ("👁 Поле зрения танка:", "fv", 100, 500, CONFIG['tank']['fov']),
            ("🎯 Дальность выстрела:", "rg", 50, 500, CONFIG['bullet']['range']),
        ]

        # Создать элементы для каждого параметра
        for label_text, attr_name, min_val, max_val, curr_val in items:
            # Метка
            tk.Label(frm, text=label_text, fg="#FFFFFF", bg="#111111", 
                    font=("Segoe UI", 11, "bold")).grid(row=row, column=0, sticky="w", padx=25, pady=12)

            # Кнопка минус
            btn_minus = tk.Button(frm, text="−", font=("Segoe UI", 10, "bold"), bg="#DD0000", fg="white", 
                                 width=3, command=lambda attr=attr_name, mn=min_val: self.dec_value(attr, mn))
            btn_minus.grid(row=row, column=1, padx=2, pady=12, sticky="w")

            # Поле ввода (Spinbox)
            sb = tk.Spinbox(frm, from_=min_val, to=max_val, width=8,
                           bg="#222222", fg="#FFFFFF", font=("Segoe UI", 11, "bold"), bd=1)
            self.set_spinbox_value(sb, curr_val)
            sb.grid(row=row, column=1, padx=2, pady=12)

            # Кнопка плюс
            btn_plus = tk.Button(frm, text="+", font=("Segoe UI", 10, "bold"), bg="#00AA00", fg="white", 
                                width=3, command=lambda attr=attr_name, mx=max_val: self.inc_value(attr, mx))
            btn_plus.grid(row=row, column=1, padx=2, pady=12, sticky="e")

            setattr(self, attr_name, sb)
            row += 1

        # Препятствия (слайдер)
        tk.Label(frm, text="🧱 Препятствия:", fg="#FFFFFF", bg="#111111", 
                font=("Segoe UI", 11, "bold")).grid(row=row, column=0, sticky="w", padx=25, pady=12)
        self.om = tk.Scale(frm, from_=0.5, to=2.0, resolution=0.1, orient="horizontal",
                          bg="#222222", fg="#FFFFFF", troughcolor="#333333", highlightthickness=0)
        self.om.set(CONFIG['obstacles']['obstacle_multiplier'])
        self.om.grid(row=row, column=1, padx=25, pady=12, sticky="ew")
        row += 1

        # IP адрес
        tk.Label(frm, text="🌐 IP адрес:", fg="#FFFFFF", bg="#111111", 
                font=("Segoe UI", 11, "bold")).grid(row=row, column=0, sticky="w", padx=25, pady=12)
        self.ip = tk.Entry(frm, width=12, bg="#222222", fg="#FFFFFF", 
                          font=("Segoe UI", 11, "bold"), bd=1, insertbackground='white')
        self.ip.insert(0, CONFIG['network']['ip'])
        self.ip.grid(row=row, column=1, padx=25, pady=12, sticky="ew")
        row += 1

        # Порт
        tk.Label(frm, text="🔌 Порт:", fg="#FFFFFF", bg="#111111", 
                font=("Segoe UI", 11, "bold")).grid(row=row, column=0, sticky="w", padx=25, pady=12)
        self.pt = tk.Entry(frm, width=12, bg="#222222", fg="#FFFFFF", 
                          font=("Segoe UI", 11, "bold"), bd=1, insertbackground='white')
        self.pt.insert(0, str(CONFIG['network']['port']))
        self.pt.grid(row=row, column=1, padx=25, pady=12, sticky="ew")
        row += 1

        # Кнопка начала игры
        btn = tk.Button(frm, text="▶️ НАЧАТЬ ИГРУ ▶️",
                       font=("Segoe UI", 13, "bold"), bg="#00AA00", fg="#FFFFFF",
                       command=self.start_game, activebackground="#00DD00", relief="flat", bd=0)
        btn.grid(row=row, column=0, columnspan=2, pady=25, padx=25, sticky="ew")

    # Увеличить значение параметра на 1
    def inc_value(self, attr_name, max_val):
        sb = getattr(self, attr_name)
        curr = int(sb.get())
        new_val = min(curr + 1, max_val)
        self.set_spinbox_value(sb, new_val)

    # Уменьшить значение параметра на 1
    def dec_value(self, attr_name, min_val):
        sb = getattr(self, attr_name)
        curr = int(sb.get())
        new_val = max(curr - 1, min_val)
        self.set_spinbox_value(sb, new_val)

    # Запустить игру с выбранными параметрами
    def start_game(self):
        global CONFIG, current_game, total_games

        # Обновить конфиг из полей ввода
        CONFIG['game']['tank_count'] = int(self.tc.get())
        CONFIG['game']['total_games'] = int(self.gc.get())
        CONFIG['window']['width'] = int(self.wd.get())
        CONFIG['window']['height'] = int(self.ht.get())
        CONFIG['obstacles']['obstacle_multiplier'] = self.om.get()
        CONFIG['tank']['fov'] = int(self.fv.get())
        CONFIG['tank']['max_hp'] = int(self.hp.get())
        CONFIG['bullet']['range'] = int(self.rg.get())
        CONFIG['network']['ip'] = self.ip.get()
        try:
            CONFIG['network']['port'] = int(self.pt.get())
        except:
            CONFIG['network']['port'] = 5000

        current_game = 1
        total_games = CONFIG['game']['total_games']

        self.window.destroy()
        open_game_window()


# Открыть меню настроек
def open_settings_gui():
    global w
    SettingsGUI(w)


# ГЛАВНАЯ ФУНКЦИЯ

# Главная функция запуска приложения
def main():
    global w

    # Создать главное окно
    w = tk.Tk()
    w.title("Танки. Битва ботов")
    w.withdraw()  # Спрятать окно в начале

    # Привязать события клавиатуры
    w.bind("<KeyPress>", key_press)
    w.bind("<KeyRelease>", key_release)
    w.focus_set()

    # Открыть меню настроек
    open_settings_gui()
    w.mainloop()


if __name__ == "__main__":
    main()