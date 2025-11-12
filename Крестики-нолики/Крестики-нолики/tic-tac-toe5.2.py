import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os
import time
from itertools import combinations
import threading
import sys
import random

root = None
botPathEnt = None
timeoutEnt = None
numGamesEnt = None
boardSizeEnt = None
boardFrame = None
buttons = []
statusLbl = None
statsLbl = None
botStats = {}
botNames = []
slowMode = False
paused = False
gameRunning = False
delay = 1000
board = None
curPlayer = 0
boardSize = 0
botX = None
botO = None
maxDepth = 0
BASE_FONT_SIZE = 14
BASE_BUTTON_WIDTH = 4
BASE_BUTTON_HEIGHT = 2

BG_COLOR = "#ffffff"
FG_COLOR = "#ffffff"
ACCENT_COLOR = "#4a9cff"
BTN_STYLE = {"bg": BG_COLOR, "fg": FG_COLOR, "activebackground": "#3d3d3d", "bd": 0}
ENTRY_STYLE = {"bg": "#404040", "fg": FG_COLOR, "insertbackground": FG_COLOR}
LABEL_STYLE = {"bg": BG_COLOR, "fg": ACCENT_COLOR}

def disableButtons():
    for row in buttons:
        for btn in row:
            btn['state'] = tk.DISABLED

def enableButtons():
    for row in buttons:
        for btn in row:
            btn['state'] = tk.NORMAL

def cellClick(row, col):
    messagebox.showinfo("Информация", "Игра ведется ботами, взаимодействие с доской недоступно.")

def startTournament():
    global botStats, botNames, botPathEnt, timeoutEnt, numGamesEnt, boardSizeEnt, buttons, gameRunning

    if not all([botPathEnt, timeoutEnt, numGamesEnt, boardSizeEnt]):
        messagebox.showerror("Ошибка", "Не все виджеты инициализированы")
        return

    botPaths = botPathEnt.get().split()

    try:
        maxDepth = int(timeoutEnt.get())
        numGames = int(numGamesEnt.get())
        boardSize = int(boardSizeEnt.get())
    except ValueError:
        messagebox.showerror("Ошибка", "Некорректные числовые значения")
        return

    if len(botPaths) < 2:
        messagebox.showerror("Ошибка", "Нужно минимум 2 бота")
        return

    for path in botPaths:
        if not (path.endswith(".exe") or path.endswith(".py")):
            messagebox.showerror("Ошибка", f"Бот {path} должен быть .exe или .py файлом")
            return

    for widget in boardFrame.winfo_children():
        widget.destroy()

    buttons.clear()
    for i in range(boardSize):
        rowBtns = []
        for j in range(boardSize):
            if boardSize in (4, 5):
                fontSize = BASE_FONT_SIZE
                buttonWidth = BASE_BUTTON_WIDTH
                buttonHeight = BASE_BUTTON_HEIGHT
            else:
                fontSize = max(8, int(BASE_FONT_SIZE * (3 / boardSize)))
                buttonWidth = max(2, int(BASE_BUTTON_WIDTH * (3 / boardSize)))
                buttonHeight = max(1, int(BASE_BUTTON_HEIGHT * (3 / boardSize)))

            btn = tk.Button(boardFrame, text="", width=buttonWidth, height=buttonHeight, 
                            font=('Segoe UI', fontSize, 'bold'), **BTN_STYLE)
            btn.grid(row=i, column=j, padx=2, pady=2)
            rowBtns.append(btn)
        buttons.append(rowBtns)
    root.update()

    botNames = [os.path.basename(p) for p in botPaths]
    botStats = {name: {"wins": 0, "losses": 0, "draws": 0} for name in botNames}

    gameRunning = True
    threading.Thread(target=runTournament, args=(botPaths, maxDepth, numGames, boardSize), daemon=True).start()

def runTournament(botPaths, maxDepth, numGames, boardSize):
    global statusLbl, gameRunning
    pairs = list(combinations(range(len(botPaths)), 2))

    for gameNum in range(numGames):
        if not gameRunning:
            break
        statusLbl.config(text=f"Турнир {gameNum + 1}/{numGames}")
        root.update()

        for a, b in pairs:
            if not gameRunning:
                break

            botA = botPaths[a]
            botB = botPaths[b]
            nameA = os.path.basename(botA)
            nameB = os.path.basename(botB)

            statusLbl.config(text=f"Турнир {gameNum+1}/{numGames}\n{nameA} (X) vs {nameB} (O)")
            root.update()
            res1 = playGame(botA, botB, maxDepth, boardSize)
            updateStats(res1, [botA, botB])

            statusLbl.config(text=f"Турнир {gameNum+1}/{numGames}\n{nameB} (X) vs {nameA} (O)")
            root.update()
            res2 = playGame(botB, botA, maxDepth, boardSize)
            updateStats(res2, [botB, botA])

            time.sleep(0.3)
    statusLbl.config(text="Турнир завершен.")
    root.update()

def playGame(botX_path, botO_path, gameDepth, gameSize):
    global slowMode, paused, board, curPlayer, boardSize, botX, botO, maxDepth

    board = [0] * (gameSize * gameSize)
    curPlayer = 1
    winner = 0
    boardSize = gameSize
    botX = botX_path
    botO = botO_path
    maxDepth = gameDepth

    updateBoardDisplay(board, boardSize)
    root.update()
    time.sleep(0.1)

    while True:
        if not gameRunning:
            return 0
        while paused:
            time.sleep(0.1)
        if not gameRunning:
            return 0

        bot = botX if curPlayer == 1 else botO
        try:
            move = getBotMove(bot, board, curPlayer, maxDepth, boardSize)
            if move is None or board[move] != 0:
                winner = 2 if curPlayer == 1 else 1
                break
        except Exception as e:
            winner = 2 if curPlayer == 1 else 1
            break

        board[move] = curPlayer
        updateBoardDisplay(board, boardSize)
        root.update()
        time.sleep(0.1)
        saveGameState(board)

        if slowMode:
            time.sleep(delay / 1000)

        winner = checkWinner(board, boardSize)
        if winner != 0:
            break

        if 0 not in board:
            winner = -1
            break

        curPlayer = 2 if curPlayer == 1 else 1

    updateBoardDisplay(board, boardSize)
    root.update()
    time.sleep(0.1)
    saveGameState(board)
    root.update()
    return winner

def nextMove():
    global slowMode, paused, board, curPlayer, boardSize, botX, botO, maxDepth

    if curPlayer == 0:
        return

    bot = botX if curPlayer == 1 else botO
    try:
        move = getBotMove(bot, board, curPlayer, maxDepth, boardSize)
        if move is None or board[move] != 0:
            winner = 2 if curPlayer == 1 else 1
            endGame(winner)
            return
    except Exception as e:
        winner = 2 if curPlayer == 1 else 1
        endGame(winner)
        return

    board[move] = curPlayer
    updateBoardDisplay(board, boardSize)
    root.update()
    time.sleep(0.1)
    saveGameState(board)

    if slowMode:
        time.sleep(delay / 1000)

    winner = checkWinner(board, boardSize)
    if winner != 0:
        endGame(winner)
        return

    if 0 not in board:
        endGame(-1)
        return

    curPlayer = 2 if curPlayer == 1 else 1

def endGame(winner):
    global curPlayer
    updateBoardDisplay(board, boardSize)
    root.update()
    time.sleep(0.1)
    saveGameState(board)
    root.update()
    curPlayer = 0

def saveGameState(board):
    with open("game.txt", "w") as f:
        f.write("".join(map(str, board)))

def getBotMove(botPath, board, player, timeout, size):
    if botPath == "random_bot.exe":
        empty = [i for i, val in enumerate(board) if val == 0]
        return random.choice(empty) if empty else None

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

def checkWinner(board, size):
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

def updateBoardDisplay(board, size):
    for i in range(size):
        for j in range(size):
            index = i * size + j
            text = ""
            color = FG_COLOR

            if size == 1:
                if board[index] == 1 or board[index] == 2:
                    text = "🦆"
                    color = "#e6af2e"
            else:
                if board[index] == 1:
                    text = "✕"
                    color = "#ff5555"
                elif board[index] == 2:
                    text = "◯"
                    color = "#55aaff"

            if size in (4,5):
                buttons[i][j].config(text=text, fg=color, font=('Arial', BASE_FONT_SIZE, 'bold'))
                buttons[i][j].config(width = BASE_BUTTON_WIDTH, height = BASE_BUTTON_HEIGHT)
            else:
                fontSize = max(8, int(BASE_FONT_SIZE * (3 / boardSize)))
                buttons[i][j].config(text=text, fg=color, font=('Arial', fontSize, 'bold'))
                buttonWidth = max(2, int(BASE_BUTTON_WIDTH * (3 / boardSize)))
                buttonHeight = max(1, int(BASE_BUTTON_HEIGHT * (3 / boardSize)))
                buttons[i][j].config(width = buttonWidth, height = buttonHeight)

def updateStats(result, bots):
    names = [os.path.basename(b) for b in bots]
    b1Name = names[0]
    b2Name = names[1]

    if result == 1:
        botStats[b1Name]["wins"] += 1
        botStats[b2Name]["losses"] += 1
    elif result == 2:
        botStats[b2Name]["wins"] += 1
        botStats[b1Name]["losses"] += 1
    else:
        botStats[b1Name]["draws"] += 1
        botStats[b2Name]["draws"] += 1
    displayStats()

def displayStats():
    text = ""
    for name, data in botStats.items():
        text += (
            f"• {name}: "
            f"🏆Побед: {data['wins']}  💀Поражений: {data['losses']}  🤝Ничьих: {data['draws']}\n"
        )
    statsLbl.config(text=text)

def toggleSlowMode():
    global slowMode
    slowMode = not slowMode
    slowButton.config(text="⏭ Быстрее" if slowMode else "⏮ Медленнее")

def togglePause():
    global paused
    paused = not paused
    pauseButton.config(text="▶ Продолжить" if paused else "⏸ Пауза")

def endTournament():
    global gameRunning, curPlayer
    gameRunning = False
    curPlayer = 0
    statusLbl.config(text="Турнир остановлен пользователем.")
    root.update()


root = tk.Tk()
root.title("Крестики нолики. Битва ботов")
root.configure(bg=BG_COLOR)
root.minsize(500, 600)

style = ttk.Style()
style.theme_use('clam')
style.configure('TLabel', **LABEL_STYLE)
style.configure('TButton', background=ACCENT_COLOR, foreground=FG_COLOR, font=('Segoe UI', 10))
style.configure('TEntry', **ENTRY_STYLE)
style.map('TButton', background=[('active', '#3a7cc4')])

mainFrame = ttk.Frame(root, padding=20)
mainFrame.grid(row=0, column=0, sticky="nsew")

ttk.Label(mainFrame, text="Пути к ботам:", font=('Segoe UI', 11, 'bold')).grid(row=0, column=0, sticky="w", pady=3)
botPathEnt = ttk.Entry(mainFrame, width=50, font=('Segoe UI', 10))
botPathEnt.grid(row=1, column=0, columnspan=1, pady=5, sticky="ew")

paramsFrame = ttk.Frame(mainFrame)
paramsFrame.grid(row=2, column=0, pady=10, sticky="w")

ttk.Label(paramsFrame, text="Размер поля:").grid(row=0, column=0, padx=5)
boardSizeEnt = ttk.Entry(paramsFrame, width=7)
boardSizeEnt.insert(0, "3")
boardSizeEnt.grid(row=0, column=1, padx=5)

ttk.Label(paramsFrame, text="Турниров:").grid(row=0, column=2, padx=5)
numGamesEnt = ttk.Entry(paramsFrame, width=7)
numGamesEnt.insert(0, "1")
numGamesEnt.grid(row=0, column=3, padx=5)

ttk.Label(paramsFrame, text="Таймаут (мс):").grid(row=0, column=4, padx=5)
timeoutEnt = ttk.Entry(paramsFrame, width=7)
timeoutEnt.insert(0, "1000")
timeoutEnt.grid(row=0, column=5, padx=5)


buttonFrame = ttk.Frame(mainFrame)
buttonFrame.grid(row=3, column=0, pady=10, sticky="ew")

pauseButton = ttk.Button(buttonFrame, text="⏸ Пауза", command=togglePause)
pauseButton.grid(row=0, column=0, padx=5, pady=5)

nextMoveButton = ttk.Button(buttonFrame, text="➡ След. ход", command=nextMove)
nextMoveButton.grid(row=0, column=1, padx=5, pady=5)

slowButton = ttk.Button(buttonFrame, text="⏮ Медленнее", command=toggleSlowMode)
slowButton.grid(row=0, column=2, padx=5, pady=5)

endButton = ttk.Button(buttonFrame, text="❎ Завершить", command=endTournament)
endButton.grid(row=0, column=3, padx=5, pady=5)


for i in range(4):
    buttonFrame.columnconfigure(i, weight=1)

playBtn = ttk.Button(mainFrame, text="🚀 Запустить турнир", command=startTournament)
playBtn.grid(row=4, column=0, pady=15, sticky="ew")

boardFrame = ttk.Frame(mainFrame, relief='flat')
boardFrame.grid(row=5, column=0, pady=10)

statusLbl = ttk.Label(mainFrame, text="Ожидание старта...", font=('Segoe UI', 10, 'italic'))
statusLbl.grid(row=6, column=0, pady=10)

statsLbl = ttk.Label(mainFrame, text="", font=('Consolas', 9), wraplength=550)
statsLbl.grid(row=7, column=0, sticky="w")

root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)
mainFrame.columnconfigure(0, weight=1)

root.mainloop()


#by DaDuckTG