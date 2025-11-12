import tkinter as tk
import time
import random

w = tk.Tk()
w.title("Танчики")
w.geometry("1280x720")
w.resizable(False, False)

c = tk.Canvas(w, width=1280, height=720, bg="#228B22")
c.pack()

t1x, t1y = 100, 100
t1hp = 3
t1color = "#0066CC"
t1dx, t1dy = 0, 0
t1size = 24
t1last_shot = 0

t2x, t2y = 1100, 600
t2hp = 3
t2color = "#CC0000"
t2dx, t2dy = 0, 0
t2size = 24
t2last_shot = 0

walls = []
water = []
bullets = []
keys = set()

def create_obstacles():
    global walls, water
    walls = []
    water = []
    
    for i in range(15):
        x1 = random.randint(100, 900)
        y1 = random.randint(80, 450)
        width = random.randint(50, 120)
        height = random.randint(50, 120)
        x2 = x1 + width
        y2 = y1 + height
        
        if x2 > 1150:
            x2 = 1150
        if y2 > 620:
            y2 = 620
            
        if (abs(x1 - t1x) < 80 and abs(y1 - t1y) < 80) or (abs(x1 - t2x) < 80 and abs(y1 - t2y) < 80):
            continue
            
        obstacle_type = random.choice(["wall", "wall", "water"])
        
        if obstacle_type == "wall":
            c.create_rectangle(x1, y1, x2, y2, fill="#8B4513", outline="#654321", width=3)
            c.create_rectangle(x1+2, y1+2, x2-2, y2-2, fill="#A0522D", outline="#8B4513", width=1)
            
            for j in range(3):
                for k in range(3):
                    brick_x = x1 + j * (width // 3)
                    brick_y = y1 + k * (height // 3)
                    c.create_rectangle(brick_x, brick_y, brick_x + width//3, brick_y + height//3, 
                                     outline="#654321", width=1)
            
            walls.append((x1, y1, x2, y2))
        else:
            c.create_rectangle(x1, y1, x2, y2, fill="#1E90FF", outline="#0000CD", width=3)
            c.create_rectangle(x1+3, y1+3, x2-3, y2-3, fill="#87CEEB", outline="#4682B4", width=1)
            
            for wave in range(5):
                wave_y = y1 + wave * (height // 5) + height // 10
                points = []
                for px in range(x1, x2, 8):
                    wave_height = 3 * (1 + 0.5 * random.random())
                    points.extend([px, wave_y + wave_height])
                if len(points) > 2:
                    c.create_line(points, fill="#0000CD", width=1, smooth=True)
            
            water.append((x1, y1, x2, y2))

def draw_tank(x, y, color, hp, direction):
    if hp <= 0:
        return
        
    body_color = color
    track_color = "#2F4F2F" if color == "#0066CC" else "#800000"
    
    c.create_rectangle(x-14, y-10, x+14, y+10, fill=track_color, outline="black", width=2, tags="tank")
    c.create_rectangle(x-12, y-8, x+12, y+8, fill=body_color, outline="black", width=2, tags="tank")
    
    c.create_rectangle(x-10, y-6, x-6, y+6, fill=track_color, outline="black", width=1, tags="tank")
    c.create_rectangle(x+6, y-6, x+10, y+6, fill=track_color, outline="black", width=1, tags="tank")
    
    for i in range(-8, 9, 4):
        c.create_rectangle(x-10, y+i-1, x-6, y+i+1, fill="black", tags="tank")
        c.create_rectangle(x+6, y+i-1, x+10, y+i+1, fill="black", tags="tank")
    
    turret_color = body_color
    c.create_oval(x-6, y-6, x+6, y+6, fill=turret_color, outline="black", width=2, tags="tank")
    
    if direction[0] > 0:
        c.create_rectangle(x+6, y-2, x+16, y+2, fill="black", outline="gray", width=1, tags="tank")
    elif direction[0] < 0:
        c.create_rectangle(x-16, y-2, x-6, y+2, fill="black", outline="gray", width=1, tags="tank")
    elif direction[1] > 0:
        c.create_rectangle(x-2, y+6, x+2, y+16, fill="black", outline="gray", width=1, tags="tank")
    else:
        c.create_rectangle(x-2, y-16, x+2, y-6, fill="black", outline="gray", width=1, tags="tank")
    
    hp_color = "green" if hp == 3 else "orange" if hp == 2 else "red"
    c.create_rectangle(x-12, y-18, x+12, y-14, fill="black", outline="white", width=1, tags="tank")
    bar_width = int((hp / 3) * 20)
    c.create_rectangle(x-10, y-17, x-10+bar_width, y-15, fill=hp_color, tags="tank")
    
    c.create_text(x, y-25, text=f"HP: {hp}", font=("Arial", 10, "bold"), fill="white", tags="tank")

def key_press(e):
    keys.add(e.keysym.lower())

def key_release(e):
    keys.discard(e.keysym.lower())

def check_wall_collision(x, y, size):
    for wx1, wy1, wx2, wy2 in walls:
        if (x - size//2 < wx2 and x + size//2 > wx1 and 
            y - size//2 < wy2 and y + size//2 > wy1):
            return True
    return False

def check_water_collision(x, y, size):
    for wx1, wy1, wx2, wy2 in water:
        if (x - size//2 < wx2 and x + size//2 > wx1 and 
            y - size//2 < wy2 and y + size//2 > wy1):
            return True
    return False

def check_bullet_wall_collision(x, y):
    for wx1, wy1, wx2, wy2 in walls:
        if wx1 <= x <= wx2 and wy1 <= y <= wy2:
            return True
    return False

def move_tank1(dx, dy):
    global t1x, t1y, t1dx, t1dy
    new_x = t1x + dx
    new_y = t1y + dy
    
    if (new_x - t1size//2 >= 20 and new_x + t1size//2 <= 1260 and
        new_y - t1size//2 >= 20 and new_y + t1size//2 <= 700):
        
        if not check_wall_collision(new_x, new_y, t1size) and not check_water_collision(new_x, new_y, t1size):
            t1x = new_x
            t1y = new_y
            if dx != 0 or dy != 0:
                t1dx, t1dy = dx, dy

def move_tank2(dx, dy):
    global t2x, t2y, t2dx, t2dy
    new_x = t2x + dx
    new_y = t2y + dy
    
    if (new_x - t2size//2 >= 20 and new_x + t2size//2 <= 1260 and
        new_y - t2size//2 >= 20 and new_y + t2size//2 <= 700):
        
        if not check_wall_collision(new_x, new_y, t2size) and not check_water_collision(new_x, new_y, t2size):
            t2x = new_x
            t2y = new_y
            if dx != 0 or dy != 0:
                t2dx, t2dy = dx, dy

def shoot_tank1():
    global t1last_shot
    current_time = time.time() * 1000
    if current_time - t1last_shot > 400 and (t1dx != 0 or t1dy != 0):
        speed = 10
        if abs(t1dx) > abs(t1dy):
            bdx = speed if t1dx > 0 else -speed
            bdy = 0
        else:
            bdx = 0
            bdy = speed if t1dy > 0 else -speed
            
        bullet = c.create_oval(t1x-4, t1y-4, t1x+4, t1y+4, fill="#FFD700", outline="#FF8C00", width=2)
        c.create_oval(t1x-2, t1y-2, t1x+2, t1y+2, fill="#FFFF00")
        bullets.append([t1x, t1y, bdx, bdy, bullet, 1])
        t1last_shot = current_time

def shoot_tank2():
    global t2last_shot
    current_time = time.time() * 1000
    if current_time - t2last_shot > 400 and (t2dx != 0 or t2dy != 0):
        speed = 10
        if abs(t2dx) > abs(t2dy):
            bdx = speed if t2dx > 0 else -speed
            bdy = 0
        else:
            bdx = 0
            bdy = speed if t2dy > 0 else -speed
            
        bullet = c.create_oval(t2x-4, t2y-4, t2x+4, t2y+4, fill="#FFD700", outline="#FF8C00", width=2)
        c.create_oval(t2x-2, t2y-2, t2x+2, t2y+2, fill="#FFFF00")
        bullets.append([t2x, t2y, bdx, bdy, bullet, 2])
        t2last_shot = current_time

def handle_input():
    if 'w' in keys or 'ц' in keys:
        move_tank1(0, -4)
    if 's' in keys or 'ы' in keys:
        move_tank1(0, 4)
    if 'a' in keys or 'ф' in keys:
        move_tank1(-4, 0)
    if 'd' in keys or 'в' in keys:
        move_tank1(4, 0)
    if 'space' in keys:
        shoot_tank1()
        
    if 'up' in keys:
        move_tank2(0, -4)
    if 'down' in keys:
        move_tank2(0, 4)
    if 'left' in keys:
        move_tank2(-4, 0)
    if 'right' in keys:
        move_tank2(4, 0)
    if 'return' in keys:
        shoot_tank2()

def update_bullets():
    global t1hp, t2hp
    for b in bullets[:]:
        b[0] += b[2]
        b[1] += b[3]
        
        c.coords(b[4], b[0]-4, b[1]-4, b[0]+4, b[1]+4)
        
        if (b[0] < 0 or b[0] > 1280 or b[1] < 0 or b[1] > 720 or
            check_bullet_wall_collision(b[0], b[1])):
            c.delete(b[4])
            bullets.remove(b)
            continue
        
        if (abs(b[0] - t1x) < 25 and abs(b[1] - t1y) < 25 and b[5] != 1):
            t1hp -= 1
            if t1hp < 0:
                t1hp = 0
            c.delete(b[4])
            bullets.remove(b)
            continue
            
        if (abs(b[0] - t2x) < 25 and abs(b[1] - t2y) < 25 and b[5] != 2):
            t2hp -= 1
            if t2hp < 0:
                t2hp = 0
            c.delete(b[4])
            bullets.remove(b)

def update_display():
    c.delete("tank")
    
    if t1hp > 0:
        draw_tank(t1x, t1y, t1color, t1hp, (t1dx, t1dy))
    
    if t2hp > 0:
        draw_tank(t2x, t2y, t2color, t2hp, (t2dx, t2dy))

def game_loop():
    handle_input()
    update_bullets()
    update_display()
    
    if t1hp <= 0 or t2hp <= 0:
        winner = "Красный" if t1hp <= 0 else "Синий"
        c.create_rectangle(540, 340, 740, 380, fill="black", outline="white", width=3, tags="winner")
        c.create_text(640, 360, text=f"{winner} танк победил!", 
                     font=("Arial", 20, "bold"), fill="yellow", tags="winner")
        return
    
    w.after(20, game_loop)

create_obstacles()

w.bind("<KeyPress>", key_press)
w.bind("<KeyRelease>", key_release)
w.focus_set()

game_loop()
w.mainloop()