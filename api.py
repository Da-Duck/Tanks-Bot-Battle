"""
🤖 BOT API - Простое подключение ботов
Импортируйте этот файл в свой бот и пишите только логику!
"""

import socket
import json
import time
import math


class BotAPI:
    """
    Простой API для написания ботов
    
    Пример использования:
    ```python
    from api import BotAPI
    
    class MyBot(BotAPI):
        def logic(self, fov):
            return "f"  # Команда
    
    bot = MyBot(host='localhost', port=5000)
    bot.run()
    ```
    """
    
    def __init__(self, host='localhost', port=5000):
        """Инициализация бота"""
        self.host = host
        self.port = port
        self.sock = None
        self.file = None
        self.tank_id = None
        self.connected = False
    
    def connect(self):
        """Подключиться к серверу"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            
            self.file = self.sock.makefile('r', encoding='utf-8')
            hello = json.loads(self.file.readline().strip())
            
            self.tank_id = hello.get('tank_id')
            self.connected = True
            
            print(f"✅ Бот подключен! ID: {self.tank_id + 1}")
            return True
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            return False
    
    def send_command(self, command):
        """Отправить команду на сервер"""
        if not command:
            return
        try:
            msg = json.dumps({"cmd": command}) + "\n"
            self.sock.sendall(msg.encode('utf-8'))
        except:
            self.connected = False
    
    def receive_fov(self):
        """Получить состояние игры"""
        try:
            line = self.file.readline()
            if line:
                return json.loads(line.strip())
        except:
            pass
        return None
    
    def distance(self, x1, y1, x2, y2):
        """Расстояние между точками"""
        return math.hypot(x2 - x1, y2 - y1)
    
    def angle_to(self, my_x, my_y, target_x, target_y):
        """Угол к цели (радианы)"""
        return math.atan2(target_y - my_y, target_x - my_x)
    
    def angle_diff(self, a1, a2):
        """Разница углов"""
        diff = (a2 - a1 + math.pi) % (2 * math.pi) - math.pi
        return diff
    
    def logic(self, fov):
        """
        ВАШ КОД ЗДЕСЬ!
        
        Args:
            fov: словарь с состоянием игры
                fov['bot'] - ваша позиция {'x': ..., 'y': ..., 'a': ..., 'hp': ...}
                fov['tanks'] - враги [{'tank_id': ..., 'x': ..., 'y': ..., ...}, ...]
                fov['walls'] - стены [[x1, y1, x2, y2], ...]
                fov['water'] - вода [[x1, y1, x2, y2], ...]
                fov['dest'] - разрушаемое [[x1, y1, x2, y2], ...]
                fov['bullets'] - пули [{'x': ..., 'y': ...}, ...]
        
        Returns:
            str: команда ("f", "b", "l", "r", "s" или комбинация "lfs")
        """
        return ""  # Переопределите в своем классе!
    
    def run(self):
        """Главный цикл бота"""
        if not self.connect():
            return
        
        print("▶️  Бот запущен!")
        
        try:
            while self.connected:
                fov = self.receive_fov()
                if fov is None:
                    break
                
                command = self.logic(fov)
                if command:
                    self.send_command(command)
                
                time.sleep(0.02)
        except KeyboardInterrupt:
            print("\n⏹️  Бот остановлен")
        except Exception as e:
            print(f"\n❌ Ошибка: {e}")
        finally:
            self.disconnect()
    
    def disconnect(self):
        """Отключиться от сервера"""
        try:
            if self.sock:
                self.sock.close()
        except:
            pass
        self.connected = False
        print("📴 Отключено")
