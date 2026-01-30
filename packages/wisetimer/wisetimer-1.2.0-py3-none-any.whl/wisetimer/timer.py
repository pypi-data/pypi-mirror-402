import time as t
from typing import Optional, Dict, Union
class Timer:
    def __init__(self):
        self.progTime: Optional[float] = None
        self.timeStart: Optional[float] = None
        self.LimTimeStart: Optional[float] = None
        self.timeLim: Union[float, int, None] = None
        self._created_by: str = "😀11-year-old developer.(The AI ​​Assistant helped me find errors and explained things I didn't understand.🤖)"
    def start(self):
        if self.timeStart is not None:
            raise RuntimeError("❗The timer is already running, stop it first: Timer().stop().")
        self.timeStart = t.perf_counter()
        return "✅Timer started!"
    def lap(self):
        if self.timeStart is None:
                raise RuntimeError("❗Timer is not active. First, start the timer: Timer().start().")
        else:
            self.progTime = t.perf_counter() - self.timeStart
            return f"🚩Checkpoint at {self.progTime:.6f} sec."
    def stop(self):
        if self.timeStart is None:
                raise RuntimeError("❗Timer is not active. First, start the timer: Timer().start().")
        else:
            self.progTime = t.perf_counter() - self.timeStart
            self.timeStart = None
            return f"⏰Timer stopped, execution time: {self.progTime:.6f} sec."
    def reset(self):
            self.progTime = None
            self.timeStart = None
            self.check = []
            self.LimTimeStart = None
            self.timeLim = None
            return "✅Timer reset!"
    def status(self):
        if self.timeStart is None:
            return "▶Timer is not active."
        elif self.timeStart is not None:
            self.progTime = t.perf_counter() - self.timeStart
            return f"✔Timer running, {self.progTime:.6f} sec elapsed."
    def limit(self, lim):
        self.LimTimeStart = t.perf_counter()
        self.timeLim = lim
        print("✅Execution limit started.")
        return "✅Execution limit started."
    def limitRevise(self):
        if self.LimTimeStart is None:
            raise RuntimeError("❗Limit timer is not active. First, start the limit timer: Timer().limit(YOUR LIMIT)")
        self.passedLimitTime = t.perf_counter() - self.LimTimeStart
        if self.passedLimitTime > self.timeLim:
            raise RuntimeError(f"⛔Execution limit reached. Passed:{self.passedLimitTime:.6f}, limit:{self.timeLim:.6f}.")
        else:
            print(f"✅Execution limit not exceeded. Passed:{self.passedLimitTime:.6f}, left:{self.timeLim-self.passedLimitTime:.6f}.")
            return f"✅Execution limit not exceeded. Passed:{self.passedLimitTime:.6f}, left:{self.timeLim-self.passedLimitTime:.6f}."
    @classmethod
    def funcTimer(cls, func):
        def wrapper(*args, **kwargs):
            StartFuncTime = t.perf_counter()
            result = func(*args, **kwargs)
            FuncTime = t.perf_counter() - StartFuncTime
            print(f"🕒Function '{func.__name__}' executed in {FuncTime:.6f} sec.")
            return result
        return wrapper
    def __enter__(self):
        self.timeStart = t.perf_counter()
        return self
    def __exit__(self, exc_type,exc_val, exc_tb):
        result = self.stop()
        print(result)
        return False  
