import json
import math
import random
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
    t = 0
    sp = 1
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
            ts = j.get('tanks') or []
            if not ts:
                s.sendall((('fr' if t % 20 < 10 else 'fl') + '\n').encode('utf-8'))
                t += 1
                continue
            e = min(ts, key=lambda q: dist(x, y, q.get('x', 0.0), q.get('y', 0.0)))
            ex = float(e.get('x', 0.0))
            ey = float(e.get('y', 0.0))
            d = dist(x, y, ex, ey)
            ta = math.atan2(ey - y, ex - x)
            da = ang(ta - a)

            cmd = ''
            if d > 180:
                cmd += 'f'
            else:
                cmd += 'f'
                cmd += 'r' if sp > 0 else 'l'

            if abs(da) > 0.08:
                cmd += 'r' if da > 0 else 'l'

            if d < 260 and abs(da) < 0.15:
                cmd += 's'

            if not cmd:
                cmd = 'f'

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