
from subprocess import Popen, PIPE
from threading import Thread

def __controllerThread(program, device, lock):

    process = Popen(program, stdin=PIPE, stdout=PIPE)

    try:
        while process.poll() is None:
            question = process.stdout.readline().decode()

            if question and question[-1] == '\n':
                question = question[:-1]

            with lock:
                if device.isDestroyed():
                    break
                answer = device.communicate(question)

            process.stdin.write(answer.encode())
            process.stdin.write(b'\n')
            process.stdin.flush()

    except BrokenPipeError:
        pass

    process.send_signal(signal.SIGHUP)

def loadController(program_path, ship, lock):

    return Thread(target=__controllerThread, daemon=True,
                  args=([program_path], ship, lock))
