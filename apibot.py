import sys
import time
import random
from api import TankGameAPI

def main():
    #определение параметров подключения
    host = "127.0.0.1"
    port = 5000
    
    #использование аргументов командной строки, если они есть
    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        port = int(sys.argv[2])
    
    print(f"подключение к серверу {host}:{port}...")
    
    #создание и подключение api
    api = TankGameAPI(host, port)
    if not api.connect():
        print("не удалось подключиться к серверу")
        return
    
    tank_num = api.tank_id + 1 if api.tank_id is not None else "неизвестный"
    print(f"успешное подключение! мой танк: {tank_num}")
    
    try:
        #основной цикл работы бота
        while True:
            #получение состояния игры
            game_state = api.get_state()
            if game_state is None:
                print("игра завершена или соединение разорвано")
                break
            
            #принятие решения и отправка команды
            cmd = get_next_command(game_state)
            api.command(cmd)
            
            #небольшая пауза для снижения нагрузки
            time.sleep(0.02)
            
    except KeyboardInterrupt:
        print("\nбот остановлен пользователем")
    finally:
        #гарантированное закрытие соединения
        api.close()
        print("соединение закрыто")

def get_next_command(state):
    #извлечение полезной информации из состояния игры
    self_tank = state.get("self", {})
    ammo = self_tank.get("ammo", 0)
    enemies = state.get("enemies", [])
    
    command = ""
    
    #случайное вращение (влево/вправо)
    if random.random() < 0.6:
        command += random.choice("lr")
    
    #случайное движение (вперед/назад)
    if random.random() < 0.7:
        command += random.choice("fb")
    
    #приоритет стрельбы, если есть враги в зоне видимости
    if enemies and ammo > 0:
        if random.random() < 0.8:  # высокая вероятность стрельбы при наличии целей
            command += "s"
    else:
        #иногда стреляем просто так, если есть патроны
        if ammo > 0 and random.random() < 0.2:
            command += "s"
    
    #минимум одно действие в каждом шаге
    if not command:
        command = "f"  #по умолчанию двигаемся вперед
    
    return command

if __name__ == "__main__":
    main()
