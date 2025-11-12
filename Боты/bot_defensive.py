import json
import math
import socket
import time
import os
import sys

def ang(a):
    while a < -math.pi:
        a += 2 * math.pi
    while a > math.pi:
        a -= 2 * math.pi
    return a

def dist(x1, y1, x2, y2):
    return math.hypot(x2 - x1, y2 - y1)

def get_host_port():
    h = os.environ.get('TANKS_HOST', '127.0.0.1')
    p = int(os.environ.get('TANKS_PORT', '5000'))
    if len(sys.argv) >= 2: h = sys.argv[1]
    if len(sys.argv) >= 3:
        try: p = int(sys.argv[2])
        except: pass
    return h, p

def main():
    h, p = get_host_port()
    s = None
    f = None
    sd = 1
    tank_id = None
    while True:
        try:
            if s is None:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((h, p))
                f = s.makefile('r', encoding='utf-8', newline='\n')
            ln = f.readline()
            if not ln:
                raise ConnectionError('closed')
            j = json.loads(ln)
            if j.get('hello'):
                tank_id = j.get('tank_id', tank_id)
                continue
            b = j.get('bot') or {}
            a = float(b.get('a', b.get('angle', 0.0)))
            x = float(b.get('x', 0.0))
            y = float(b.get('y', 0.0))
            hp = int(b.get('hp', 3))
            ts = j.get('tanks') or []
            bl = j.get('bullets') or []

            cmd = ''

            nb = None
            nd = 1e9
            for q in bl:
                qx = float(q.get('x', 0.0)); qy = float(q.get('y', 0.0))
                d = dist(x, y, qx, qy)
                if d < nd:
                    nd = d; nb = (qx, qy)
            if nb and nd < 90:
                cmd += 'f'
                cmd += 'r' if sd > 0 else 'l'
                sd *= -1
                s.sendall((cmd + '\n').encode('utf-8'))
                continue

            if not ts:
                s.sendall(('f\n').encode('utf-8'))
                continue

            e = min(ts, key=lambda q: dist(x, y, q.get('x', 0.0), q.get('y', 0.0)))
            ex = float(e.get('x', 0.0))
            ey = float(e.get('y', 0.0))
            d = dist(x, y, ex, ey)
            ta = math.atan2(ey - y, ex - x)
            da = ang(ta - a)

            if d < 170 or hp <= 1:
                cmd += 'b'
            elif d > 230:
                cmd += 'f'

            if abs(da) > 0.08:
                cmd += 'r' if da > 0 else 'l'

            if d < 260 and abs(da) < 0.12:
                cmd += 's'

            if not cmd:
                cmd = 'r'

            s.sendall((cmd + '\n').encode('utf-8'))
        except Exception:
            try:
                if f:
                    f.close()
            except Exception:
                pass
            try:
                if s:
                    s.close()
            except Exception:
                pass
            s = None
            f = None
            time.sleep(1.0)

if __name__ == '__main__':
    main()