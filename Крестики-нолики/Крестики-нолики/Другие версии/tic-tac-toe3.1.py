import tkinter as tk
from tkinter import messagebox
import subprocess
import time
import threading
import os


root = None
board = '000000000'
available_moves = {'0', '1', '2', '3', '4', '5', '6', '7', '8'}
move_count = 0
last_position = 0
game_active = False
bot1_file = ""
bot2_file = ""
wins1 = 0
wins2 = 0
draws = 0
delay = 1000
auto_play_count = 0
auto_running = False
result_label = None
buttons = []
stat_label = None
bot1_entry = None
bot2_entry = None
speed_entry = None
auto_play_entry = None

def create_menu():
    global bot1_entry, bot2_entry, speed_entry, auto_play_entry

    menu_frame = tk.Frame(root)
    menu_frame.pack(pady=20)

    tk.Label(menu_frame, text="Путь к боту 1:").grid(row=0, column=0, padx=5)
    bot1_entry = tk.Entry(menu_frame, width=30)
    bot1_entry.grid(row=0, column=1, padx=5, columnspan=2)

    tk.Label(menu_frame, text="Путь к боту 2:").grid(row=1, column=0, padx=5)
    bot2_entry = tk.Entry(menu_frame, width=30)
    bot2_entry.grid(row=1, column=1, padx=5, columnspan=2)

    tk.Label(menu_frame, text="Скорость (мс):").grid(row=2, column=0, padx=5)
    speed_entry = tk.Entry(menu_frame, width=10)
    speed_entry.grid(row=2, column=1, padx=5)
    speed_entry.insert(0, "1000")
    speed_button = tk.Button(menu_frame, text="Изменить скорость", command=change_speed)
    speed_button.grid(row=2, column=2, padx=5)

    tk.Label(menu_frame, text="Кол-во игр:").grid(row=3, column=0, padx=5)
    auto_play_entry = tk.Entry(menu_frame, width=10)
    auto_play_entry.grid(row=3, column=1, padx=5)
    auto_play_button = tk.Button(menu_frame, text="Запустить несколько игр", command=start_auto_play)
    auto_play_button.grid(row=3, column=2, padx=5)

    start_button = tk.Button(menu_frame, text="Играть", command=start_game, bg="green")
    start_button.grid(row=4, column=0, columnspan=3, pady=10)

    global result_label
    result_label = tk.Label(menu_frame, text="", font=('Arial', 12), wraplength=350)
    result_label.grid(row=5, column=0, columnspan=3, pady=5)


def change_speed():
    global delay
    try:
        speed = int(speed_entry.get())
        if speed > 0:
            delay = speed
        else:
            messagebox.showerror("Ошибка", "Скорость должна быть положительным числом")
    except ValueError:
        messagebox.showerror("Ошибка", "Неверный формат скорости")


def create_game_board():
    global buttons

    board_frame = tk.Frame(root)
    board_frame.pack()
    buttons = []
    for i in range(9):
        btn = tk.Button(board_frame, text=" ", font=('Arial', 40), width=3, height=1,
                        command=lambda x=i: make_move(x))
        btn.grid(row=i // 3, column=i % 3, padx=5, pady=5)
        buttons.append(btn)

    disable_board()


def create_statistics():
    global stat_label
    stat_label = tk.Label(root, text="Бот 1: 0  |  Ничьи: 0  | Бот 2: 0", font=('Arial', 12))
    stat_label.pack(pady=10)


def start_game():
    global bot1_file, bot2_file, board, move_count, game_active

    if auto_running:
        messagebox.showinfo("Внимание", "Дождитесь завершения автоигр!")
        return
    bot1_file = bot1_entry.get()
    bot2_file = bot2_entry.get()

    if not bot1_file or not bot2_file:
        messagebox.showerror("Ошибка", "Пожалуйста, введите пути к файлам ботов.")
        return

    if not os.path.exists(bot1_file) or not os.path.exists(bot2_file):
        messagebox.showerror("Ошибка", "Один или оба файла бота не найдены.")
        return

    board = '000000000'
    move_count = 0
    update_board()
    game_active = True
    enable_board()
    result_label.config(text="")
    play_round()


def start_auto_play():
    global auto_play_count

    if auto_running:
        messagebox.showinfo("Внимание", "Дождитесь завершения автоигр!")
        return
    try:
        count = int(auto_play_entry.get())
        if count > 0:
            auto_play_count = count
            run_auto_games()
        else:
            messagebox.showerror("Ошибка", "Количество игр должно быть положительным числом")
    except ValueError:
        messagebox.showerror("Ошибка", "Неверный формат количества игр")


def run_auto_games():
    global bot1_file, bot2_file, wins1, wins2, draws, auto_running

    bot1_file = bot1_entry.get()
    bot2_file = bot2_entry.get()

    if not bot1_file or not bot2_file:
        messagebox.showerror("Ошибка", "Пожалуйста, введите пути к файлам ботов.")
        return

    if not os.path.exists(bot1_file) or not os.path.exists(bot2_file):
        messagebox.showerror("Ошибка", "Один или оба файла бота не найдены.")
        return

    disable_board()
    wins1 = 0
    wins2 = 0
    draws = 0
    auto_running = True
    result_label.config(text="")

    def auto_play_loop():
        global board, move_count, game_active
        for _ in range(auto_play_count):
            board = '000000000'
            move_count = 0
            game_active = True
            auto_play_game()
            while game_active:
                time.sleep(0.01)
        root.after(0, enable_board)
        root.after(0, update_stat)
        auto_running = False

    threading.Thread(target=auto_play_loop).start()


def auto_play_game():
    global game_active
    if not game_active:
        return
    auto_process_move()


def update_board():
    global buttons, board
    for i in range(9):
        if board[i] == '0':
            buttons[i].config(text=" ", fg="black")
        elif board[i] == '1':
            buttons[i].config(text='X', fg="red")
        elif board[i] == '2':
            buttons[i].config(text='O', fg="blue")


def disable_board():
    global buttons
    for btn in buttons:
        btn.config(state=tk.DISABLED)


def enable_board():
    global buttons
    for btn in buttons:
        btn.config(state=tk.NORMAL)


def make_move(move):
    global game_active
    if not game_active:
        return
    process_move()


def process_move():
    global game_active, move_count, bot1_file, bot2_file, board, last_position

    if not game_active:
        return

    move_count = move_count % 2 + 1
    bot_file = bot1_file if move_count == 1 else bot2_file

    try:
        with open('game.txt', 'w') as file:
            file.write(board)

        process = subprocess.Popen([bot_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        end_game(f'Файл бота {move_count} не найден.', True)
        return

    try:
        stdout, stderr = process.communicate(timeout=2)
        if stderr:
            end_game(f'Ошибка бота {move_count}: {stderr.decode()}', True)
            return

        move = stdout.decode().strip()
    except subprocess.TimeoutExpired:
        process.kill()
        end_game(f'Превышено время ожидания бота {move_count}', True)
        return

    if move not in available_moves:
        end_game(f'Неправильный формат вывода бота {move_count}', True)
        return

    last_position = board[int(move)]

    board_list = list(board)
    board_list[int(move)] = str(move_count)
    board = ''.join(board_list)
    update_board()

    if last_position != '0':
        end_game(f'Неправильный ход бота {move_count}', True)
        return

    if win():
        end_game(f'Победа бота {move_count}')
    elif draw():
        end_game('Ничья')
    else:
        play_round()


def auto_process_move():
    global game_active, move_count, bot1_file, bot2_file, board, last_position

    if not game_active:
        return

    move_count = move_count % 2 + 1
    bot_file = bot1_file if move_count == 1 else bot2_file

    try:
        with open('game.txt', 'w') as file:
            file.write(board)

        process = subprocess.Popen([bot_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        end_game(f'Файл бота {move_count} не найден.', True)
        return

    try:
        stdout, stderr = process.communicate(timeout=2)
        if stderr:
            end_game(f'Ошибка бота {move_count}: {stderr.decode()}', True)
            return

        move = stdout.decode().strip()
    except subprocess.TimeoutExpired:
        process.kill()
        end_game(f'Превышено время ожидания бота {move_count}', True)
        return

    if move not in available_moves:
        end_game(f'Неправильный формат вывода бота {move_count}', True)
        return

    last_position = board[int(move)]

    board_list = list(board)
    board_list[int(move)] = str(move_count)
    board = ''.join(board_list)

    if last_position != '0':
        end_game(f'Неправильный ход бота {move_count}', True)
        return

    if win():
        end_game(f'Победа бота {move_count}')
    elif draw():
        end_game('Ничья')
    else:
        root.after(1, auto_play_game)


def win():
    global board
    for i in range(0, 9, 3):
        if board[i] == board[i + 1] == board[i + 2] != '0':
            return True
    for i in range(3):
        if board[i] == board[i + 3] == board[i + 6] != '0':
            return True
    if board[0] == board[4] == board[8] != '0' or (board[2] == board[4] == board[6] != '0'):
        return True
    return False


def draw():
    global board
    for i in range(9):
        if board[i] == '0':
            return False
    return True


def end_game(message, forfeit=False):
    global game_active, wins1, wins2, draws
    game_active = False
    winner_message = ""
    if forfeit:
        if move_count == 1:
            wins2 += 1
            winner_message = "Техническое поражение. Победа бота 2!"
        else:
            wins1 += 1
            winner_message = "Техническое поражение. Победа бота 1!"
    elif message.startswith('Победа бота 1'):
        wins1 += 1
        winner_message = "Победа бота 1!"
    elif message.startswith('Победа бота 2'):
        wins2 += 1
        winner_message = "Победа бота 2!"
    else:
        draws += 1
        winner_message = "Ничья!"

    result_label.config(text=winner_message)
    update_stat()


def play_round():
    global game_active
    if game_active:
        root.after(delay, process_move)


def update_stat():
    global stat_label, wins1, wins2, draws
    stat_label.config(text=f"Бот 1: {wins1}  |  Ничьи: {draws}  | Бот 2: {wins2}")


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Битва Ботов Крестики-Нолики")
    root.minsize(400, 400)

    create_menu()
    create_game_board()
    create_statistics()

    root.mainloop()