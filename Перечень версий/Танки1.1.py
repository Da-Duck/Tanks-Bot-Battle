import tkinter as tk
import time
import math
import random


w = tk.Tk()
w.title("Танчики")
w.geometry("1280x720")
w.resizable(False, False)

c = tk.Canvas(w, width=1280, height=720, bg="#228B22")
c.pack()

t1_x, t1_y = 100, 100
t1_hp = 3
t1_angle = 0
t1_last_shot = 0

t2_x, t2_y = 1100, 600
t2_hp = 3
t2_angle = 0
t2_last_shot = 0

SHOT_RANGE = 200
WALLS = []
WATER = []
BULLETS = []
KEYS = set()

bot_action = None
bot_action_end = 0

game_over = False

btn = None
label = None


def intersects(r1, r2):
    return not (r1[2] <= r2[0] or r1[0] >= r2[2] or r1[3] <= r2[1] or r1[1] >= r2[3])


def create_obstacles():
    global WALLS, WATER
    WALLS = []
    WATER = []
    areas = []
    for _ in range(15):
        x1 = random.randint(100, 900)
        y1 = random.randint(80, 450)
        width = random.randint(50, 120)
        height = random.randint(50, 120)
        x2 = min(x1 + width, 1150)
        y2 = min(y1 + height, 620)
        rect = (x1, y1, x2, y2)
        if (abs(x1 - t1_x) < 80 and abs(y1 - t1_y) < 80) or (abs(x1 - t2_x) < 80 and abs(y1 - t2_y) < 80):
            continue
        if any(intersects(rect, a) for a in areas):
            continue
        areas.append(rect)
        obstacle = random.choice(["wall", "wall", "water"])
        if obstacle == "wall":
            c.create_rectangle(x1, y1, x2, y2, fill="#8B4513", outline="#654321", width=3)
            WALLS.append(rect)
        else:
            c.create_rectangle(x1, y1, x2, y2, fill="#1E90FF", outline="#0000CD", width=3)
            WATER.append(rect)


def draw_tank(x, y, hp, angle, color):
    if hp <= 0:
        return
    c.create_oval(x - SHOT_RANGE, y - SHOT_RANGE, x + SHOT_RANGE, y + SHOT_RANGE, outline="red", width=2, tags="tank")
    dx = math.cos(angle)
    dy = math.sin(angle)
    w, h = 24, 16
    corners = [(-w/2, -h/2), (w/2, -h/2), (w/2, h/2), (-w/2, h/2)]
    body_points = []
    for cx, cy in corners:
        rx = x + cx * math.cos(angle) - cy * math.sin(angle)
        ry = y + cx * math.sin(angle) + cy * math.cos(angle)
        body_points.extend([rx, ry])
    c.create_polygon(body_points, fill="#2F4F2F", outline="black", width=2, tags="tank")
    w2, h2 = 20, 12
    corners2 = [(-w2/2, -h2/2), (w2/2, -h2/2), (w2/2, h2/2), (-w2/2, h2/2)]
    inner_points = []
    for cx, cy in corners2:
        rx = x + cx * math.cos(angle) - cy * math.sin(angle)
        ry = y + cx * math.sin(angle) + cy * math.cos(angle)
        inner_points.extend([rx, ry])
    c.create_polygon(inner_points, fill=color, outline="black", width=2, tags="tank")
    c.create_oval(x - 6, y - 6, x + 6, y + 6, fill=color, outline="black", width=2, tags="tank")
    c.create_line(x, y, x + 20 * dx, y + 20 * dy, fill="black", width=4, tags="tank")
    hp_color = "green" if hp == 3 else "orange" if hp == 2 else "red"
    c.create_rectangle(x - 12, y - 18, x + 12, y - 14, fill="black", outline="white", tags="tank")
    bar_width = int((hp / 3) * 24)
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


def move_tank(x, y, angle, fwd, back, left, right):
    if left in KEYS:
        angle -= 0.1
    if right in KEYS:
        angle += 0.1
    speed = 4
    if fwd in KEYS:
        nx = x + math.cos(angle) * speed
        ny = y + math.sin(angle) * speed
        if 20 < nx < 1260 and 20 < ny < 700 and not check_collision(nx, ny, 24, WALLS) and not check_collision(nx, ny, 24, WATER):
            x, y = nx, ny
    if back in KEYS:
        nx = x - math.cos(angle) * speed
        ny = y - math.sin(angle) * speed
        if 20 < nx < 1260 and 20 < ny < 700 and not check_collision(nx, ny, 24, WALLS) and not check_collision(nx, ny, 24, WATER):
            x, y = nx, ny
    return x, y, angle


def shoot(x, y, angle, last_shot, owner):
    now = time.time() * 1000
    if now - last_shot > 400:
        dx = math.cos(angle) * 10
        dy = math.sin(angle) * 10
        bx = x + dx * 2
        by = y + dy * 2
        bullet = c.create_oval(bx - 4, by - 4, bx + 4, by + 4, fill="#FFD700", outline="#FF8C00", width=2)
        BULLETS.append([bx, by, dx, dy, bullet, owner])
        last_shot = now
    return last_shot


def update_bullets():
    global t1_hp, t2_hp
    for b in BULLETS[:]:
        b[0] += b[2]
        b[1] += b[3]
        c.coords(b[4], b[0] - 4, b[1] - 4, b[0] + 4, b[1] + 4)
        out_of_bounds = b[0] < 0 or b[0] > 1280 or b[1] < 0 or b[1] > 720
        hit_wall = check_collision(b[0], b[1], 1, WALLS)
        dist_from_owner = math.hypot(b[0] - b[5][0], b[1] - b[5][1])
        too_far = dist_from_owner > SHOT_RANGE
        if out_of_bounds or hit_wall or too_far:
            c.delete(b[4])
            BULLETS.remove(b)
            continue
        if abs(b[0] - t1_x) < 25 and abs(b[1] - t1_y) < 25 and b[5] != (t1_x, t1_y):
            t1_hp = max(t1_hp - 1, 0)
            c.delete(b[4])
            BULLETS.remove(b)
            continue
        if abs(b[0] - t2_x) < 25 and abs(b[1] - t2_y) < 25 and b[5] != (t2_x, t2_y):
            t2_hp = max(t2_hp - 1, 0)
            c.delete(b[4])
            BULLETS.remove(b)


def bot_behaviour():
    global bot_action, bot_action_end, t2_x, t2_y, t2_angle, t2_last_shot
    now = time.time() * 1000
    if bot_action is None or now > bot_action_end:
        bot_action = random.choice(['turn_left', 'turn_right', 'forward', 'back', 'shoot'])
        bot_action_end = now + random.randint(500, 1500)
    if bot_action == 'turn_left':
        t2_angle -= 0.07
    elif bot_action == 'turn_right':
        t2_angle += 0.07
    elif bot_action == 'forward':
        nx = t2_x + math.cos(t2_angle) * 3
        ny = t2_y + math.sin(t2_angle) * 3
        if 20 < nx < 1260 and 20 < ny < 700 and not check_collision(nx, ny, 24, WALLS) and not check_collision(nx, ny, 24, WATER):
            t2_x, t2_y = nx, ny
    elif bot_action == 'back':
        nx = t2_x - math.cos(t2_angle) * 3
        ny = t2_y - math.sin(t2_angle) * 3
        if 20 < nx < 1260 and 20 < ny < 700 and not check_collision(nx, ny, 24, WALLS) and not check_collision(nx, ny, 24, WATER):
            t2_x, t2_y = nx, ny
    elif bot_action == 'shoot':
        t2_last_shot = shoot(t2_x, t2_y, t2_angle, t2_last_shot, (t2_x, t2_y))


def update_display():
    c.delete("tank")
    draw_tank(t1_x, t1_y, t1_hp, t1_angle, "#0066CC")
    draw_tank(t2_x, t2_y, t2_hp, t2_angle, "#CC0000")


def restart():
    global t1_x, t1_y, t1_hp, t1_angle, t1_last_shot
    global t2_x, t2_y, t2_hp, t2_angle, t2_last_shot
    global BULLETS, KEYS, bot_action, bot_action_end, game_over, btn, label

    t1_x, t1_y, t1_hp, t1_angle, t1_last_shot = 100, 100, 3, 0, 0
    t2_x, t2_y, t2_hp, t2_angle, t2_last_shot = 1100, 600, 3, 0, 0
    BULLETS = []
    KEYS = set()
    bot_action = None
    bot_action_end = 0
    game_over = False
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
    # label is a tk.Label widget, create separately
    label = tk.Label(w, text=f"{winner} танк победил!", font=("Arial", 28, "bold"), fg="yellow", bg="#222")
    label.place(x=440, y=320, width=400, height=60)
    global btn
    btn = tk.Button(w, text="Играть снова", font=("Arial", 14), command=restart)
    btn.place(x=570, y=390, width=200, height=40)


def game_loop():
    global t1_x, t1_y, t1_angle, t1_last_shot
    if game_over:
        return

    t1_x, t1_y, t1_angle = move_tank(t1_x, t1_y, t1_angle, 'w', 's', 'a', 'd')
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
