import socket
import json
import random
import time
import sys

# задаем адрес сервера по умолчанию
host = "127.0.0.1"
port = 5000

# если указали адрес и порт в аргументах, используем их
if len(sys.argv) >= 3:
    host = sys.argv[1]
    port = int(sys.argv[2])

# создаем tcp соединение с сервером игры
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((host, port))

# переключаемся на построчное чтение текста из сокета
text = sock.makefile("r", encoding="utf-8")

# читаем первую строку с приветствием от сервера
hello = text.readline().strip()

# пытаемся показать номер танка, если он есть
try:
    hellojson = json.loads(hello)
    tankid = hellojson.get("tank_id")
    if tankid is not None:
        print(f"мой танк: {tankid + 1}")
except json.JSONDecodeError:
    print("не удалось прочитать приветствие от сервера")

# основной цикл бота
while True:
    # читаем очередное состояние поля от сервера
    line = text.readline()
    if not line:
        # если сервер закрыл соединение, выходим
        print("соединение закрыто сервером")
        break

    line = line.strip()
    if not line:
        continue

    try:
        view = json.loads(line)
    except json.JSONDecodeError:
        # если пришло что-то непонятное, просто пропускаем
        continue

    # простая случайная тактика:
    # иногда поворачиваем, иногда едем, иногда стреляем
    command = ""

    # с небольшой вероятностью поворачиваем в случайную сторону
    if random.random() < 0.6:
        command += random.choice("lr")

    # с небольшой вероятностью едем вперед или назад
    if random.random() < 0.8:
        command += random.choice("fb")

    # если видим врагов и есть патроны, чаще жмем на выстрел
    enemies = view.get("enemies", [])
    ammo = view.get("self", {}).get("ammo", 0)
    if enemies and ammo > 0 and random.random() < 0.7:
        command += "s"
    elif random.random() < 0.1 and ammo > 0:
        command += "s"

    # если команда пустая, все равно немного дернемся вперед
    if not command:
        command = "f"

    # упаковываем команду в json и отправляем на сервер
    message = json.dumps({"cmd": command})
    try:
        sock.sendall((message + "\n").encode("utf-8"))
    except OSError:
        # если не удалось отправить команду, аккуратно выходим
        print("ошибка отправки команды, выходим")
        break

    # делаем небольшую паузу, чтобы не спамить сервер
    time.sleep(0.03)

# закрываем соединение и файловый объект
text.close()
sock.close()