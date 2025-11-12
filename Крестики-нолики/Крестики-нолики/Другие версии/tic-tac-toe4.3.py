
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
bFrame = None
btns = []
stLbl = None
saLbl = None
bStat = {}
bNames = []
is_slow_mode = False
delay_duration = 1000  # 1 секунда в миллисекундах


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
    global bStat, bNames, bpEnt, mdEnt, ngEnt  # Declare as global to avoid errors

    if bpEnt is None or mdEnt is None or ngEnt is None:
        messagebox.showerror("Ошибка", "Не все виджеты инициализированы")
        return

    bp = bpEnt.get().split()

    # Валидация вывода
    try:
        md = int(mdEnt.get())
        ng = int(ngEnt.get())
    except ValueError:
        messagebox.showerror("Ошибка", "Некорректные числовые значения")
        return

    if len(bp) < 2:
        messagebox.showerror("Ошибка", "Нужно минимум 2 бота")
        return

    for path in bp:
        if not path.endswith(".exe") and not path.endswith(".py"):
            messagebox.showerror("Ошибка", f"Бот {path} должен быть .exe или .py файлом")
            return

    # Инициализация статистики
    bNames = [os.path.basename(p) for p in bp]
    bStat = {name: {"wins": 0, "losses": 0, "draws": 0} for name in bNames}

    # Запускаем турнир в отдельном потоке
    threading.Thread(target=runMT, args=(bp, md, ng), daemon=True).start()


def runMT(bp, md, ng):
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

            res = playGame(botX, botO, md)
            updStat(res, [botX, botO])

            botX = bp[b]
            botO = bp[a]
            b1 = os.path.basename(botX)
            b2 = os.path.basename(botO)
            statT = f"Турнир {gmNum + 1}/{ng}\nПара: {b1} (X) vs {b2} (O)"
            stLbl.config(text=statT)
            m.update()

            res = playGame(botX, botO, md)
            updStat(res, [botX, botO])


def playGame(botX, botO, md):
    global is_slow_mode
    board = [0] * 9
    curPlayer = 1
    winner = 0

    updBDis(board)
    m.update()

    for moveNum in range(9):
        bot = botX if curPlayer == 1 else botO
        try:
            move = getBotM(bot, board, curPlayer, md)
            if move is None or board[move] != 0:
                winner = 2 if curPlayer == 1 else 1
                break
        except Exception as e:
            continue

        if move is None:
            winner = 2 if curPlayer == 1 else 1
            break

        board[move] = curPlayer
        updBDis(board)
        save_game_state(board)
        m.update()

        if is_slow_mode:
            time.sleep(delay_duration / 1000)

        winner = chkWinner(board)
        if winner != 0:
            break

        curPlayer = 2 if curPlayer == 1 else 1

    updBDis(board)
    save_game_state(board)
    m.update()
    return winner

def save_game_state(board):
    with open("game.txt", "w") as f:
        f.write("".join(map(str, board)))


def getBotM(botPath, board, player, timeout):
    command = [botPath]  # Default command for .exe
    if botPath.endswith(".py"):
        command = [sys.executable, botPath]  # Use python interpreter for .py

    try:
        result = subprocess.run(
            command,
            input=str(player) + "\n" + "".join(map(str, board)),
            capture_output=True,
            timeout=timeout / 1000,
            check=False,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        moveStr = result.stdout.strip()
        if moveStr.isdigit():
            move = int(moveStr)
            if 0 <= move <= 8 and board[move] == 0:
                return move
            else:
                print(f"Бот вернул некорректный ход (вне диапазона или занято): {move}")
                return None
        elif moveStr == '' or moveStr == ' ':
            print(f"Бот вернул пустую строку / не успел сходить: {move}")
            return None
        else:
            print(f"Бот вернул некорректный ход (не число): {moveStr}")
            return None
    except subprocess.TimeoutExpired:
        print("Время вышло")
        return None
    except Exception as e:
        return None


def chkWinner(board):
    wins = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],
        [0, 3, 6], [1, 4, 7], [2, 5, 8],
        [0, 4, 8], [2, 4, 6]
    ]
    for combo in wins:
        a, b, c = combo
        if board[a] == board[b] == board[c] and board[a] != 0:
            return board[a]
    return 0 if 0 in board else -1

def updBDis(board):
    for i in range(9):
        row = i // 3
        col = i % 3
        text = ""
        color = "black"
        if board[i] == 1:
            text = "X"
            color = "red"
        elif board[i] == 2:
            text = "O"
            color = "blue"
        btns[row][col].config(text=text, fg=color)
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
        slow_button.config(text="Нормальная скорость")
    else:
        slow_button.config(text="Медленная скорость")


# --- Пользовательское окно ---
m = tk.Tk()
m.title("Крестики-Нолики: Битва Ботов")

bpLbl = ttk.Label(m, text="Пути к ботам (через пробел):")
bpLbl.grid(row=0, column=0, padx=5, pady=5, sticky="w")

bpEnt = ttk.Entry(m, width=50)
bpEnt.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

ngLbl = ttk.Label(m, text="Количество турниров:")
ngLbl.grid(row=1, column=0, padx=5, pady=5, sticky="w")

ngEnt = ttk.Entry(m, width=10)
ngEnt.insert(0, "1")
ngEnt.grid(row=1, column=1, padx=5, pady=5, sticky="w")

mdLbl = ttk.Label(m, text="Время на ход в милисекундах:")
mdLbl.grid(row=2, column=0, padx=5, pady=5, sticky="w")

mdEnt = ttk.Entry(m, width=10)
mdEnt.insert(0, "1000")
mdEnt.grid(row=2, column=1, padx=5, pady=5, sticky="w")

slow_button = ttk.Button(m, text="Медленная скорость", command=toggle_slow_mode)
slow_button.grid(row=3, column=0, columnspan=2, padx=5, pady=5)

playBtn = ttk.Button(m, text="Играть", command=startT)
playBtn.grid(row=4, column=0, columnspan=2, padx=5, pady=10)

bFrame = ttk.Frame(m)
bFrame.grid(row=5, column=0, columnspan=2, padx=5, pady=5)

btns = []
for i in range(3):
    rowBtns = []
    for j in range(3):
        button = tk.Button(bFrame, text="", width=5, height=2, command=lambda row=i, col=j: cellClk(row, col))
        button.grid(row=i, column=j, padx=2, pady=2)
        rowBtns.append(button)
    btns.append(rowBtns)

stLbl = ttk.Label(m, text="Ожидание начала турнира...")
stLbl.grid(row=6, column=0, columnspan=2, padx=5, pady=5)

saLbl = ttk.Label(m, text="Статистика:\n")
saLbl.grid(row=7, column=0, columnspan=2, padx=5, pady=5, sticky="w")

m.grid_columnconfigure(1, weight=1)

m.mainloop()
