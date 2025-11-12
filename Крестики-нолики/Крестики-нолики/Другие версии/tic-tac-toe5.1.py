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

BG_COLOR = "#ffffff"
FG_COLOR = "#ffffff"
ACCENT_COLOR = "#4a9cff"
BTN_STYLE = {"bg": BG_COLOR, "fg": FG_COLOR, "activebackground": "#3d3d3d", "bd": 0}
ENTRY_STYLE = {"bg": "#404040", "fg": FG_COLOR, "insertbackground": FG_COLOR}
LABEL_STYLE = {"bg": BG_COLOR, "fg": ACCENT_COLOR}
FRAME_STYLE = {"bg": BG_COLOR}

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

    if not all([bpEnt, mdEnt, ngEnt, sizeEnt]):
        messagebox.showerror("Ошибка", "Не все виджеты инициализированы")
        return

    bp = bpEnt.get().split()

    try:
        md = int(mdEnt.get())
        ng = int(ngEnt.get())
        size = int(sizeEnt.get())
    except ValueError:
        messagebox.showerror("Ошибка", "Некорректные числовые значения")
        return

    if len(bp) < 2:
        messagebox.showerror("Ошибка", "Нужно минимум 2 бота")
        return

    if size < 3:
        messagebox.showerror("Ошибка", "Размер поля должен быть не менее 3")
        return

    for path in bp:
        if not (path.endswith(".exe") or path.endswith(".py")):
            messagebox.showerror("Ошибка", f"Бот {path} должен быть .exe или .py файлом")
            return

    for widget in bFrame.winfo_children():
        widget.destroy()

    btns.clear()
    for i in range(size):
        rowBtns = []
        for j in range(size):
            button = tk.Button(bFrame, text="", width=4, height=2, 
                            font=('Segoe UI', 10, 'bold'), **BTN_STYLE)
            button.grid(row=i, column=j, padx=2, pady=2)
            rowBtns.append(button)
        btns.append(rowBtns)
    m.update()

    bNames = [os.path.basename(p) for p in bp]
    bStat = {name: {"wins": 0, "losses": 0, "draws": 0} for name in bNames}

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

            stLbl.config(text=f"Турнир {gmNum+1}/{ng}\n{nameA} (X) vs {nameB} (O)")
            m.update()
            res1 = playGame(botA, botB, md, size)
            updStat(res1, [botA, botB])

            stLbl.config(text=f"Турнир {gmNum+1}/{ng}\n{nameB} (X) vs {nameA} (O)")
            m.update()
            res2 = playGame(botB, botA, md, size)
            updStat(res2, [botB, botA])

            time.sleep(0.3)

def playGame(botX, botO, md, size):
    global is_slow_mode
    board = [0] * (size * size)
    curPlayer = 1
    winner = 0

    updBDis(board, size)
    m.update()
    time.sleep(0.1)

    while True:
        bot = botX if curPlayer == 1 else botO
        try:
            move = getBotM(bot, board, curPlayer, md, size)
            if move is None or board[move] != 0:
                winner = 2 if curPlayer == 1 else 1
                break
        except Exception as e:
            winner = 2 if curPlayer == 1 else 1
            break

        board[move] = curPlayer
        updBDis(board, size)
        m.update()
        time.sleep(0.1)
        save_game_state(board)

        if is_slow_mode:
            time.sleep(delay_duration / 1000)

        winner = chkWinner(board, size)
        if winner != 0:
            break

        if 0 not in board:
            winner = -1
            break

        curPlayer = 2 if curPlayer == 1 else 1

    updBDis(board, size)
    m.update()
    time.sleep(0.1)
    save_game_state(board)
    m.update()
    return winner

def save_game_state(board):
    with open("game.txt", "w") as f:
        f.write("".join(map(str, board)))

def getBotM(botPath, board, player, timeout, size):
    if botPath == "random_bot":
        empty_cells = [i for i, val in enumerate(board) if val == 0]
        return random.choice(empty_cells) if empty_cells else None

    command = [botPath]
    if botPath.endswith(".py"):
        command = [sys.executable, botPath]

    try:
        result = subprocess.run(
            command,
            input=str(player) + "\n" + str(size) + "\n" + "".join(map(str, board)),
            capture_output=True,
            timeout=timeout / 1000,
            check=False,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        moveStr = result.stdout.strip()
        if moveStr.isdigit():
            move = int(moveStr)
            if 0 <= move < len(board) and board[move] == 0:
                return move
        return None
    except subprocess.TimeoutExpired:
        return None
    except Exception as e:
        return None

def chkWinner(board, size):
    n = size
    for i in range(n):
        if all(board[i*n + j] == 1 for j in range(n)):
            return 1
        if all(board[i*n + j] == 2 for j in range(n)):
            return 2
    
    for j in range(n):
        if all(board[i*n + j] == 1 for i in range(n)):
            return 1
        if all(board[i*n + j] == 2 for i in range(n)):
            return 2
    
    if all(board[i*n + i] == 1 for i in range(n)):
        return 1
    if all(board[i*n + i] == 2 for i in range(n)):
        return 2
    
    if all(board[i*n + (n-1-i)] == 1 for i in range(n)):
        return 1
    if all(board[i*n + (n-1-i)] == 2 for i in range(n)):
        return 2
    
    return -1 if 0 not in board else 0

def updBDis(board, size):
    for i in range(size):
        for j in range(size):
            index = i * size + j
            text = ""
            color = FG_COLOR
            if board[index] == 1:
                text = "✕"
                color = "#ff5555"
            elif board[index] == 2:
                text = "◯"
                color = "#55aaff"
            btns[i][j].config(text=text, fg=color, font=('Arial', 14, 'bold'))

def updStat(result, bots):
    names = [os.path.basename(b) for b in bots]
    b1Name = names[0]
    b2Name = names[1]

    if result == 1:
        bStat[b1Name]["wins"] += 1
        bStat[b2Name]["losses"] += 1
    elif result == 2:
        bStat[b2Name]["wins"] += 1
        bStat[b1Name]["losses"] += 1
    else:
        bStat[b1Name]["draws"] += 1
        bStat[b2Name]["draws"] += 1
    updSaDis()

def updSaDis():
    saText = ""
    for name, data in bStat.items():
        saText += (
            f"• {name}: "
            f"🏆Побед: {data['wins']}  💀Поражений: {data['losses']}  🤝Ничей: {data['draws']}\n"
        )
    saLbl.config(text=saText)

def toggle_slow_mode():
    global is_slow_mode
    is_slow_mode = not is_slow_mode
    slow_button.config(text="⏩ Быстрая" if is_slow_mode else "⏸ Медленная")

m = tk.Tk()
m.title("Крестики нолики. Битва ботов")
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
sizeEnt.insert(0, "3")
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

#by DaDuckTG