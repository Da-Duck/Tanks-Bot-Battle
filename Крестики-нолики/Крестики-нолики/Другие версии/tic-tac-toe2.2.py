import pygame
import time
import random
import subprocess

pygame.init()

WIDTH = 600
HEIGHT = 600
CELL_SIZE = WIDTH // 3
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
LIGHT_GRAY = (230, 230, 230)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Крестики-нолики. Битва ботов.")

font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 24)
input_font = pygame.font.Font(None, 28)
author_font = pygame.font.Font(None, 20)

board = '000000000'
lst = {'0', '1', '2', '3', '4', '5', '6', '7', '8'}
move = 0
count = 0
lastpos = 0
game_over = False
winner = None
tie = False

button_width = 200
button_height = 40
button_x = WIDTH // 2 - button_width // 2
bot1_input_rect = pygame.Rect(button_x, 100, button_width, button_height)
bot2_input_rect = pygame.Rect(button_x, 160, button_width, button_height)
start_button_rect = pygame.Rect(button_x, 220, button_width, button_height)
rules_button_rect = pygame.Rect(button_x, 280, button_width, button_height)
settings_button_rect = pygame.Rect(button_x, 340, button_width, button_height)
input_box_color = LIGHT_GRAY

bot1_file = ""
bot2_file = ""
input_active = None
show_rules = False
start_game = False
show_settings = False

bot1_wins = 0
bot2_wins = 0
ties = 0

game_speed = 1
settings_speed_rect = pygame.Rect(button_x, 100, button_width, button_height)
settings_window_rect = pygame.Rect(button_x, 160, button_width, button_height)
settings_human_rect = pygame.Rect(button_x, 220, button_width, button_height)
settings_back_rect = pygame.Rect(button_x, 280, button_width, button_height)
rules_back_rect = pygame.Rect(button_x, HEIGHT - 100, button_width, button_height)

human_game = False

def update_button_positions():
    global button_x, bot1_input_rect, bot2_input_rect, rules_button_rect, start_button_rect, settings_button_rect, settings_speed_rect, settings_window_rect, settings_back_rect, settings_human_rect, rules_back_rect
    button_x = WIDTH // 2 - button_width // 2
    bot1_input_rect = pygame.Rect(button_x, HEIGHT*0.166, button_width, button_height)
    bot2_input_rect = pygame.Rect(button_x, HEIGHT*0.266, button_width, button_height)
    start_button_rect = pygame.Rect(button_x, HEIGHT*0.366, button_width, button_height)
    rules_button_rect = pygame.Rect(button_x, HEIGHT*0.466, button_width, button_height)
    settings_button_rect = pygame.Rect(button_x, HEIGHT*0.566, button_width, button_height)
    settings_speed_rect = pygame.Rect(button_x, HEIGHT*0.166, button_width, button_height)
    settings_window_rect = pygame.Rect(button_x, HEIGHT*0.266, button_width, button_height)
    settings_human_rect = pygame.Rect(button_x, HEIGHT*0.366, button_width, button_height)
    settings_back_rect = pygame.Rect(button_x, HEIGHT*0.466, button_width, button_height)
    rules_back_rect = pygame.Rect(button_x, HEIGHT - 100, button_width, button_height)
    
    
def draw_board():
    screen.fill(WHITE)
    for i in range(1, 3):
        pygame.draw.line(screen, BLACK, (i * CELL_SIZE, 0), (i * CELL_SIZE, HEIGHT), 3)
        pygame.draw.line(screen, BLACK, (0, i * CELL_SIZE), (WIDTH, i * CELL_SIZE), 3)

    for i in range(9):
        row = i // 3
        col = i % 3
        x = col * CELL_SIZE + CELL_SIZE // 2
        y = row * CELL_SIZE + CELL_SIZE // 2
        
        if board[i] == '1':
            text = font.render("X", True, RED)
        elif board[i] == '2':
             text = font.render("O", True, BLUE)
        else:
            continue
        text_rect = text.get_rect(center=(x, y))
        screen.blit(text, text_rect)
    
    draw_statistics()
    pygame.display.flip()


def draw_statistics():
    stats_height = 40
    pygame.draw.rect(screen, BLACK, (0, HEIGHT - stats_height, WIDTH, stats_height))
    stats_text = small_font.render(f"Бот 1: {bot1_wins} | Ничьи: {ties} | Бот 2: {bot2_wins}", True, WHITE)
    stats_rect = stats_text.get_rect(center=(WIDTH // 2, HEIGHT - stats_height // 2))
    screen.blit(stats_text, stats_rect)


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
        if board[i] == '0':
            return False
    return True

def display_message(message, color, y_offset):
    text = font.render(message, True, color)
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + y_offset))
    
    outline_color = BLACK
    outline_width = 2
    
    text_surface = font.render(message, True, color)
    text_rect_outline = text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 + y_offset))
    
    for dx in range(-outline_width, outline_width + 1):
      for dy in range(-outline_width, outline_width + 1):
          if dx * dx + dy * dy <= outline_width * outline_width:
            temp_text_rect = text_rect_outline.move(dx,dy)
            screen.blit(font.render(message, True, outline_color), temp_text_rect)
    
    screen.blit(text_surface, text_rect)
    


def restart_game():
    global board, move, count, lastpos, game_over, winner, tie
    board = '000000000'
    move = 0
    count = 0
    lastpos = 0
    game_over = False
    winner = None
    tie = False
    
    file = open('game.txt', 'w')
    file.write('000000000')
    file.close()
    
    draw_board()
    
def draw_menu():
    screen.fill(WHITE)
    
    text1 = font.render("Бот 1:", True, BLACK)
    text1_rect = text1.get_rect(center=(button_x - 60, HEIGHT*0.166+button_height//2))
    screen.blit(text1, text1_rect)
    
    pygame.draw.rect(screen, input_box_color, bot1_input_rect)
    text_surface1 = input_font.render(bot1_file, True, BLACK)
    screen.blit(text_surface1, (bot1_input_rect.x + 5, bot1_input_rect.y + 5))

    text2 = font.render("Бот 2:", True, BLACK)
    text2_rect = text2.get_rect(center=(button_x - 60, HEIGHT*0.266+button_height//2))
    screen.blit(text2, text2_rect)
    
    pygame.draw.rect(screen, input_box_color, bot2_input_rect)
    text_surface2 = input_font.render(bot2_file, True, BLACK)
    screen.blit(text_surface2, (bot2_input_rect.x + 5, bot2_input_rect.y + 5))

    pygame.draw.rect(screen, GRAY, start_button_rect)
    text_start = font.render("Старт", True, BLACK)
    text_start_rect = text_start.get_rect(center=start_button_rect.center)
    screen.blit(text_start, text_start_rect)
    
    pygame.draw.rect(screen, GRAY, rules_button_rect)
    text_rules = small_font.render("Правила", True, BLACK)
    text_rules_rect = text_rules.get_rect(center=rules_button_rect.center)
    screen.blit(text_rules, text_rules_rect)
    
    pygame.draw.rect(screen, GRAY, settings_button_rect)
    text_settings = small_font.render("Настройки", True, BLACK)
    text_settings_rect = text_settings.get_rect(center=settings_button_rect.center)
    screen.blit(text_settings, text_settings_rect)
    
    draw_statistics()
    
    pygame.display.flip()

def draw_rules():
    screen.fill(WHITE)
    rules_text = [
        "Правила для ботов:",
        "0. При вводе имён файлов с кодами ботов укажите полный путь к файлам,",
        "   или, если боты находятся в одной папке с программой, достаточно",
        "   ввести только имя файлов.",
        "1. Бот не должен влиять на работу бота противника.",
        "3. Бот должен принимать на вход файл game.txt",
        "4. Бот должен выводить в консоль номер ячейки куда он сходил",
        "5. Ячейки нумеруются с 0 до 8 слева направо сверху вниз",
        "Пример файла game.txt:",
        "000102000",
        "0 - пустая клетка",
        "1 - крестик",
        "2 - нолик",
        "Пример вывода:",
        "6"
    ]
    y_offset = 50
    for line in rules_text:
        text = small_font.render(line, True, BLACK)
        text_rect = text.get_rect(center=(WIDTH // 2, y_offset))
        screen.blit(text, text_rect)
        y_offset += 30
    
    pygame.draw.rect(screen, GRAY, rules_back_rect)
    text_back = small_font.render("Назад", True, BLACK)
    text_back_rect = text_back.get_rect(center=rules_back_rect.center)
    screen.blit(text_back, text_back_rect)
    
    draw_statistics()
    pygame.display.flip()
    
def draw_settings():
    screen.fill(WHITE)
    
    pygame.draw.rect(screen, GRAY, settings_speed_rect)
    text_speed = small_font.render(f"Скорость: {game_speed}x", True, BLACK)
    text_speed_rect = text_speed.get_rect(center=settings_speed_rect.center)
    screen.blit(text_speed, text_speed_rect)
    
    pygame.draw.rect(screen, GRAY, settings_window_rect)
    text_window = small_font.render(f"Окно: {WIDTH}x{HEIGHT}", True, BLACK)
    text_window_rect = text_window.get_rect(center=settings_window_rect.center)
    screen.blit(text_window, text_window_rect)
    
    pygame.draw.rect(screen, GRAY, settings_human_rect)
    text_human = small_font.render(f"Игрок: {'Да' if human_game else 'Нет'}", True, BLACK)
    text_human_rect = text_human.get_rect(center=settings_human_rect.center)
    screen.blit(text_human, text_human_rect)
    
    pygame.draw.rect(screen, GRAY, settings_back_rect)
    text_back = small_font.render("Назад", True, BLACK)
    text_back_rect = text_back.get_rect(center=settings_back_rect.center)
    screen.blit(text_back, text_back_rect)

    author_text = author_font.render("by @daducktg", True, BLACK)
    author_rect = author_text.get_rect(center=(WIDTH // 2, settings_back_rect.bottom + 20))
    screen.blit(author_text, author_rect)
    
    draw_statistics()
    
    pygame.display.flip()


file = open('game.txt', 'w')
file.write('000000000')
file.close()

draw_menu()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if game_over:
              x, y = event.pos
              restart_button_rect = pygame.Rect(100, HEIGHT // 2 + 20, 400, 40)
              if restart_button_rect.collidepoint(x, y):
                  restart_game()
              elif pygame.Rect(100, HEIGHT // 2 + 70, 400, 40).collidepoint(x,y):
                  start_game = False
                  game_over = False
                  draw_menu()
            elif show_settings:
              x, y = event.pos
              if settings_speed_rect.collidepoint(x,y):
                  game_speed += 0.5
                  if game_speed > 10:
                      game_speed = 0.5
              elif settings_window_rect.collidepoint(x,y):
                  if WIDTH == 400:
                      WIDTH = 500
                      HEIGHT = 500
                  elif WIDTH == 500:
                      WIDTH = 600
                      HEIGHT = 600
                  elif WIDTH == 600:
                      WIDTH = 700
                      HEIGHT = 700
                  elif WIDTH == 700:
                      WIDTH = 800
                      HEIGHT = 800
                  else:
                      WIDTH = 400
                      HEIGHT = 400
                  CELL_SIZE = WIDTH // 3
                  screen = pygame.display.set_mode((WIDTH, HEIGHT))
                  update_button_positions()
              elif settings_human_rect.collidepoint(x,y):
                    human_game = not human_game
              elif settings_back_rect.collidepoint(x,y):
                show_settings = False
            elif show_rules:
                x, y = event.pos
                if rules_back_rect.collidepoint(x,y):
                    show_rules = False
            elif not start_game:
              x, y = event.pos
              if bot1_input_rect.collidepoint(x,y):
                input_active = "bot1"
              elif bot2_input_rect.collidepoint(x,y):
                input_active = "bot2"
              elif rules_button_rect.collidepoint(x,y):
                 show_rules = True
              elif start_button_rect.collidepoint(x,y):
                start_game = True
              elif settings_button_rect.collidepoint(x,y):
                  show_settings = True
              else:
                input_active = None
        if event.type == pygame.KEYDOWN:
              if input_active == "bot1":
                 if event.key == pygame.K_BACKSPACE:
                    bot1_file = bot1_file[:-1]
                 else:
                    bot1_file += event.unicode
              if input_active == "bot2":
                  if event.key == pygame.K_BACKSPACE:
                    bot2_file = bot2_file[:-1]
                  else:
                    bot2_file += event.unicode


    if not start_game and not show_settings and not show_rules:
      draw_menu()
    elif show_settings:
      draw_settings()
    elif show_rules:
        draw_rules()
    elif not game_over:
        time.sleep(1/game_speed)
        move = -1
        count = count % 2 + 1
        
        if human_game and count == 1:
             move = -1
             while not(move in lst):
                  for event in pygame.event.get():
                     if event.type == pygame.MOUSEBUTTONDOWN:
                          x,y = event.pos
                          for i in range(9):
                            row = i // 3
                            col = i % 3
                            x_cell = col * CELL_SIZE
                            y_cell = row * CELL_SIZE
                            if x_cell <= x <= x_cell+CELL_SIZE and y_cell <= y <= y_cell+CELL_SIZE:
                                  move = str(i)
                                  break
                  if move != -1:
                     break
        elif not human_game or count == 2:
          if count == 1:
              process = subprocess.Popen(['python', bot1_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
          else:
              process = subprocess.Popen(['python', bot2_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
              
          try:
              stdout, stderr = process.communicate(timeout=2)
              if stderr:
                  display_message(f'Ошибка бота {count}: Техническое поражение.', RED, 0)
                  game_over = True
                  
              else:
                move = stdout.decode().strip()
          except subprocess.TimeoutExpired:
              process.kill()
              display_message(f'Превышено время ожидания бота {count}: Техническое поражение.', RED, 0)
              game_over = True

        if not game_over:
            if move == -1:
              display_message(f'Превышено время ожидания бота {count}: Техническое поражение.', RED, 0)
              game_over = True
            elif not(move in lst):
              display_message(f'Неправильный формат вывода бота {count}: Техническое поражение.', RED, 0)
              game_over = True
            else:
              lastpos = board[int(move)]
            
              board = list(board)
              board[int(move)] = str(count)
              board = ''.join(board)
              
              draw_board()
              
              file = open('game.txt', 'w')
              file.write(board)
              file.close()

              if lastpos != '0':
                display_message(f'Неправильный ход бота {count}: Техническое поражение.', RED, 0)
                game_over = True
              elif win():
                winner = count
                game_over = True
                if winner == 1:
                  bot1_wins += 1
                elif winner == 2:
                  bot2_wins += 1
              elif draw():
                tie = True
                game_over = True
                ties += 1
    else:
        if winner:
           display_message(f'Победил бот {winner}', GREEN, -20)
        elif tie:
           display_message('Ничья.', WHITE, -20)

        pygame.draw.rect(screen, GRAY, (100, HEIGHT // 2 + 20, 400, 40))
        text = small_font.render("Начать заново", True, BLACK)
        text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 40))
        screen.blit(text, text_rect)
        
        pygame.draw.rect(screen, GRAY, (100, HEIGHT // 2 + 70, 400, 40))
        text = small_font.render("Вернуться в меню", True, BLACK)
        text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 90))
        screen.blit(text, text_rect)
        
        draw_statistics()
        pygame.display.flip()
    
pygame.quit()