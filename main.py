import tkinter as tk
from tkinter import ttk, messagebox
import time
import math
import random
import json
import socket
import threading
import sys
import os

# ============== КОНФИГ ==============

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
        'total_games': 3,
        'show_gui_after': True,
    },
    'network': {
        # ВАЖНО: 0.0.0.0 слушает все интерфейсы — боты могут подключаться с других машин
        'ip': '0.0.0.0',
        'port': 5000,
        'enabled': True,
        'update_interval': 100,   # ms — частота рассылки состояния удалённым ботам
    }
}

# ============== ГЛОБАЛЫ ==============

w = None
game_canvas = None
game_paused = False
current_game = 1
total_games = CONFIG['game']['total_games']
game_speed = 1.0

WALLS = []
WATER = []
DESTRUCTIBLES = []
TANKS = []
BULLETS = []
KEYS = set()

game_over = False
btn_pause = None
btn_exit = None
btn_new_game = None
label_pause = None

stats_log = []
TANK_STATS = {}
TANK_WINS = {}

# -------- сеть --------

NET_SERVER = None     # экземпляр Server
WAIT_WIN = None       # окно "Ожидание ботов"
NET_LAST_BROADCAST_TS = 0.0  # троттлинг рассылки

# ============== СЕТЬ ==============

class RemoteClient:
    def __init__(self, sock, addr, tank_id):
        self.sock = sock
        self.addr = addr
        self.tank_id = tank_id
        self.cmd = ""       # последняя строка команд
        self.alive = True
        self.file = sock.makefile('r', encoding='utf-8', newline='\n')
        self.t = threading.Thread(target=self.reader, daemon=True)
        self.t.start()

    def reader(self):
        try:
            while self.alive:
                line = self.file.readline()
                if not line:
                    break
                line = line.strip()
                if not line:
                    continue
                # допускаем JSON {"cmd":"rfs"} или просто "rfs"
                if line.startswith('{'):
                    try:
                        j = json.loads(line)
                        self.cmd = j.get('cmd', '')
                    except Exception:
                        self.cmd = ''
                else:
                    self.cmd = line
        except Exception:
            pass
        finally:
            self.alive = False
            try:
                self.sock.close()
            except Exception:
                pass


class Server:
    def __init__(self, host, port, expected):
        self.host = host
        self.port = port
        self.expected = expected
        self.sock = None
        self.accept_th = None
        self.clients = {}       # tank_id -> RemoteClient
        self.lock = threading.Lock()
        self.running = False

    def start(self):
        self.running = True
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            # Не везде поддерживается, потому — best-effort
            self.sock.setsockopt(socket.SOL_SOCKET, getattr(socket, "SO_REUSEPORT", 15), 1)
        except Exception:
            pass
        self.sock.bind((self.host, self.port))
        self.sock.listen(16)
        self.accept_th = threading.Thread(target=self.accept_loop, daemon=True)
        self.accept_th.start()

    def stop(self):
        self.running = False
        try:
            if self.sock:
                self.sock.close()
        except Exception:
            pass

    def accept_loop(self):
        while self.running:
            try:
                s, a = self.sock.accept()
            except OSError:
                break
            with self.lock:
                used = set(self.clients.keys())
                # если уже все места заняты — вежливо отказать
                if len(used) >= self.expected:
                    try:
                        s.sendall((json.dumps({"error": "room_full"}, ensure_ascii=False) + "\n").encode('utf-8'))
                    except Exception:
                        pass
                    try:
                        s.close()
                    except Exception:
                        pass
                    continue
                # найти свободный id
                for i in range(self.expected):
                    if i not in used:
                        next_id = i
                        break
                rc = RemoteClient(s, a, next_id)
                self.clients[next_id] = rc
            # рукопожатие
            hello = json.dumps({"hello": True, "tank_id": next_id}, ensure_ascii=False) + "\n"
            try:
                s.sendall(hello.encode('utf-8'))
            except Exception:
                pass
            # обновить окно ожидания
            if WAIT_WIN:
                WAIT_WIN.refresh()

    def broadcast(self, msgs_per_id):
        # msgs_per_id: dict{tank_id: json_str}
        with self.lock:
            for i, rc in list(self.clients.items()):
                if not rc.alive:
                    del self.clients[i]
                    if WAIT_WIN:
                        WAIT_WIN.refresh()
                    continue
                msg = msgs_per_id.get(i)
                if not msg:
                    continue
                try:
                    rc.sock.sendall((msg + "\n").encode('utf-8'))
                except Exception:
                    rc.alive = False

    def get_cmd(self, tank_id):
        with self.lock:
            rc = self.clients.get(tank_id)
            if rc and rc.alive:
                return rc.cmd or ""
        return ""

    def connected_count(self):
        with self.lock:
            return len([c for c in self.clients.values() if c.alive])


# ============== ТАНКИ ==============

class Tank:
    def __init__(self, x, y, color_idx, tank_id, ai=True, team=0, remote=False):
        self.x = x
        self.y = y
        self.hp = CONFIG['tank']['max_hp']
        self.angle = 0
        self.last_shot = 0
        self.color_idx = color_idx
        self.tank_id = tank_id
        self.ai = ai
        self.team = team
        self.remote = remote   # управляется удаленным ботом?

        if tank_id not in TANK_STATS:
            TANK_STATS[tank_id] = {'kills': 0, 'deaths': 0}
        if tank_id not in TANK_WINS:
            TANK_WINS[tank_id] = 0

    def get_color(self):
        return CONFIG['colors']['tank_colors'][self.color_idx % len(CONFIG['colors']['tank_colors'])]

    def to_json(self):
        return {
            'tank_id': self.tank_id,
            'x': self.x,
            'y': self.y,
            'hp': self.hp,
            'angle': self.angle,
            'a': self.angle,
            'color_idx': self.color_idx,
            'team': self.team,
        }

    def update_position(self, keys, walls, water, tanks, destructibles):
        if self.remote and NET_SERVER:
            self.remote_think(walls, water, tanks, destructibles)
        elif self.ai:
            self.bot_think(tanks, walls, water, destructibles)
        else:
            self.player_think(keys, walls, water, tanks, destructibles)

    def player_think(self, keys, walls, water, tanks, destructibles):
        if 'a' in keys:
            self.angle -= CONFIG['tank']['rotation_speed']
        if 'd' in keys:
            self.angle += CONFIG['tank']['rotation_speed']
        s = CONFIG['tank']['speed']
        if 'w' in keys:
            self.try_move(s, walls, water, tanks, destructibles)
        if 's' in keys:
            self.try_move(-s, walls, water, tanks, destructibles)
        if 'space' in keys:
            self.try_shoot(self)

    def remote_think(self, walls, water, tanks, destructibles):
        cmd = NET_SERVER.get_cmd(self.tank_id) if NET_SERVER else ""
        if not cmd:
            return
        # команды: l r f b s (комбинируются)
        if 'l' in cmd:
            self.angle -= CONFIG['tank']['rotation_speed']
        if 'r' in cmd:
            self.angle += CONFIG['tank']['rotation_speed']
        s = CONFIG['tank']['speed']
        if 'f' in cmd:
            self.try_move(s, walls, water, tanks, destructibles)
        if 'b' in cmd:
            self.try_move(-s, walls, water, tanks, destructibles)
        if 's' in cmd:
            self.try_shoot(self)

    def bot_think(self, tanks, walls, water, destructibles):
        if len(tanks) < 2:
            return
        enemies = [t for t in tanks if t != self and t.hp > 0]
        if not enemies:
            return
        e = min(enemies, key=lambda t: math.hypot(t.x - self.x, t.y - self.y))
        dx = e.x - self.x
        dy = e.y - self.y
        ta = math.atan2(dy, dx)
        da = (ta - self.angle + math.pi) % (2 * math.pi) - math.pi
        if abs(da) > 0.05:
            self.angle += CONFIG['tank']['rotation_speed'] * (1 if da > 0 else -1) / 2
        else:
            s = CONFIG['tank']['speed'] * 0.75
            self.try_move(s, walls, water, tanks, destructibles)
        if math.hypot(dx, dy) < CONFIG['tank']['fov']:
            self.try_shoot(self)

    def try_move(self, s, walls, water, tanks, destructibles):
        nx = self.x + math.cos(self.angle) * s
        ny = self.y + math.sin(self.angle) * s
        if self.is_valid_position(nx, ny, walls, water, tanks, destructibles):
            self.x, self.y = nx, ny

    def is_valid_position(self, x, y, walls, water, tanks, destructibles):
        sz = CONFIG['tank']['size_w']
        if not (20 < x < CONFIG['window']['width'] - 20 and 20 < y < CONFIG['window']['height'] - 20):
            return False
        if check_collision(x, y, sz, walls) or check_collision(x, y, sz, water):
            return False
        for d_rect, _ in destructibles:
            if d_rect[0] < x < d_rect[2] and d_rect[1] < y < d_rect[3]:
                return False
        for t in tanks:
            if t is not self and abs(x - t.x) < sz and abs(y - t.y) < sz:
                return False
        return True

    def try_shoot(self, owner):
        now = time.time() * 1000
        if now - self.last_shot > CONFIG['tank']['shoot_cooldown']:
            dx = math.cos(self.angle) * CONFIG['bullet']['speed']
            dy = math.sin(self.angle) * CONFIG['bullet']['speed']
            bx = self.x + dx * 2
            by = self.y + dy * 2
            b = game_canvas.create_oval(bx - CONFIG['bullet']['size'], by - CONFIG['bullet']['size'],
                                        bx + CONFIG['bullet']['size'], by + CONFIG['bullet']['size'],
                                        fill=CONFIG['colors']['bullet_fill'],
                                        outline=CONFIG['colors']['bullet_outline'], width=2)
            BULLETS.append([bx, by, dx, dy, b, self])
            self.last_shot = now


# ============== ПРЕПЯТСТВИЯ ==============

def intersects(r1, r2):
    return not (r1[2] <= r2[0] or r1[0] >= r2[2] or r1[3] <= r2[1] or r1[1] >= r2[3])

def create_obstacles():
    global WALLS, WATER, DESTRUCTIBLES
    WALLS.clear(); WATER.clear(); DESTRUCTIBLES.clear()
    areas = []
    mult = CONFIG['obstacles']['obstacle_multiplier']
    wc = max(1, int(CONFIG['obstacles']['wall_count'] * mult))
    ac = max(1, int(CONFIG['obstacles']['water_count'] * mult))
    dc = max(1, int(CONFIG['obstacles']['destructible_count'] * mult))

    for _ in range(wc):
        r = generate_obstacle(areas, WALLS, 'wall_fill', 'wall_outline')
        if r: areas.append(r)
    for _ in range(ac):
        r = generate_obstacle(areas, WATER, 'water_fill', 'water_outline')
        if r: areas.append(r)
    for _ in range(dc):
        sz = random.randint(20, 30)
        x1 = random.randint(100, max(101, CONFIG['window']['width'] - 100 - sz))
        y1 = random.randint(80, max(81, CONFIG['window']['height'] - 80 - sz))
        x2, y2 = x1 + sz, y1 + sz
        r = (x1, y1, x2, y2)
        if any(intersects(r, a) for a in areas):
            continue
        areas.append(r)
        obj = game_canvas.create_rectangle(x1, y1, x2, y2,
                                           fill=CONFIG['colors']['destructible_fill'],
                                           outline=CONFIG['colors']['destructible_outline'], width=2)
        DESTRUCTIBLES.append([r, obj])

def generate_obstacle(areas, lst, fill_key, outline_key):
    x1 = random.randint(100, max(101, CONFIG['window']['width'] - 200))
    y1 = random.randint(80, max(81, CONFIG['window']['height'] - 200))
    w_ = random.randint(CONFIG['obstacles']['min_size'], CONFIG['obstacles']['max_size'])
    h_ = random.randint(CONFIG['obstacles']['min_size'], CONFIG['obstacles']['max_size'])
    x2 = min(x1 + w_, CONFIG['window']['width'] - 50)
    y2 = min(y1 + h_, CONFIG['window']['height'] - 50)
    r = (x1, y1, x2, y2)
    if any(intersects(r, a) for a in areas):
        return None
    game_canvas.create_rectangle(x1, y1, x2, y2,
                                 fill=CONFIG['colors'][fill_key],
                                 outline=CONFIG['colors'][outline_key], width=3)
    lst.append(r); return r


# ============== РИСОВАНИЕ ==============

def draw_tank(t):
    if t.hp <= 0:
        return
    fov = CONFIG['tank']['fov']
    game_canvas.create_oval(t.x - fov, t.y - fov, t.x + fov, t.y + fov,
                            outline=CONFIG['colors']['fov_outline'], width=2, tags="tank")
    draw_tank_body(t); draw_tank_turret(t); draw_tank_barrel(t); draw_tank_hp(t)

def draw_tank_body(t):
    w_, h_ = CONFIG['tank']['size_w'], CONFIG['tank']['size_h']
    pts = []
    for cx, cy in [(-w_/2,-h_/2),(w_/2,-h_/2),(w_/2,h_/2),(-w_/2,h_/2)]:
        rx = t.x + cx*math.cos(t.angle) - cy*math.sin(t.angle)
        ry = t.y + cx*math.sin(t.angle) + cy*math.cos(t.angle)
        pts.extend([rx, ry])
    game_canvas.create_polygon(pts, fill="#2F4F2F", outline="black", width=2, tags="tank")
    w2, h2 = CONFIG['tank']['inner_w'], CONFIG['tank']['inner_h']
    pts = []
    for cx, cy in [(-w2/2,-h2/2),(w2/2,-h2/2),(w2/2,h2/2),(-w2/2,h2/2)]:
        rx = t.x + cx*math.cos(t.angle) - cy*math.sin(t.angle)
        ry = t.y + cx*math.sin(t.angle) + cy*math.cos(t.angle)
        pts.extend([rx, ry])
    game_canvas.create_polygon(pts, fill=t.get_color(), outline="black", width=2, tags="tank")

def draw_tank_turret(t):
    game_canvas.create_oval(t.x-6, t.y-6, t.x+6, t.y+6, fill=t.get_color(), outline="black", width=2, tags="tank")

def draw_tank_barrel(t):
    dx, dy = math.cos(t.angle), math.sin(t.angle)
    game_canvas.create_line(t.x, t.y, t.x + 20*dx, t.y + 20*dy, fill="black", width=4, tags="tank")

def draw_tank_hp(t):
    hp_color = CONFIG['colors']['hp_full'] if t.hp == 3 else CONFIG['colors']['hp_mid'] if t.hp == 2 else CONFIG['colors']['hp_low']
    game_canvas.create_rectangle(t.x-12, t.y-18, t.x+12, t.y-14, fill=CONFIG['colors']['hp_bg'], outline=CONFIG['colors']['hp_outline'], tags="tank")
    bw = int((t.hp / CONFIG['tank']['max_hp']) * 24)
    game_canvas.create_rectangle(t.x-12, t.y-18, t.x-12 + bw, t.y-14, fill=hp_color, tags="tank")
    game_canvas.create_text(t.x, t.y-25, text=f"HP: {t.hp}", font=("Segoe UI", 10, "bold"), fill="white", tags="tank")

def is_visible(x, y, cx, cy, r):
    return (x-cx)*(x-cx) + (y-cy)*(y-cy) <= r*r

def update_display():
    game_canvas.delete("tank")
    fov = CONFIG['tank']['fov']
    vis = set()
    for t in TANKS:
        if t.hp <= 0:
            continue
        for w_ in WALLS:
            if is_visible((w_[0]+w_[2])/2, (w_[1]+w_[3])/2, t.x, t.y, fov):
                vis.add(('wall', w_))
        for w_ in WATER:
            if is_visible((w_[0]+w_[2])/2, (w_[1]+w_[3])/2, t.x, t.y, fov):
                vis.add(('water', w_))
        for d, _obj in DESTRUCTIBLES:
            if is_visible((d[0]+d[2])/2, (d[1]+d[3])/2, t.x, t.y, fov):
                vis.add(('destructible', d))
    for typ, o in vis:
        if typ == 'wall':
            game_canvas.create_rectangle(o[0], o[1], o[2], o[3],
                                         fill=CONFIG['colors']['wall_fill'],
                                         outline=CONFIG['colors']['wall_outline'], width=3, tags="tank")
        elif typ == 'water':
            game_canvas.create_rectangle(o[0], o[1], o[2], o[3],
                                         fill=CONFIG['colors']['water_fill'],
                                         outline=CONFIG['colors']['water_outline'], width=3, tags="tank")
        else:
            game_canvas.create_rectangle(o[0], o[1], o[2], o[3],
                                         fill=CONFIG['colors']['destructible_fill'],
                                         outline=CONFIG['colors']['destructible_outline'], width=2, tags="tank")
    for t in TANKS:
        draw_tank(t)

def draw_stats():
    y = 10
    game_canvas.create_text(10, y, anchor="nw", text="🎮 СТАТИСТИКА 🎮", font=("Segoe UI", 12, "bold"), fill="white")
    y += 25
    for tid in sorted(TANK_STATS.keys()):
        k = TANK_STATS[tid]['kills']; d = TANK_STATS[tid]['deaths']; wns = TANK_WINS.get(tid, 0)
        col = CONFIG['colors']['tank_colors'][tid % len(CONFIG['colors']['tank_colors'])]
        txt = f"🚀 Танк {tid+1}: 💀{d} ⚔️{k} 🏆{wns}"
        game_canvas.create_text(10, y, anchor="nw", text=txt, font=("Segoe UI", 10), fill=col); y += 20
    game_canvas.create_text(10, CONFIG['window']['height']-30, anchor="nw",
                            text=f"🎯 Игра {current_game}/{total_games}", font=("Segoe UI", 11, "bold"), fill="yellow")


# ============== ПУЛИ/КОЛЛИЗИИ ==============

def check_collision(x, y, size, obs):
    for ox1, oy1, ox2, oy2 in obs:
        if x - size/2 < ox2 and x + size/2 > ox1 and y - size/2 < oy2 and y + size/2 > oy1:
            return True
    return False

def update_bullets():
    for b in BULLETS[:]:
        b[0] += b[2]; b[1] += b[3]
        game_canvas.coords(b[4], b[0] - CONFIG['bullet']['size'], b[1] - CONFIG['bullet']['size'],
                                     b[0] + CONFIG['bullet']['size'], b[1] + CONFIG['bullet']['size'])
        out = b[0] < 0 or b[0] > CONFIG['window']['width'] or b[1] < 0 or b[1] > CONFIG['window']['height']
        hit_wall = check_collision(b[0], b[1], 1, WALLS)
        hit_water = check_collision(b[0], b[1], 1, WATER)
        hit_fov = math.hypot(b[0] - b[5].x, b[1] - b[5].y) > CONFIG['bullet']['range']
        hit_dest = False
        for d_rect, d_obj in DESTRUCTIBLES:
            if d_rect[0] < b[0] < d_rect[2] and d_rect[1] < b[1] < d_rect[3]:
                hit_dest = True
                game_canvas.delete(d_obj)
                DESTRUCTIBLES.remove([d_rect, d_obj])
                break
        if out or hit_wall or hit_water or hit_dest or hit_fov:
            game_canvas.delete(b[4]); BULLETS.remove(b); continue
        for t in TANKS:
            if t is not b[5] and t.hp > 0 and abs(b[0]-t.x) < CONFIG['tank']['size_w'] and abs(b[1]-t.y) < CONFIG['tank']['size_h']:
                t.hp = max(t.hp - 1, 0)
                game_canvas.delete(b[4]); BULLETS.remove(b)
                TANK_STATS[b[5].tank_id]['kills'] += 1
                if t.hp <= 0:
                    TANK_STATS[t.tank_id]['deaths'] += 1
                    check_game_over()
                break

def check_game_over():
    global game_over
    alive = [t for t in TANKS if t.hp > 0]
    if len(alive) <= 1:
        game_over = True
        show_game_over(alive[0] if alive else None)


# ============== ИГРОВОЙ ЦИКЛ ==============

def toggle_pause():
    global game_paused, label_pause
    game_paused = not game_paused
    if game_paused:
        label_pause = tk.Label(w, text="⏸️  ПАУЗА  ⏸️", font=("Segoe UI", 36, "bold"), fg="red", bg="#228B22")
        label_pause.place(x=CONFIG['window']['width']//2 - 150, y=CONFIG['window']['height']//2 - 60, width=300, height=120)
        btn_pause.config(text="▶️  Продолжить  ▶️")
    else:
        if label_pause: label_pause.destroy()
        btn_pause.config(text="⏸️  Пауза  ⏸️")

def exit_game():
    global game_over
    game_over = True

def restart_game():
    global TANKS, BULLETS, KEYS, game_over, btn_pause, btn_exit, btn_new_game, label_pause
    global WALLS, WATER, DESTRUCTIBLES, stats_log, game_speed, game_canvas

    TANKS = []; BULLETS = []; KEYS = set(); game_over = False
    WALLS = []; WATER = []; DESTRUCTIBLES = []; stats_log = []; game_speed = 1.0
    if btn_pause: btn_pause.destroy()
    if btn_exit: btn_exit.destroy()
    if btn_new_game: btn_new_game.destroy()
    if label_pause: label_pause.destroy()

    game_canvas.delete("all")

    spawn_tanks_remote_or_ai()
    create_obstacles()
    create_game_buttons()

    # Запуcтить цикл
    game_loop()

def create_game_buttons():
    global btn_pause, btn_exit
    btn_pause = tk.Button(w, text="⏸️  Пауза  ⏸️", font=("Segoe UI", 9, "bold"), command=toggle_pause, bg="#0066CC", fg="white")
    btn_pause.place(x=10, y=CONFIG['window']['height'] - 40, width=150, height=35)
    btn_exit = tk.Button(w, text="🚪  Выход  🚪", font=("Segoe UI", 9, "bold"), command=exit_game, bg="#DD0000", fg="white")
    btn_exit.place(x=170, y=CONFIG['window']['height'] - 40, width=150, height=35)

def spawn_positions(n):
    pos = [
        (100, 100),
        (CONFIG['window']['width'] - 100, CONFIG['window']['height'] - 100),
        (100, CONFIG['window']['height'] - 100),
        (CONFIG['window']['width'] - 100, 100),
        (CONFIG['window']['width']//2, 100),
        (CONFIG['window']['width']//2, CONFIG['window']['height'] - 100),
        (100, CONFIG['window']['height']//2),
        (CONFIG['window']['width'] - 100, CONFIG['window']['height']//2),
    ]
    out = []
    for i in range(n):
        out.append(pos[i % len(pos)])
    return out

def spawn_tanks_remote_or_ai():
    global TANKS
    TANKS = []
    n = CONFIG['game']['tank_count']
    ps = spawn_positions(n)
    for i in range(n):
        x, y = ps[i]
        remote = CONFIG['network']['enabled']
        TANKS.append(Tank(x, y, i, tank_id=i, ai=not remote, team=0, remote=remote))

def show_game_over(winner):
    global btn_pause, btn_exit, btn_new_game, label_pause
    if btn_pause: btn_pause.destroy(); btn_pause = None
    if btn_exit: btn_exit.destroy(); btn_exit = None
    if label_pause: label_pause.destroy(); label_pause = None
    game_canvas.delete("all")
    if winner:
        text = f"🏆 ПОБЕДИТЕЛЬ: Танк {winner.color_idx + 1}! 🏆"
        TANK_WINS[winner.tank_id] += 1
    else:
        text = "⚔️ НИЧЬЯ! ⚔️"
    lbl = tk.Label(w, text=text, font=("Segoe UI", 28, "bold"), fg="#FFD700", bg="#111111", relief="solid", bd=2)
    lbl.place(x=250, y=280, width=780, height=80)
    # Без кнопки "Новая игра" — серия рулится автоматически

def game_loop():
    global game_over, current_game, total_games
    if game_over:
        # перейти к следующей игре серии или назад в меню
        w.after(1200, handle_game_end)
        return
    if not game_paused:
        for t in TANKS:
            if t.hp > 0:
                t.update_position(KEYS, WALLS, WATER, TANKS, DESTRUCTIBLES)
        update_bullets()
        # сетевой тик: рассылка FOV
        if CONFIG['network']['enabled'] and NET_SERVER:
            net_tick()
    update_display()
    draw_stats()
    if not game_over:
        delay = int((1000 / CONFIG['game']['fps']) / game_speed)
        w.after(delay, game_loop)

def handle_game_end():
    global current_game, total_games
    current_game += 1
    if current_game <= total_games:
        restart_game()
    else:
        close_game_window()
        open_settings_gui()


# ============== СЕТЕВЫЕ FOV/ФАЙЛЫ ==============

def build_fov_payload(me):
    # подготовить индивидуальный срез
    pl = [t.to_json() for t in TANKS if t is not me]
    walls = [list(w_) for w_ in WALLS]
    water = [list(w_) for w_ in WATER]
    dest = [list(d) for d, _ in DESTRUCTIBLES]
    bullets = [{'x': b[0], 'y': b[1]} for b in BULLETS]
    bot = {'x': me.x, 'y': me.y, 'a': me.angle, 'hp': me.hp}
    return {'player': None, 'walls': walls, 'water': water, 'dest': dest, 'bullets': bullets, 'bot': bot, 'tanks': pl}

def net_tick():
    # троттлинг рассылки: не чаще, чем update_interval
    global NET_LAST_BROADCAST_TS
    now_ms = time.time() * 1000.0
    if now_ms - NET_LAST_BROADCAST_TS < CONFIG['network']['update_interval']:
        return
    NET_LAST_BROADCAST_TS = now_ms

    # рассылаем FOV всем подключенным, одновременно пишем fovN.json
    msgs = {}
    for t in TANKS:
        if not t.remote:
            continue
        j = build_fov_payload(t)
        s = json.dumps(j, ensure_ascii=False)
        msgs[t.tank_id] = s
        # запишем файл
        try:
            with open(f"fov{t.tank_id+1}.json", "w", encoding="utf-8") as f:
                f.write(s)
        except Exception:
            pass
    if NET_SERVER:
        NET_SERVER.broadcast(msgs)


# ============== ВВОД/ОКНА ==============

def key_press(e):
    k = e.keysym.lower()
    if k == 'escape':
        exit_game()
    if k == 'space':
        KEYS.add('space')
    if k in ('w', 'a', 's', 'd'):
        KEYS.add(k)

def key_release(e):
    k = e.keysym.lower()
    if k == 'space' and 'space' in KEYS:
        KEYS.remove('space')
    if k in ('w', 'a', 's', 'd') and k in KEYS:
        KEYS.remove(k)

def close_game_window():
    global game_canvas, btn_pause, btn_exit, btn_new_game, label_pause
    if btn_pause: btn_pause.destroy(); btn_pause = None
    if btn_exit: btn_exit.destroy(); btn_exit = None
    if btn_new_game: btn_new_game.destroy(); btn_new_game = None
    if label_pause: label_pause.destroy(); label_pause = None
    if game_canvas: game_canvas.destroy(); game_canvas = None
    w.withdraw()

def open_game_window():
    w.state('zoomed')
    w.geometry(f"{CONFIG['window']['width']}x{CONFIG['window']['height']}")
    w.deiconify()
    global game_canvas
    game_canvas = tk.Canvas(w, width=CONFIG['window']['width'], height=CONFIG['window']['height'],
                            bg=CONFIG['window']['bg'], highlightthickness=0)
    game_canvas.pack()
    # старт игры
    restart_game()


# ============== ОКНО ОЖИДАНИЯ БОТОВ ==============

class WaitingWindow:
    def __init__(self, root, server, expected):
        self.root = root
        self.server = server
        self.expected = expected
        self.top = tk.Toplevel(root)
        self.top.title("⏳ Ожидание ботов")
        self.top.geometry("420x360")
        self.top.resizable(False, False)
        self.lbl = tk.Label(self.top, text=f"Слушаем {CONFIG['network']['ip']}:{CONFIG['network']['port']}", font=("Segoe UI", 10))
        self.lbl.pack(pady=10)
        self.lb = tk.Listbox(self.top, height=12, font=("Consolas", 10))
        self.lb.pack(fill="both", expand=True, padx=10, pady=10)
        self.stat = tk.Label(self.top, text="", font=("Segoe UI", 11, "bold"))
        self.stat.pack(pady=5)
        self.btn = tk.Button(self.top, text="▶️ ИГРАТЬ ▶️", font=("Segoe UI", 12, "bold"), command=self.start_game, bg="#00AA00", fg="white")
        self.btn.pack(pady=8)
        self.btn.config(state="disabled")
        self.refresh()
        # периодическое обновление
        self.tick()

    def tick(self):
        self.refresh()
        self.top.after(300, self.tick)

    def refresh(self):
        self.lb.delete(0, tk.END)
        cnt = 0
        with self.server.lock:
            for i, rc in sorted(self.server.clients.items()):
                st = "OK" if rc.alive else "OFF"
                self.lb.insert(tk.END, f"tank {i+1}: {rc.addr[0]}:{rc.addr[1]}  [{st}]")
                if rc.alive: cnt += 1
        self.stat.config(text=f"Подключено: {cnt}/{self.expected}")
        if cnt >= self.expected:
            self.btn.config(state="normal")

    def start_game(self):
        self.top.destroy()
        global WAIT_WIN
        WAIT_WIN = None
        open_game_window()


# ============== МЕНЮ НАСТРОЕК ==============

class SettingsGUI:
    def __init__(self, root):
        self.root = root
        self.window = tk.Toplevel(root)
        self.window.title("⚙️ Танки. Битва ботов")
        self.window.geometry("520x760")
        self.window.resizable(False, False)
        self.window.config(bg="#111111")

        sw = self.window.winfo_screenwidth()
        sh = self.window.winfo_screenheight()
        x = (sw - 520)//2; y = (sh - 760)//2
        self.window.geometry(f"520x760+{x}+{y}")
        self.build_ui()

    def set_spin(self, sb, v): sb.delete(0, tk.END); sb.insert(0, str(v))

    def build_ui(self):
        f = tk.Frame(self.window, bg="#111111"); f.pack(fill="both", expand=True)
        row = 0
        tk.Label(f, text="⚙️ ТАНКИ. БИТВА БОТОВ ⚙️", font=("Segoe UI", 16, "bold"), fg="#FFD700", bg="#111111").grid(row=row, column=0, columnspan=3, pady=16); row += 1

        items = [
            ("🎮 Кол-во танков (2-8):", "tc", 2, 8, CONFIG['game']['tank_count']),
            ("🎯 Кол-во игр в серии:", "gc", 1, 12, CONFIG['game']['total_games']),
            ("📏 Ширина поля:", "wd", 800, 1280, CONFIG['window']['width']),
            ("📏 Высота поля:", "ht", 600, 720, CONFIG['window']['height']),
            ("❤  Здоровье танка:", "hp", 1, 10, CONFIG['tank']['max_hp']),
            ("👁 Поле зрения:", "fv", 100, 500, CONFIG['tank']['fov']),
            ("🎯 Дальность выстрела:", "rg", 50, 500, CONFIG['bullet']['range']),
        ]
        for text, name, a, b, v in items:
            tk.Label(f, text=text, fg="#FFFFFF", bg="#111111", font=("Segoe UI", 11, "bold")).grid(row=row, column=0, sticky="w", padx=18, pady=10)
            sb = tk.Spinbox(f, from_=a, to=b, width=8, bg="#222222", fg="#FFFFFF", font=("Segoe UI", 11, "bold"), bd=1)
            self.set_spin(sb, v); sb.grid(row=row, column=1, padx=6, pady=10, sticky="w")
            setattr(self, name, sb)
            row += 1

        # Препятствия
        tk.Label(f, text="🧱 Препятствия (множитель):", fg="#FFFFFF", bg="#111111", font=("Segoe UI", 11, "bold")).grid(row=row, column=0, sticky="w", padx=18, pady=10)
        self.om = tk.Scale(f, from_=0.5, to=2.0, resolution=0.1, orient="horizontal", bg="#222222", fg="#FFFFFF", troughcolor="#333333", highlightthickness=0)
        self.om.set(CONFIG['obstacles']['obstacle_multiplier']); self.om.grid(row=row, column=1, padx=18, pady=10, sticky="ew"); row += 1

        # Сеть
        self.net_var = tk.IntVar(value=1 if CONFIG['network']['enabled'] else 0)
        cb = tk.Checkbutton(f, text="🌐 Включить сеть (TCP)", variable=self.net_var, bg="#111111", fg="#FFFFFF", selectcolor="#111111", font=("Segoe UI", 11, "bold"))
        cb.grid(row=row, column=0, columnspan=2, sticky="w", padx=18, pady=8); row += 1

        tk.Label(f, text="🌐 IP адрес (bind):", fg="#FFFFFF", bg="#111111", font=("Segoe UI", 11, "bold")).grid(row=row, column=0, sticky="w", padx=18, pady=8)
        self.ip = tk.Entry(f, width=12, bg="#222222", fg="#FFFFFF", font=("Segoe UI", 11, "bold"), bd=1, insertbackground='white'); self.ip.insert(0, CONFIG['network']['ip'])
        self.ip.grid(row=row, column=1, padx=18, pady=8, sticky="w"); row += 1

        tk.Label(f, text="🔌 Порт:", fg="#FFFFFF", bg="#111111", font=("Segoe UI", 11, "bold")).grid(row=row, column=0, sticky="w", padx=18, pady=8)
        self.pt = tk.Entry(f, width=12, bg="#222222", fg="#FFFFFF", font=("Segoe UI", 11, "bold"), bd=1, insertbackground='white'); self.pt.insert(0, str(CONFIG['network']['port']))
        self.pt.grid(row=row, column=1, padx=18, pady=8, sticky="w"); row += 1

        tk.Label(f, text="📡 Интервал сети (мс):", fg="#FFFFFF", bg="#111111", font=("Segoe UI", 11, "bold")).grid(row=row, column=0, sticky="w", padx=18, pady=8)
        self.upd = tk.Entry(f, width=12, bg="#222222", fg="#FFFFFF", font=("Segoe UI", 11, "bold"), bd=1, insertbackground='white'); self.upd.insert(0, str(CONFIG['network']['update_interval']))
        self.upd.grid(row=row, column=1, padx=18, pady=8, sticky="w"); row += 1

        # Кнопка запуска
        btn = tk.Button(f, text="▶️ СТАРТ СЕРИИ ▶️", font=("Segoe UI", 14, "bold"), bg="#00AA00", fg="#FFFFFF", command=self.start_series, relief="flat")
        btn.grid(row=row, column=0, columnspan=2, pady=18, padx=18, sticky="ew"); row += 1

    def start_series(self):
        global CONFIG, current_game, total_games, NET_SERVER, WAIT_WIN
        CONFIG['game']['tank_count'] = int(self.tc.get())
        CONFIG['game']['total_games'] = int(self.gc.get())
        CONFIG['window']['width'] = int(self.wd.get())
        CONFIG['window']['height'] = int(self.ht.get())
        CONFIG['obstacles']['obstacle_multiplier'] = float(self.om.get())
        CONFIG['tank']['fov'] = int(self.fv.get())
        CONFIG['tank']['max_hp'] = int(self.hp.get())
        CONFIG['bullet']['range'] = int(self.rg.get())
        CONFIG['network']['enabled'] = bool(self.net_var.get())
        CONFIG['network']['ip'] = self.ip.get().strip() or '0.0.0.0'
        try:
            CONFIG['network']['port'] = int(self.pt.get())
        except Exception:
            CONFIG['network']['port'] = 5000
        try:
            CONFIG['network']['update_interval'] = max(20, int(self.upd.get()))
        except Exception:
            CONFIG['network']['update_interval'] = 100

        current_game = 1
        total_games = CONFIG['game']['total_games']

        # старт сервера если нужно
        if CONFIG['network']['enabled']:
            if NET_SERVER:
                try: NET_SERVER.stop()
                except Exception: pass
            NET_SERVER = Server(CONFIG['network']['ip'], CONFIG['network']['port'], CONFIG['game']['tank_count'])
            NET_SERVER.start()
            # окно ожидания
            WAIT_WIN = WaitingWindow(self.root, NET_SERVER, CONFIG['game']['tank_count'])
        else:
            open_game_window()

        self.window.destroy()


# ============== ОСНОВА ==============

def open_settings_gui():
    SettingsGUI(w)

def main():
    global w
    w = tk.Tk()
    w.title(CONFIG['window']['title'])
    w.withdraw()
    w.bind("<KeyPress>", key_press)
    w.bind("<KeyRelease>", key_release)
    w.focus_set()
    open_settings_gui()
    w.mainloop()

if __name__ == "__main__":
    main()
