
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import subprocess
import os
import random
import time
from itertools import combinations

# Global Variables (Avoid excessive use of globals in a larger project)
master = None
bot_paths_entry = None
move_duration_entry = None
num_games_entry = None
board_frame = None
buttons = []
status_label = None
stats_label = None
bot_stats = {}
bot_names = []


def disable_board():
    """Disable all buttons on the board."""
    global buttons
    for row in buttons:
        for button in row:
            button['state'] = tk.DISABLED


def enable_board():
    """Enable all buttons on the board."""
    global buttons
    for row in buttons:
        for button in row:
            button['state'] = tk.NORMAL


def cell_clicked(row, col):
    """This is a placeholder.  The UI is for visualization, not direct player interaction."""
    messagebox.showinfo("Информация", "Игра ведется ботами, взаимодействие с доской недоступно.")


def start_tournament():
    global bot_paths_entry, move_duration_entry, num_games_entry, bot_names, bot_stats

    bot_paths = bot_paths_entry.get().split()
    try:
        move_duration = int(move_duration_entry.get())
    except ValueError:
        messagebox.showerror("Ошибка", "Некорректная длительность хода. Введите целое число.")
        return

    try:
        num_games = int(num_games_entry.get())
    except ValueError:
        messagebox.showerror("Ошибка", "Некорректное количество турниров. Введите целое число.")
        return

    if len(bot_paths) < 2:
        messagebox.showerror("Ошибка", "Необходимо указать как минимум два пути к ботам.")
        return

    # Basic path validation - check if files exist
    for path in bot_paths:
        if not os.path.exists(path):
            messagebox.showerror("Ошибка", f"Файл не найден: {path}")
            return

    # Basic path validation - check if files are executables
    for path in bot_paths:
        if not path.lower().endswith(".exe"):
            messagebox.showerror("Ошибка", f"Укажите исполняемый файл (.exe): {path}")
            return

    bot_names = [os.path.basename(path) for path in bot_paths]
    bot_stats = {name: {"wins": 0, "losses": 0, "draws": 0} for name in bot_names}

    run_multiple_tournaments(bot_paths, move_duration, num_games)


def run_multiple_tournaments(bot_paths, move_duration, num_games):
    """Runs multiple tournaments, alternating starting player and bot pairings."""
    global status_label, master, bot_stats, bot_names
    num_bots = len(bot_paths)
    bot_combinations = list(combinations(range(num_bots), 2))  # All possible unique pairings

    for game_num in range(num_games):
        status_label.config(text=f"Турнир {game_num + 1}/{num_games}: Начало...")
        master.update()
        print(f"Starting Tournament: {game_num + 1}")

        # Shuffle the bot combinations for variety in each tournament
        random.shuffle(bot_combinations)

        for i, (bot1_index, bot2_index) in enumerate(bot_combinations):
            bot1_path = bot_paths[bot1_index]
            bot2_path = bot_paths[bot2_index]

            # Alternate who starts as X and O within this pairing
            if i % 2 == 0:
                first_bot_path = bot1_path
                second_bot_path = bot2_path
                first_bot_name = bot_names[bot1_index]
                second_bot_name = bot_names[bot2_index]
            else:
                first_bot_path = bot2_path
                second_bot_path = bot1_path
                first_bot_name = bot_names[bot2_index]
                second_bot_name = bot_names[bot1_index]


            status_label.config(text=f"Турнир {game_num + 1}/{num_games}, Игра {i + 1}: {os.path.basename(first_bot_path)} vs {os.path.basename(second_bot_path)}...")
            master.update()
            print(f"Starting Game {i + 1}: {first_bot_name} vs {second_bot_name}")
            winner = play_game(first_bot_path, second_bot_path, move_duration)
            print(f"Game {i + 1} Result: Winner = {winner}")


            if winner == 1:
                bot_stats[first_bot_name]["wins"] += 1
                bot_stats[second_bot_name]["losses"] += 1
            elif winner == 2:
                bot_stats[second_bot_name]["wins"] += 1
                bot_stats[first_bot_name]["losses"] += 1
            else:
                bot_stats[first_bot_name]["draws"] += 1
                bot_stats[second_bot_name]["draws"] += 1

            update_stats_display()

        status_label.config(text="Все турниры завершены!")
        master.update()
        messagebox.showinfo("Турниры завершены", "Все турниры между ботами завершены. Результаты внизу.")


def play_game(bot1_path, bot2_path, move_duration):
    """Plays a single game between two bots."""
    global buttons, master
    board = [0] * 9  # 0: empty, 1: X, 2: O
    player_turn = 1  # 1: bot1 (X), 2: bot2 (O)
    moves_made = 0
    winner = 0  # Initialize winner
    print("Starting a new game")

    while moves_made < 9 and winner == 0:
        print(f"Move {moves_made + 1}, Player {player_turn}")
        update_board_display(board)
        master.update()  # Force update to show the updated board
        time.sleep(float(move_duration) / 1000)

        # Choose the bot to play this turn
        bot_path = bot1_path if player_turn == 1 else bot2_path
        try:
            move = get_bot_move(bot_path, board, player_turn, move_duration)
            print(f"Bot at {bot_path} returned move: {move}")
        except Exception as e:
            print(f"Ошибка при выполнении хода ботом: {e}")
            # Assume the other player wins if a bot errors.
            winner = 2 if player_turn == 1 else 1
            break  # exit the loop
        if move is None:
            print("Бот вернул None.")
            winner = 2 if player_turn == 1 else 1
            break  # exit the loop

        if not (0 <= move <= 8):
            print("Неверный ход от бота (вне диапазона).")
            winner = 2 if player_turn == 1 else 1
            break  # exit the loop

        if board[move] != 0:
            print("Неверный ход от бота (клетка занята).")
            winner = 2 if player_turn == 1 else 1
            break  # exit the loop

        board[move] = player_turn
        moves_made += 1
        winner = check_winner(board)
        if winner:
            print(f"Winner found: {winner}")
            break  # exit the loop


        player_turn = 3 - player_turn  # Switch player (1 <-> 2)
        print(f"Switching player to {player_turn}")

    # If the loop completes without a winner, it's a draw
    update_board_display(board)
    master.update()
    print(f"Game over, returning winner {winner}")
    return winner  # Return the winner (0 for draw)


def get_bot_move(bot_path, board, player_turn, move_duration):
    """Calls the bot executable and retrieves its move."""
    try:
        # Write the current board state to game.txt
        with open("game.txt", "w") as f:
            f.write("".join(map(str, board)))

        # Run the bot as a subprocess
        print(f"Running bot: {bot_path}")
        result = subprocess.run([bot_path], capture_output=True, text=True, timeout=move_duration / 1000, creationflags=subprocess.CREATE_NO_WINDOW) #added creationflags
        print(f"Bot finished with return code: {result.returncode}")

        # Check for errors
        if result.returncode != 0:
            print(f"Ошибка при выполнении бота: {result.stderr}")
            return None

        # Parse the bot's move from its output
        move_str = result.stdout.strip()
        print(f"Bot output: {move_str}")
        try:
            move = int(move_str)
            return move
        except ValueError:
            print(f"Неверный формат хода от бота: {move_str}")
            return None

    except subprocess.TimeoutExpired:
        print("Время хода бота истекло.")
        return None  # Bot timed out
    except FileNotFoundError:
        print(f"Бот не найден: {bot_path}")
        return None  # Bot executable not found
    except Exception as e:
        print(f"Ошибка при вызове бота: {e}")
        return None  # Other error occurred


def check_winner(board):
    """Checks the board for a winner. Returns 1 for X, 2 for O, or 0 for no winner."""
    winning_combinations = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
        [0, 4, 8], [2, 4, 6]  # Diagonals
    ]

    for combo in winning_combinations:
        a, b, c = combo
        if board[a] != 0 and board[a] == board[b] == board[c]:
            return board[a]

    # Check for a draw (all cells filled)
    if all(cell != 0 for cell in board):
        return 0

    return 0  # No winner yet


def update_board_display(board):
    """Updates the GUI to reflect the current state of the board."""
    global buttons, master
    symbols = {0: "", 1: "X", 2: "O"}
    colors = {1: "red", 2: "blue"}  # Define colors for X and O

    for i in range(3):
        for j in range(3):
            symbol = symbols[board[i * 3 + j]]
            color = colors.get(board[i * 3 + j], "black")  # Get color or default to black
            buttons[i][j]['text'] = symbol
            buttons[i][j]['foreground'] = color
            buttons[i][j].update() # Force the button to update its display
    master.update() # Make sure the main window updates too


def update_stats_display():
    """Updates the statistics display at the bottom of the window."""
    global stats_label, bot_stats
    stats_text = "Статистика:\n"
    for bot_name, stats in bot_stats.items():
        stats_text += f"{bot_name}: Wins: {stats['wins']}, Losses: {stats['losses']}, Draws: {stats['draws']}\n"
    stats_label.config(text=stats_text)


# --- UI Initialization and Main Loop ---
master = tk.Tk()
master.title("Крестики-Нолики: Битва Ботов")

bot_paths_label = ttk.Label(master, text="Пути к ботам (через пробел):")
bot_paths_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

bot_paths_entry = ttk.Entry(master, width=50)
bot_paths_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

move_duration_label = ttk.Label(master, text="Длительность хода (мс):")
move_duration_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")

move_duration_entry = ttk.Entry(master, width=10)
move_duration_entry.insert(0, "500")  # Default move duration
move_duration_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

num_games_label = ttk.Label(master, text="Количество турниров:")
num_games_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")

num_games_entry = ttk.Entry(master, width=10)
num_games_entry.insert(0, "1")  # Default number of games
num_games_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")

play_button = ttk.Button(master, text="Играть", command=start_tournament)
play_button.grid(row=3, column=0, columnspan=2, padx=5, pady=10)

# Game Board UI
board_frame = ttk.Frame(master)
board_frame.grid(row=4, column=0, columnspan=2, padx=5, pady=5)

buttons = []  # Initialize buttons list
for i in range(3):
    row_buttons = []
    for j in range(3):
        button = tk.Button(board_frame, text="", width=5, command=lambda row=i, col=j: cell_clicked(row, col))  # Use tk.Button
        button.grid(row=i, column=j, padx=2, pady=2)
        row_buttons.append(button)
    buttons.append(row_buttons)


status_label = ttk.Label(master, text="Ожидание начала турнира...")
status_label.grid(row=5, column=0, columnspan=2, padx=5, pady=5)

stats_label = ttk.Label(master, text="Статистика:\n")
stats_label.grid(row=6, column=0, columnspan=2, padx=5, pady=5, sticky="w")

master.grid_columnconfigure(1, weight=1)  # Make the entry stretch

master.mainloop()
