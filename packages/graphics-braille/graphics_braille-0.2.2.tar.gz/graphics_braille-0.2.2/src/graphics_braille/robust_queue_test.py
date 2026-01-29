#robust_queue_test.py

from multiprocessing import Process
from time import sleep
from random import randint

import graphics_braille
import robust_queue as rq

# A simple use case of the custom Queue that allows .qsize() method
# in MacOS X.

def foo(q):
    i = 0
    while True:
        q.put(f'current i = {i}')
        sleep(randint(0, 3))
        i += 1


if __name__ == '__main__':
    q: rq.RQueue = rq.RQueue()
    p: Process = Process(target=foo, args=(q,))
    p.start()

    times = 0
    while times < 5:
        print(f'current qsize = {q.qsize()}')
        if not q.empty():
            print(f'qsize = {q.qsize()} before get')
            print(f'Item got from queue: {q.get()}')
            print(f'qsize = {q.qsize()} after get')
        times += 1
        sleep(randint(0, 3))

    p.terminate()
    p.join()
    print(f'qsize = {q.qsize()} at the end')