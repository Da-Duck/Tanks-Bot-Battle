import time
import subprocess
import random

def play_tic_tac_toe(bot1_file, bot2_file):
    board = '000000000'
    lst = {'0', '1', '2', '3', '4', '5', '6', '7', '8'}
    move = 0
    count = 0
    lastpos = 0

    def output():
        for i in range(9):
            if board[i] == '0':
                print(' ', end='')
            if board[i] == '1':
                print('X', end='')
            if board[i] == '2':
                print('O', end='')

            if i == 2 or i == 5:
                print()
                print('-----')
            elif i != 8:
                print('|', end='')
        print()

    def win():
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
        for i in range(9):
            if board[i] != '0':
                return False
        return True

    file = open('game.txt', 'w')
    file.write('000000000')
    file.close()

    while True:


        move = -1
        count = count % 2 + 1

        if count == 1:
            process = subprocess.Popen(['python', bot1_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            process = subprocess.Popen(['python', bot2_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        try:
            stdout, stderr = process.communicate(timeout=1)
            if stderr:
                return -1
            move = stdout.decode().strip()
        except subprocess.TimeoutExpired:
            process.kill()
            return -1

        if move == -1:
            return -1

        if not(move in lst):
            return -1

        lastpos = board[int(move)]

        board = list(board)
        board[int(move)] = str(count)
        board = ''.join(board)

        file = open('game.txt', 'w')
        file.write(board)
        file.close()


        if lastpos != '0':
            return -1

        if win():
            return count

        if draw():
            return 0


def main():
    num_bots = int(input("Введите количество ботов: "))
    num_games = int(input("Введите количество игр между каждой парой: "))

    bot_files = []
    for i in range(num_bots):
        bot_file = input(f"Введите имя файла для бота {i+1}: ")
        bot_files.append(bot_file)
    
    wins = [0] * num_bots
    losses = [0] * num_bots
    draws = [0] * num_bots

    for i in range(num_bots):
        for j in range(i + 1, num_bots):
            for _ in range(num_games):
                result = play_tic_tac_toe(bot_files[i], bot_files[j])
                if result == 1:
                    wins[i] +=1
                    losses[j] +=1
                elif result == 2:
                    wins[j] +=1
                    losses[i] +=1
                elif result == 0:
                    draws[i] += 1
                    draws[j] += 1
                else:
                    wins[j if result == 1 else i] += 1
                    losses[i if result == 1 else j] += 1
                

    print("\n--- Общая статистика ---")
    for i in range(num_bots):
        total_games = sum([wins[i], losses[i], draws[i]])
        win_rate = (wins[i] / total_games) * 100 if total_games > 0 else 0
        print(f"Bot {i+1}: Побед: {wins[i]}, Поражений: {losses[i]}, Ничьих: {draws[i]}, Процент побед: {win_rate:.2f}%")


if __name__ == "__main__":
    main()