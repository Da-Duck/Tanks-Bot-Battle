import time
import subprocess

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

bot1_file = input("Введите имя файла для бота 1: ")
bot2_file = input("Введите имя файла для бота 2: ")

print('Начало битвы ботов')
output()

file = open('game.txt', 'w')
file.write('000000000')
file.close()

while True:
    
    time.sleep(1)
    
    move = -1
    count = count % 2 + 1
    
    if count == 1:
        process = subprocess.Popen(['python', bot1_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        process = subprocess.Popen(['python', bot2_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
    try:
      stdout, stderr = process.communicate(timeout=2)
      if stderr:
        print(f'Ошибка бота {count}: {stderr.decode()}')
        print('Техническое поражение.')
        break
      
      move = stdout.decode().strip()
    except subprocess.TimeoutExpired:
      process.kill()
      print(f'Превышено время ожидания бота {count}')
      print('Техническое поражение.')
      break
      
    print('Ход бота', str(count) + ':', move)

    if move == -1:
        print('Превышено время ожидания бота', count)
        print('Техническое поражение.')
        break        

    if not(move in lst):       
        print('Неправильный формат вывода бота', count)
        print('Техническое поражение.')
        break

    lastpos = board[int(move)]
    
    board = list(board)
    board[int(move)] = str(count)
    board = ''.join(board)
    
    
    output()
    
    
    file = open('game.txt', 'w')
    file.write(board)
    file.close()  


    if lastpos != '0':
        print('Неправильный ход бота', count)
        print('Техническое поражение.')
        break

    if win():
        print('Победа бота', count)
        break
    
    if draw():
        print('Ничья.')
        break