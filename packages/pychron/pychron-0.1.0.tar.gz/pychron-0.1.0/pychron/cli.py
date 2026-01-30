import subprocess
import sys
import threading
import time
from datetime import datetime

_timer_running = False
_timer_start = None
_PRINT_LOCK = threading.Lock()


def timer_loop():
    global _timer_running, _timer_start
    start = _timer_start
    with _PRINT_LOCK:
        sys.stdout.write(f"\n\n\033[91mpychron:>\033[0m Start: {start.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        sys.stdout.flush()
    time.sleep(1)
    while _timer_running:
        now = datetime.now()
        elapsed = int((now - start).total_seconds())
        line = f"\033[91mpychron:>\033[0m Waiting: {now.strftime('%Y-%m-%d %H:%M:%S')} | Elapsed: {elapsed} sec"
        with _PRINT_LOCK:
            sys.stdout.write('\r' + line)
            sys.stdout.flush()
        time.sleep(1)


def run():
    global _timer_running, _timer_start
    if len(sys.argv) < 2:
        print("Usage: \033[91mpychron:>\033[0m <script.py> [args...]")
        sys.exit(1)
    script = sys.argv[1]
    args = sys.argv[2:]
    _timer_start = datetime.now()
    _timer_running = True
    t = threading.Thread(target=timer_loop, daemon=True)
    t.start()
    process = subprocess.Popen(
        [sys.executable, "-u", script] + args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    for line in process.stdout:
        with _PRINT_LOCK:
            sys.stdout.write('\r' + ' ' * 80 + '\r')
            sys.stdout.write(line)
            if not line.endswith('\n'):
                sys.stdout.write('\n')
            sys.stdout.flush()
    process.wait()
    _timer_running = False
    t.join(timeout=1.0)
    now = datetime.now()
    elapsed = int((now - _timer_start).total_seconds())
    with _PRINT_LOCK:
        sys.stdout.write('\r' + ' ' * 80 + '\r')
        sys.stdout.write(f"\n\n\033[91mpychron:>\033[0m Finish: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        sys.stdout.write(f"\n\033[91mpychron:>\033[0m Total time: {elapsed} sec\n\n")
        sys.stdout.flush()


def main():
    run()


if __name__ == "__main__":
    main()
