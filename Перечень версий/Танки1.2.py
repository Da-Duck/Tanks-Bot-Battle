import tkinter as tk
import time
import math
import random

CONFIG = {
    'window': {
        'width': 1280,
        'height': 720,
        'title': "Танчики",
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
        'fov_t1': 260,
        'fov_t2': 260,
    },
    'bullet': {
        'speed': 10,
        'size': 4,
    },
    'obstacles': {
        'wall_count': 15,
        'water_count': 5,
        'destructible_count': 10,
        'min_size': 50,
        'max_size': 120
    },
    'colors': {
        'wall_fill': "#8B4513",
        'wall_outline': "#654321",
        'water_fill': "#1E90FF",
        'water_outline': "#0000CD",
        'destructible_fill': "#DC143C",
        'destructible_outline': "#8B0000",
        'tank1': "#0066CC",
        'tank2': "#CC0000",
        'bullet_fill': "#FFD700",
        'bullet_outline': "#FF8C00",
        'fov_outline': "#FF4444",
        'hp_bg': "black",
        'hp_outline': "white",
        'hp_full': "green",
        'hp_mid': "orange",
        'hp_low': "red",
    }
}

w = tk.Tk()
w.title(CONFIG['window']['title'])
w.geometry(f"{CONFIG['window']['width']}x{CONFIG['window']['height']}")
w.resizable(False, False)

c = tk.Canvas(w, width=CONFIG['window']['width'], height=CONFIG['window']['height'], bg=CONFIG['window']['bg'])
c.pack()

t1_x, t1_y = 100, 100
t1_hp = CONFIG['tank']['max_hp']
t1_angle = 0
t1_last_shot = 0

t2_x, t2_y = 1100, 600
t2_hp = CONFIG['tank']['max_hp']
t2_angle = 0
t2_last_shot = 0

WALLS = []
WATER = []
DESTRUCTIBLES = []
BULLETS = []
KEYS = set()

game_over = False
btn = None
label = None

def intersects(r1, r2):
    return not (r1[2] <= r2[0] or r1[0] >= r2[2] or r1[3] <= r2[1] or r1[1] >= r2[3])

def create_obstacles():
    global WALLS, WATER, DESTRUCTIBLES
    WALLS.clear()
    WATER.clear()
    DESTRUCTIBLES.clear()
    areas = []
    for _ in range(CONFIG['obstacles']['wall_count']):
        x1 = random.randint(100, 900)
        y1 = random.randint(80, 450)
        w = random.randint(CONFIG['obstacles']['min_size'], CONFIG['obstacles']['max_size'])
        h = random.randint(CONFIG['obstacles']['min_size'], CONFIG['obstacles']['max_size'])
        x2 = min(x1 + w, 1150)
        y2 = min(y1 + h, 620)
        rect = (x1, y1, x2, y2)
        if (abs(x1 - t1_x) < 80 and abs(y1 - t1_y) < 80) or (abs(x1 - t2_x) < 80 and abs(y1 - t2_y) < 80):
            continue
        if any(intersects(rect, a) for a in areas):
            continue
        areas.append(rect)
        c.create_rectangle(x1, y1, x2, y2, fill=CONFIG['colors']['wall_fill'], outline=CONFIG['colors']['wall_outline'], width=3)
        WALLS.append(rect)
    for _ in range(CONFIG['obstacles']['water_count']):
        x1 = random.randint(100, 900)
        y1 = random.randint(80, 450)
        w = random.randint(CONFIG['obstacles']['min_size'], CONFIG['obstacles']['max_size'])
        h = random.randint(CONFIG['obstacles']['min_size'], CONFIG['obstacles']['max_size'])
        x2 = min(x1 + w, 1150)
        y2 = min(y1 + h, 620)
        rect = (x1, y1, x2, y2)
        if any(intersects(rect, a) for a in areas):
            continue
        areas.append(rect)
        c.create_rectangle(x1, y1, x2, y2, fill=CONFIG['colors']['water_fill'], outline=CONFIG['colors']['water_outline'], width=3)
        WATER.append(rect)
    for _ in range(CONFIG['obstacles']['destructible_count']):
        sz = random.randint(20, 30)
        x1 = random.randint(100, 1100 - sz)
        y1 = random.randint(80, 600 - sz)
        x2 = x1 + sz
        y2 = y1 + sz
        rect = (x1, y1, x2, y2)
        if any(intersects(rect, a) for a in areas):
            continue
        areas.append(rect)
        obj = c.create_rectangle(x1, y1, x2, y2, fill=CONFIG['colors']['destructible_fill'], outline=CONFIG['colors']['destructible_outline'], width=2)
        DESTRUCTIBLES.append([rect, obj])

def draw_tank(x, y, hp, angle, color, fov):
    if hp <= 0:
        return
    c.create_oval(x - fov, y - fov, x + fov, y + fov, outline=CONFIG['colors']['fov_outline'], width=2, tags="tank")
    dx = math.cos(angle)
    dy = math.sin(angle)
    w, h = CONFIG['tank']['size_w'], CONFIG['tank']['size_h']
    corners = [(-w/2, -h/2), (w/2, -h/2), (w/2, h/2), (-w/2, h/2)]
    body_points = []
    for cx, cy in corners:
        rx = x + cx * math.cos(angle) - cy * math.sin(angle)
        ry = y + cx * math.sin(angle) + cy * math.cos(angle)
        body_points.extend([rx, ry])
    c.create_polygon(body_points, fill="#2F4F2F", outline="black", width=2, tags="tank")
    w2, h2 = CONFIG['tank']['inner_w'], CONFIG['tank']['inner_h']
    corners2 = [(-w2/2, -h2/2), (w2/2, -h2/2), (w2/2, h2/2), (-w2/2, h2/2)]
    inner_points = []
    for cx, cy in corners2:
        rx = x + cx * math.cos(angle) - cy * math.sin(angle)
        ry = y + cx * math.sin(angle) + cy * math.cos(angle)
        inner_points.extend([rx, ry])
    c.create_polygon(inner_points, fill=color, outline="black", width=2, tags="tank")
    c.create_oval(x - 6, y - 6, x + 6, y + 6, fill=color, outline="black", width=2, tags="tank")
    c.create_line(x, y, x + 20 * dx, y + 20 * dy, fill="black", width=4, tags="tank")
    hp_color = CONFIG['colors']['hp_full'] if hp == 3 else CONFIG['colors']['hp_mid'] if hp == 2 else CONFIG['colors']['hp_low']
    c.create_rectangle(x - 12, y - 18, x + 12, y - 14, fill=CONFIG['colors']['hp_bg'], outline=CONFIG['colors']['hp_outline'], tags="tank")
    bar_width = int((hp / CONFIG['tank']['max_hp']) * 24)
    c.create_rectangle(x - 12, y - 18, x - 12 + bar_width, y - 14, fill=hp_color, tags="tank")
    c.create_text(x, y - 25, text=f"HP: {hp}", font=("Arial", 10, "bold"), fill="white", tags="tank")

def key_press(event):
    KEYS.add(event.keysym.lower())

def key_release(event):
    KEYS.discard(event.keysym.lower())

def check_collision(x, y, size, obstacles):
    for ox1, oy1, ox2, oy2 in obstacles:
        if x - size / 2 < ox2 and x + size / 2 > ox1 and y - size / 2 < oy2 and y + size / 2 > oy1:
            return True
    return False

def move_tank(x, y, angle, fwd, back, left, right, keys, walls, water, tanks, self_tank):
    if left in keys:
        angle -= CONFIG['tank']['rotation_speed']
    if right in keys:
        angle += CONFIG['tank']['rotation_speed']
    speed = CONFIG['tank']['speed']
    if fwd in keys:
        nx = x + math.cos(angle) * speed
        ny = y + math.sin(angle) * speed
        if 20 < nx < 1260 and 20 < ny < 700 and not check_collision(nx, ny, CONFIG['tank']['size_w'], walls) and not check_collision(nx, ny, CONFIG['tank']['size_w'], water):
            if all(not intersects((nx - CONFIG['tank']['size_w']//2, ny - CONFIG['tank']['size_h']//2, nx + CONFIG['tank']['size_w']//2, ny + CONFIG['tank']['size_h']//2), t) for t in tanks if t != self_tank):
                x, y = nx, ny
    if back in keys:
        nx = x - math.cos(angle) * speed
        ny = y - math.sin(angle) * speed
        if 20 < nx < 1260 and 20 < ny < 700 and not check_collision(nx, ny, CONFIG['tank']['size_w'], walls) and not check_collision(nx, ny, CONFIG['tank']['size_w'], water):
            if all(not intersects((nx - CONFIG['tank']['size_w']//2, ny - CONFIG['tank']['size_h']//2, nx + CONFIG['tank']['size_w']//2, ny + CONFIG['tank']['size_h']//2), t) for t in tanks if t != self_tank):
                x, y = nx, ny
    return x, y, angle

def shoot(x, y, angle, last_shot, owner):
    now = time.time() * 1000
    if now - last_shot > CONFIG['tank']['shoot_cooldown']:
        dx = math.cos(angle) * CONFIG['bullet']['speed']
        dy = math.sin(angle) * CONFIG['bullet']['speed']
        bx = x + dx * 2
        by = y + dy * 2
        bullet = c.create_oval(bx - CONFIG['bullet']['size'], by - CONFIG['bullet']['size'], bx + CONFIG['bullet']['size'], by + CONFIG['bullet']['size'], fill=CONFIG['colors']['bullet_fill'], outline=CONFIG['colors']['bullet_outline'], width=2)
        BULLETS.append([bx, by, dx, dy, bullet, owner])
        return now
    return last_shot

def update_bullets():
    global t1_hp, t2_hp
    for b in BULLETS[:]:
        b[0] += b[2]
        b[1] += b[3]
        c.coords(b[4], b[0] - CONFIG['bullet']['size'], b[1] - CONFIG['bullet']['size'], b[0] + CONFIG['bullet']['size'], b[1] + CONFIG['bullet']['size'])
        out_of_bounds = b[0] < 0 or b[0] > CONFIG['window']['width'] or b[1] < 0 or b[1] > CONFIG['window']['height']
        hit_wall = check_collision(b[0], b[1], 1, WALLS)
        hit_dest = False
        for d_rect, d_obj in DESTRUCTIBLES:
            if d_rect[0] < b[0] < d_rect[2] and d_rect[1] < b[1] < d_rect[3]:
                hit_dest = True
                c.delete(d_obj)
                DESTRUCTIBLES.remove([d_rect, d_obj])
                break
        dist_from_owner = math.hypot(b[0] - b[5][0], b[1] - b[5][1])
        too_far = dist_from_owner > CONFIG['tank']['fov_t1'] if b[5] == (t1_x, t1_y) else dist_from_owner > CONFIG['tank']['fov_t2']
        if out_of_bounds or hit_wall or hit_dest or too_far:
            c.delete(b[4])
            BULLETS.remove(b)
            continue
        if abs(b[0] - t1_x) < CONFIG['tank']['size_w'] and abs(b[1] - t1_y) < CONFIG['tank']['size_h'] and b[5] != (t1_x, t1_y):
            t1_hp = max(t1_hp - 1, 0)
            c.delete(b[4])
            BULLETS.remove(b)
            continue
        if abs(b[0] - t2_x) < CONFIG['tank']['size_w'] and abs(b[1] - t2_y) < CONFIG['tank']['size_h'] and b[5] != (t2_x, t2_y):
            t2_hp = max(t2_hp - 1, 0)
            c.delete(b[4])
            BULLETS.remove(b)

def bot_behaviour():
    global t2_x, t2_y, t2_angle, t2_last_shot
    dx = t1_x - t2_x
    dy = t1_y - t2_y
    target_angle = math.atan2(dy, dx)
    angle_diff = (target_angle - t2_angle + math.pi) % (2 * math.pi) - math.pi
    if angle_diff > 0.05:
        t2_angle += CONFIG['tank']['rotation_speed'] / 2
    elif angle_diff < -0.05:
        t2_angle -= CONFIG['tank']['rotation_speed'] / 2
    else:
        speed = CONFIG['tank']['speed'] * 0.75
        nx = t2_x + math.cos(t2_angle) * speed
        ny = t2_y + math.sin(t2_angle) * speed
        if 20 < nx < 1260 and 20 < ny < 700 and not check_collision(nx, ny, CONFIG['tank']['size_w'], WALLS) and not check_collision(nx, ny, CONFIG['tank']['size_w'], WATER):
            if not (abs(nx - t1_x) < CONFIG['tank']['size_w'] and abs(ny - t1_y) < CONFIG['tank']['size_h']):
                t2_x, t2_y = nx, ny
    dist = math.hypot(dx, dy)
    if dist < CONFIG['tank']['fov_t2']:
        t2_last_shot = shoot(t2_x, t2_y, t2_angle, t2_last_shot, (t2_x, t2_y))

def update_display():
    c.delete("tank")
    # Ограничение видимости для каждого танка: рисуем всё, что внутри fov
    def is_visible(x, y, cx, cy, r):
        return (x - cx)**2 + (y - cy)**2 <= r**2
    # Рисуем только объекты, видимые для t1
    visible_walls1 = [w for w in WALLS if is_visible((w[0]+w[2])/2, (w[1]+w[3])/2, t1_x, t1_y, CONFIG['tank']['fov_t1'])]
    visible_water1 = [w for w in WATER if is_visible((w[0]+w[2])/2, (w[1]+w[3])/2, t1_x, t1_y, CONFIG['tank']['fov_t1'])]
    visible_dest1 = [d for d, o in DESTRUCTIBLES if is_visible((d[0]+d[2])/2, (d[1]+d[3])/2, t1_x, t1_y, CONFIG['tank']['fov_t1'])]
    # Рисуем только объекты, видимые для t2
    visible_walls2 = [w for w in WALLS if is_visible((w[0]+w[2])/2, (w[1]+w[3])/2, t2_x, t2_y, CONFIG['tank']['fov_t2'])]
    visible_water2 = [w for w in WATER if is_visible((w[0]+w[2])/2, (w[1]+w[3])/2, t2_x, t2_y, CONFIG['tank']['fov_t2'])]
    visible_dest2 = [d for d, o in DESTRUCTIBLES if is_visible((d[0]+d[2])/2, (d[1]+d[3])/2, t2_x, t2_y, CONFIG['tank']['fov_t2'])]

    # Рисуем стены (объединяем видимые объекты)
    all_walls = list({w for w in visible_walls1+visible_walls2})
    for w in all_walls:
        c.create_rectangle(w[0], w[1], w[2], w[3], fill=CONFIG['colors']['wall_fill'], outline=CONFIG['colors']['wall_outline'], width=3, tags="tank")
    # Вода
    all_water = list({w for w in visible_water1+visible_water2})
    for w in all_water:
        c.create_rectangle(w[0], w[1], w[2], w[3], fill=CONFIG['colors']['water_fill'], outline=CONFIG['colors']['water_outline'], width=3, tags="tank")
    # Разрушаемые
    all_dest = list({d for d in visible_dest1+visible_dest2})
    for d in all_dest:
        c.create_rectangle(d[0], d[1], d[2], d[3], fill=CONFIG['colors']['destructible_fill'], outline=CONFIG['colors']['destructible_outline'], width=2, tags="tank")

    draw_tank(t1_x, t1_y, t1_hp, t1_angle, CONFIG['colors']['tank1'], CONFIG['tank']['fov_t1'])
    draw_tank(t2_x, t2_y, t2_hp, t2_angle, CONFIG['colors']['tank2'], CONFIG['tank']['fov_t2'])

def restart():
    global t1_x, t1_y, t1_hp, t1_angle, t1_last_shot
    global t2_x, t2_y, t2_hp, t2_angle, t2_last_shot
    global BULLETS, KEYS, game_over, btn, label, WALLS, WATER, DESTRUCTIBLES

    t1_x, t1_y, t1_hp, t1_angle, t1_last_shot = 100, 100, CONFIG['tank']['max_hp'], 0, 0
    t2_x, t2_y, t2_hp, t2_angle, t2_last_shot = 1100, 600, CONFIG['tank']['max_hp'], 0, 0
    BULLETS = []
    KEYS = set()
    game_over = False
    WALLS = []
    WATER = []
    DESTRUCTIBLES = []
    c.delete("all")
    create_obstacles()
    if btn:
        btn.destroy()
        btn = None
    if label:
        label.destroy()
        label = None
    game_loop()

def show_game_over(winner):
    global game_over, btn, label
    game_over = True
    c.delete("all")
    c.create_rectangle(440, 310, 840, 410, fill="#222", outline="white", width=3)
    label = tk.Label(w, text=f"{winner} танк победил!", font=("Arial", 28, "bold"), fg="yellow", bg="#222")
    label.place(x=440, y=320, width=400, height=60)
    global btn
    btn = tk.Button(w, text="Играть снова", font=("Arial", 14), command=restart)
    btn.place(x=570, y=390, width=200, height=40)

def game_loop():
    global t1_x, t1_y, t1_angle, t1_last_shot
    global t2_x, t2_y, t2_angle, t2_last_shot
    if game_over:
        return

    t1_x, t1_y, t1_angle = move_tank(t1_x, t1_y, t1_angle, 'w', 's', 'a', 'd', KEYS, WALLS, WATER, [(t1_x, t1_y, t1_angle, CONFIG['tank']['size_w'], CONFIG['tank']['size_h']),(t2_x, t2_y, t2_angle, CONFIG['tank']['size_w'], CONFIG['tank']['size_h'])], (t1_x, t1_y))
    if 'space' in KEYS:
        t1_last_shot = shoot(t1_x, t1_y, t1_angle, t1_last_shot, (t1_x, t1_y))

    bot_behaviour()

    update_bullets()
    update_display()
    if t1_hp <= 0 or t2_hp <= 0:
        winner = "Красный" if t1_hp <= 0 else "Синий"
        show_game_over(winner)
        return
    w.after(20, game_loop)

create_obstacles()
w.bind("<KeyPress>", key_press)
w.bind("<KeyRelease>", key_release)
w.focus_set()
game_loop()
w.mainloop()
