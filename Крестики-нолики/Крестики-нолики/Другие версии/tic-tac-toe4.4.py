
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os
import time
from itertools import combinations
import threading
import sys

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

    if bpEnt is None or mdEnt is None or ngEnt is None or sizeEnt is None:
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

    if size < 2:
        messagebox.showerror("Ошибка", "Размер поля должен быть не менее 2")
        return

    for path in bp:
        if not path.endswith(".exe") and not path.endswith(".py"):
            messagebox.showerror("Ошибка", f"Бот {path} должен быть .exe или .py файлом")
            return

    for widget in bFrame.winfo_children():
        widget.destroy()

    btns.clear()
    for i in range(size):
        rowBtns = []
        for j in range(size):
            button = tk.Button(bFrame, text="", width=5, height=2, command=lambda row=i, col=j: cellClk(row, col))
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
            botX = bp[a]
            botO = bp[b]
            b1 = os.path.basename(botX)
            b2 = os.path.basename(botO)
            statT = f"Турнир {gmNum + 1}/{ng}\nПара: {b1} (X) vs {b2} (O)"
            stLbl.config(text=statT)
            m.update()

            res = playGame(botX, botO, md, size)
            updStat(res, [botX, botO])


def playGame(botX, botO, md, size):
    global is_slow_mode
    board = [0] * (size * size)
    curPlayer = 1
    winner = 0

    updBDis(board, size)
    m.update()
    time.sleep(0.01)

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

        if move is None:
            winner = 2 if curPlayer == 1 else 1
            break

        board[move] = curPlayer
        updBDis(board, size)
        m.update()
        time.sleep(0.01)
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
    time.sleep(0.01)
    save_game_state(board)
    m.update()
    return winner

def save_game_state(board):
    with open("game.txt", "w") as f:
        f.write("".join(map(str, board)))


def getBotM(botPath, board, player, timeout, size):
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
            else:
                return None
        elif moveStr == '' or moveStr == ' ':
            return None
        else:
            return None
    except subprocess.TimeoutExpired:
        return None
    except Exception as e:
        return None


def chkWinner(board, size):
    n = size
    for i in range(n):
        row = board[i*n : (i+1)*n]
        if all(cell == row[0] and cell != 0 for cell in row):
            return row[0]
    for j in range(n):
        column = [board[i*n + j] for i in range(n)]
        if all(cell == column[0] and cell != 0 for cell in column):
            return column[0]
    diag1 = [board[i*n + i] for i in range(n)]
    if all(cell == diag1[0] and cell != 0 for cell in diag1):
        return diag1[0]
    diag2 = [board[i*n + (n-1 - i)] for i in range(n)]
    if all(cell == diag2[0] and cell != 0 for cell in diag2):
        return diag2[0]
    return -1 if 0 not in board else 0

def updBDis(board, size):
    for i in range(size):
        for j in range(size):
            index = i * size + j
            text = ""
            color = "black"
            if board[index] == 1:
                text = "X"
                color = "red"
            elif board[index] == 2:
                text = "O"
                color = "blue"
            else:
                text = ""
            btns[i][j].config(text=text, fg=color)
    m.update()


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
    saText = "Статистика:\n"
    for name, data in bStat.items():
        saText += f"{name}: Победы: {data['wins']}, Поражения: {data['losses']}, Ничьи: {data['draws']}\n"
    saLbl.config(text=saText)

def toggle_slow_mode():
    global is_slow_mode
    is_slow_mode = not is_slow_mode
    if is_slow_mode:
        slow_button.config(text="Быстрая скорость")
    else:
        slow_button.config(text="Медленная скорость")


m = tk.Tk()
m.title("Крестики-Нолики: Битва Ботов")

bpLbl = ttk.Label(m, text="Пути к ботам (через пробел):")
bpLbl.grid(row=0, column=0, padx=5, pady=5, sticky="w")

bpEnt = ttk.Entry(m, width=50)
bpEnt.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

sizeLbl = ttk.Label(m, text="Размер поля (N x N):")
sizeLbl.grid(row=1, column=0, padx=5, pady=5, sticky="w")

sizeEnt = ttk.Entry(m, width=10)
sizeEnt.insert(0, "3")
sizeEnt.grid(row=1, column=1, padx=5, pady=5, sticky="w")

ngLbl = ttk.Label(m, text="Количество турниров:")
ngLbl.grid(row=2, column=0, padx=5, pady=5, sticky="w")

ngEnt = ttk.Entry(m, width=10)
ngEnt.insert(0, "1")
ngEnt.grid(row=2, column=1, padx=5, pady=5, sticky="w")

mdLbl = ttk.Label(m, text="Время на ход в милисекундах:")
mdLbl.grid(row=3, column=0, padx=5, pady=5, sticky="w")

mdEnt = ttk.Entry(m, width=10)
mdEnt.insert(0, "1000")
mdEnt.grid(row=3, column=1, padx=5, pady=5, sticky="w")

slow_button = ttk.Button(m, text="Медленная скорость", command=toggle_slow_mode)
slow_button.grid(row=4, column=0, columnspan=2, padx=5, pady=5)

playBtn = ttk.Button(m, text="Начать игру", command=startT)
playBtn.grid(row=5, column=0, columnspan=2, padx=5, pady=10)

bFrame = ttk.Frame(m)
bFrame.grid(row=6, column=0, columnspan=2, padx=5, pady=5)

btns = []
for i in range(3):
    rowBtns = []
    for j in range(3):
        button = tk.Button(bFrame, text="", width=5, height=2, command=lambda row=i, col=j: cellClk(row, col))
        button.grid(row=i, column=j, padx=2, pady=2)
        rowBtns.append(button)
    btns.append(rowBtns)

stLbl = ttk.Label(m, text="Ожидание начала турнира...")
stLbl.grid(row=7, column=0, columnspan=2, padx=5, pady=5)

saLbl = ttk.Label(m, text="Статистика:\n")
saLbl.grid(row=8, column=0, columnspan=2, padx=5, pady=5, sticky="w")

m.grid_columnconfigure(1, weight=1)

m.mainloop()