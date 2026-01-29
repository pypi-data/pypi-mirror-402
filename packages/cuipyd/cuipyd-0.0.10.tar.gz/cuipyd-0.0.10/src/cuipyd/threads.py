import threading
import time


class StoppableLoopThread(threading.Thread):

    def __init__(self, *args, **kwargs):
        super(StoppableLoopThread, self).__init__(*args, **kwargs)
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()

    def pause(self):
        self._pause_event.set()

    def unpause(self):
        self._pause_event.clear()

    def is_paused(self):
        return self._pause_event.is_set()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    def run(self):
        while True:
            if self.stopped():
                return
            if self._pause_event.is_set():
                time.sleep(0.1)
            else:
                self._target()
