import socket
import json
import sys
import time
import random
from api import TankAPI

def main():
    host = "127.0.0.1"
    port = 5000
    
    if len(sys.argv) >= 3:
        host = sys.argv[1]
        port = int(sys.argv[2])
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    
    text = sock.makefile("r", encoding="utf-8")
    hello = text.readline().strip()
    
    try:
        hellojson = json.loads(hello)
        tankid = hellojson.get("tank_id")
        if tankid is not None:
            print(f"API бот запущен для танка: {tankid + 1}")
    except json.JSONDecodeError:
        print("не удалось прочитать приветствие от сервера")
    
    while True:
        line = text.readline()
        if not line:
            print("соединение закрыто сервером")
            break
        
        line = line.strip()
        if not line:
            continue
        
        try:
            view = json.loads(line)
        except json.JSONDecodeError:
            continue
        
        # Используем API для принятия решений
        api = TankAPI(view)
        command = api.get_command()
        
        # Отправляем команду на сервер
        message = json.dumps({"cmd": command})
        try:
            sock.sendall((message + "\n").encode("utf-8"))
        except OSError:
            print("ошибка отправки команды, выходим")
            break
        
        # Задержка для синхронизации
        time.sleep(0.03)
    
    text.close()
    sock.close()

if __name__ == "__main__":
    main()