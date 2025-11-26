import socket
import json

class TankGameAPI:
    """api для удобного взаимодействия с игрой танков"""
    
    def __init__(self, host="127.0.0.1", port=5000):
        """создание объекта api с указанием хоста и порта сервера"""
        self.host = host
        self.port = port
        self.sock = None
        self.file = None
        self.tank_id = None
    
    def connect(self):
        """подключение к серверу игры и получение идентификатора танка"""
        try:
            #создание и подключение сокета
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            
            #переключение на построчное чтение
            self.file = self.sock.makefile("r", encoding="utf-8")
            
            #чтение приветственного сообщения
            hello = self.file.readline().strip()
            if not hello:
                print("сервер не отправил приветственное сообщение")
                return False
                
            #разбор json и получение идентификатора танка
            try:
                hello_data = json.loads(hello)
                self.tank_id = hello_data.get("tank_id")
                return True
            except json.JSONDecodeError:
                print(f"ошибка разбора приветствия: {hello}")
                return False
                
        except Exception as e:
            print(f"ошибка подключения к {self.host}:{self.port} - {e}")
            return False
    
    def get_state(self):
        """получение актуального состояния игры в формате словаря"""
        try:
            line = self.file.readline()
            if not line:  #соединение закрыто сервером
                return None
                
            line = line.strip()
            if not line:  #пустая строка
                return None
                
            return json.loads(line)
        except Exception as e:
            print(f"ошибка получения состояния: {e}")
            return None
    
    def command(self, cmd_str):
        """отправка команды управления танком (l,r,f,b,s)"""
        try:
            #формирование и отправка json-сообщения
            msg = json.dumps({"cmd": cmd_str})
            self.sock.sendall((msg + "\n").encode("utf-8"))
            return True
        except Exception as e:
            print(f"ошибка отправки команды '{cmd_str}': {e}")
            return False
    
    def close(self):
        """корректное закрытие соединения с сервером"""
        try:
            if self.file:
                self.file.close()
            if self.sock:
                self.sock.close()
        except Exception as e:
            print(f"ошибка при закрытии соединения: {e}")
