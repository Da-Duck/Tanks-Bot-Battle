import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os
import time
from itertools import combinations
import threading
import sys
import random

m = None
bpEnt = None
mdEnt = None
ngEnt = None
sizeEnt = None
bFrame = None
btns = []
stLbl = None
saLbl = None
bStat = {}
bNames = []
is_slow_mode = False
delay_duration = 1000
SHIP_SIZES = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]

BG_COLOR = "#ffffff"
FG_COLOR = "#000000"
ACCENT_COLOR = "#4a9cff"
BTN_STYLE = {"bg": BG_COLOR, "fg": FG_COLOR, "activebackground": "#3d3d3d", "bd": 0}
ENTRY_STYLE = {"bg": "#404040", "fg": FG_COLOR, "insertbackground": FG_COLOR}
LABEL_STYLE = {"bg": BG_COLOR, "fg": ACCENT_COLOR}

class Board:
    def __init__(self, size):
        self.size = size
        self.grid = [[0]*size for _ in range(size)]  # 0 - empty, 1 - ship, 2 - hit, 3 - miss
        self.ships = []
        
    def place_ships_random(self):
        for size in SHIP_SIZES:
            placed = False
            while not placed:
                x = random.randint(0, self.size-1)
                y = random.randint(0, self.size-1)
                vertical = random.choice([True, False])
                if self.can_place_ship(x, y, size, vertical):
                    self.place_ship(x, y, size, vertical)
                    placed = True

    def can_place_ship(self, x, y, size, vertical):
        if vertical:
            if y + size > self.size:
                return False
            for i in range(max(0, x-1), min(self.size, x+2)):
                for j in range(max(0, y-1), min(self.size, y+size+1)):
                    if self.grid[i][j] != 0:
                        return False
        else:
            if x + size > self.size:
                return False
            for i in range(max(0, x-1), min(self.size, x+size+1)):
                for j in range(max(0, y-1), min(self.size, y+2)):
                    if self.grid[i][j] != 0:
                        return False
        return True

    def place_ship(self, x, y, size, vertical):
        coords = []
        if vertical:
            for j in range(y, y+size):
                self.grid[x][j] = 1
                coords.append((x, j))
        else:
            for i in range(x, x+size):
                self.grid[i][y] = 1
                coords.append((i, y))
        self.ships.append({"coords": coords, "hits": set()})

    def all_ships_sunk(self):
        for ship in self.ships:
            if len(ship["hits"]) != len(ship["coords"]):
                return False
        return True

def disB():
    for row in btns:
        for button in row:
            button['state'] = tk.DISABLED

def enB():
    for row in btns:
        for button in row:
            button['state'] = tk.NORMAL

def cellClk(row, col):
    messagebox.showinfo("Информация", "Игра ведется ботами, взаимодействие с доской недоступно.")

def startT():
    global bStat, bNames, bpEnt, mdEnt, ngEnt, sizeEnt, btns

    try:
        md = int(mdEnt.get())
        ng = int(ngEnt.get())
        size = int(sizeEnt.get())
    except ValueError:
        messagebox.showerror("Ошибка", "Некорректные числовые значения")
        return

    bp = bpEnt.get().split()
    if len(bp) < 2:
        messagebox.showerror("Ошибка", "Нужно минимум 2 бота")
        return

    for widget in bFrame.winfo_children():
        widget.destroy()

    btns.clear()
    for i in range(size):
        rowBtns = []
        for j in range(size):
            button = tk.Button(bFrame, text="", width=2, height=1, 
                            font=('Arial', 8), **BTN_STYLE)
            button.grid(row=i, column=j, padx=1, pady=1)
            rowBtns.append(button)
        btns.append(rowBtns)
    m.update()

    bNames = [os.path.basename(p) for p in bp]
    bStat = {name: {"wins": 0, "losses": 0} for name in bNames}

    threading.Thread(target=runMT, args=(bp, md, ng, size), daemon=True).start()

def runMT(bp, md, ng, size):
    global stLbl
    pairs = list(combinations(range(len(bp)), 2))

    for gmNum in range(ng):
        stLbl.config(text=f"Турнир {gmNum + 1}/{ng}")
        m.update()

        for a, b in pairs:
            botA = bp[a]
            botB = bp[b]
            nameA = os.path.basename(botA)
            nameB = os.path.basename(botB)

            stLbl.config(text=f"Турнир {gmNum+1}/{ng}\n{nameA} vs {nameB}")
            m.update()
            res = playGame(botA, botB, md, size)
            updStat(res, [botA, botB])
            time.sleep(0.3)

def playGame(bot1, bot2, md, size):
    board1 = Board(size)
    board2 = Board(size)
    board1.place_ships_random()
    board2.place_ships_random()
    
    current_bot, opponent_bot = bot1, bot2
    current_board = board2
    winner = 0

    while True:
        try:
            x, y = getBotM(current_bot, current_board.grid, md, size)
            if current_board.grid[x][y] in [2, 3]:
                winner = 2 if current_bot == bot1 else 1
                break
                
            if current_board.grid[x][y] == 1:
                current_board.grid[x][y] = 2
                for ship in current_board.ships:
                    if (x, y) in ship["coords"]:
                        ship["hits"].add((x, y))
            else:
                current_board.grid[x][y] = 3
            
            updBDis(current_board.grid)
            m.update()
            time.sleep(0.1)
            
            if current_board.all_ships_sunk():
                winner = 1 if current_bot == bot1 else 2
                break

            current_bot, opponent_bot = opponent_bot, current_bot
            current_board = board1 if current_board == board2 else board2
            
            if is_slow_mode:
                time.sleep(delay_duration / 1000)

        except Exception as e:
            winner = 2 if current_bot == bot1 else 1
            break

    return winner

def getBotM(botPath, grid, timeout, size):
    if botPath == "random_bot":
        while True:
            x = random.randint(0, size-1)
            y = random.randint(0, size-1)
            if grid[x][y] in [0, 1]:
                return x, y

    command = [botPath]
    if botPath.endswith(".py"):
        command = [sys.executable, botPath]

    try:
        flat_grid = "".join(str(cell) for row in grid for cell in row)
        result = subprocess.run(
            command,
            input=f"{size}\n{flat_grid}",
            capture_output=True,
            timeout=timeout / 1000,
            check=False,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        coords = result.stdout.strip().split()
        if len(coords) == 2:
            x = int(coords[0])
            y = int(coords[1])
            if 0 <= x < size and 0 <= y < size:
                return x, y
        return random.randint(0, size-1), random.randint(0, size-1)
    except:
        return random.randint(0, size-1), random.randint(0, size-1)

def updBDis(grid):
    for i in range(len(grid)):
        for j in range(len(grid[0])):
            color = "#ffffff"
            text = ""
            if grid[i][j] == 1:
                color = "#cccccc"
            elif grid[i][j] == 2:  # Hit
                color = "#ff5555"
                text = "✖"
            elif grid[i][j] == 3:  # Miss
                color = "#5555ff"
                text = "•"
            btns[i][j].config(bg=color, text=text)

def updStat(result, bots):
    names = [os.path.basename(b) for b in bots]
    if result == 1:
        bStat[names[0]]["wins"] += 1
        bStat[names[1]]["losses"] += 1
    else:
        bStat[names[1]]["wins"] += 1
        bStat[names[0]]["losses"] += 1
    updSaDis()

def updSaDis():
    saText = ""
    for name, data in bStat.items():
        saText += f"• {name}: 🏆{data['wins']} 💀{data['losses']}\n"
    saLbl.config(text=saText)

def toggle_slow_mode():
    global is_slow_mode
    is_slow_mode = not is_slow_mode
    slow_button.config(text="⏩ Быстрая" if is_slow_mode else "⏸ Медленная")

m = tk.Tk()
m.title("Морской бой. Битва ботов")
m.configure(bg=BG_COLOR)
m.minsize(500, 600)

style = ttk.Style()
style.theme_use('clam')
style.configure('TLabel', **LABEL_STYLE)
style.configure('TButton', background=ACCENT_COLOR, foreground=FG_COLOR, font=('Segoe UI', 10))
style.configure('TEntry', **ENTRY_STYLE)
style.map('TButton', background=[('active', '#3a7cc4')])

main_frame = ttk.Frame(m, padding=20)
main_frame.grid(row=0, column=0, sticky="nsew")

ttk.Label(main_frame, text="Пути к ботам:", font=('Segoe UI', 11, 'bold')).grid(row=0, column=0, sticky="w", pady=3)
bpEnt = ttk.Entry(main_frame, width=50, font=('Segoe UI', 10))
bpEnt.grid(row=1, column=0, columnspan=2, pady=5, sticky="ew")

params_frame = ttk.Frame(main_frame)
params_frame.grid(row=2, column=0, pady=10, sticky="w")

ttk.Label(params_frame, text="Размер поля:").grid(row=0, column=0, padx=5)
sizeEnt = ttk.Entry(params_frame, width=7)
sizeEnt.insert(0, "10")
sizeEnt.grid(row=0, column=1, padx=5)

ttk.Label(params_frame, text="Турниров:").grid(row=0, column=2, padx=5)
ngEnt = ttk.Entry(params_frame, width=7)
ngEnt.insert(0, "1")
ngEnt.grid(row=0, column=3, padx=5)

ttk.Label(params_frame, text="Таймаут (мс):").grid(row=0, column=4, padx=5)
mdEnt = ttk.Entry(params_frame, width=7)
mdEnt.insert(0, "1000")
mdEnt.grid(row=0, column=5, padx=5)

slow_button = ttk.Button(main_frame, text="⏸ Медленная", command=toggle_slow_mode)
slow_button.grid(row=3, column=0, pady=10, sticky="w")

playBtn = ttk.Button(main_frame, text="🚀 Запустить турнир", command=startT)
playBtn.grid(row=4, column=0, pady=15, sticky="ew")

bFrame = ttk.Frame(main_frame, relief='flat')
bFrame.grid(row=5, column=0, pady=10)

stLbl = ttk.Label(main_frame, text="Ожидание старта...", font=('Segoe UI', 10, 'italic'))
stLbl.grid(row=6, column=0, pady=10)

saLbl = ttk.Label(main_frame, text="", font=('Consolas', 9), wraplength=550)
saLbl.grid(row=7, column=0, sticky="w")

m.columnconfigure(0, weight=1)
m.rowconfigure(0, weight=1)
main_frame.columnconfigure(0, weight=1)

m.mainloop()

# Пример бота (random_bot.py):
'''
import sys
import random

size = int(sys.stdin.readline())
grid = sys.stdin.readline().strip()

empty = [(i//size, i%size) for i, c in enumerate(grid) if c in ['0', '1']]
if empty:
    x, y = random.choice(empty)
    print(x, y)
else:
    print(0, 0)
'''