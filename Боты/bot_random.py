import json
import random
import socket
import time
import os
import sys

def get_host_port():
    h = os.environ.get('TANKS_HOST', '172.16.8.70')
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
                continue
            c = ''.join(random.sample('lrfbs', k=random.randint(1, 2)))
            s.sendall((c + '\n').encode('utf-8'))
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