
import time

import signal
from subprocess import Popen, PIPE
from threading import Thread, Lock

def __controllerThreadWatcher(process, device, lock):

    while True:
        with lock:
            if device.isDestroyed():
                break
        time.sleep(1)

    process.send_signal(signal.SIGHUP)

def __controllerThread(pstdout, pstdin, device, lock):

    try:
        while True:
            question = pstdout.readline().decode()

            if question and question[-1] == '\n':
                question = question[:-1]

            with lock:
                answer = device.communicate(question)

            pstdin.write(answer.encode())
            pstdin.write(b'\n')
            pstdin.flush()

    except BrokenPipeError:
        pass

def loadController(program_path, ship, json_info, lock):

    process = Popen([program_path, json_info], stdin=PIPE, stdout=PIPE)

    Thread(target=__controllerThreadWatcher,
           args=(process, ship, lock)).start()

    return Thread(target=__controllerThread, daemon=True,
                  args=(process.stdout, process.stdin, ship, lock))
