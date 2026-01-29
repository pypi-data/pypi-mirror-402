import time as t
import random as rand
import ast
class Timer:
    def __init__(self):
        self.progTime = None
        self.timeStart = None
        self.check = []
        self.LimTimeStart = None
        self.timeLim = None
        self._created_by = "😀11-year-old developer.(The AI ​​Assistant helped me find errors and explained things I didn't understand.🤖)"
    def done(self, do=None):
        if self.timeStart == None and do == None or self.timeStart == None and do == "start":
            self.timeStart = t.perf_counter()
            return "✅Timer started!"
        if self.timeStart != None and do == "start":
            raise RuntimeError("❗The timer is already running, stop it first: Timer().done(), Timer().done('finish'), Timer().stop(), Timer().end(), Timer().finish().")
        elif self.timeStart != None and do == None or self.timeStart != None and do == "finish" or self.timeStart != None and do == "stop" or self.timeStart != None and do == "end":
            if self.timeStart == None:
                raise RuntimeError("❗Timer is not active. First, start the timer: Timer().done() or Timer().done('start') or Timer().start().")
            else:
                self.progTime = t.perf_counter() - self.timeStart
                self.timeStart = None
                return f"⏰Timer stopped, execution time: {self.progTime:.6f} sec."
        elif do == "reset":
            return self.reset()
        elif do == "lap":
            return self.lap()
        elif do == "status":
            return self.status()
        elif do != None and do != "start" and do != "finish" and do != "reset" and do != "lap" and do != "status":
            raise ValueError(f"🚫Unknown command {do}, use: start, finish, end, stop, lap, reset, status.")
    def start(self):
        if self.timeStart != None:
            raise RuntimeError("❗The timer is already running, stop it first: Timer().done(), Timer().done('finish'), Timer().stop(), Timer.end(), Timer().finish().")
        self.timeStart = t.perf_counter()
        return "✅Timer started!"
    def finish(self):
        if self.timeStart == None:
                raise RuntimeError("❗Timer is not active. First, start the timer: Timer().done() or Timer().done('start') or Timer().start().")
        else:
            self.progTime = t.perf_counter() - self.timeStart
            self.timeStart = None
            return f"⏰Timer stopped, execution time: {self.progTime:.6f} sec."
    def lap(self):
        if self.timeStart == None:
                raise RuntimeError("❗Timer is not active. First, start the timer: Timer().done() or Timer().done('start') or Timer().start().")
        else:
            self.progTime = t.perf_counter() - self.timeStart
            return f"🚩Checkpoint at {self.progTime:.6f} sec."
    def stop(self):
        return self.finish()
    def end(self):
        return self.finish()
    def reset(self):
            self.progTime = None
            self.timeStart = None
            self.check = []
            self.LimTimeStart = None
            self.timeLim = None
            return "✅Timer reset!"
    def status(self):
        if self.timeStart == None:
            return "▶Timer is not active."
        elif self.timeStart != None:
            self.progTime = t.perf_counter() - self.timeStart
            return f"✔️Timer running, {self.progTime:.6f} sec elapsed."
    def limit(self, lim):
        self.LimTimeStart = t.perf_counter()
        self.timeLim = lim
        print("✅Execution limit started.")
        return "✅Execution limit started."
    def limitRevise(self):
        if self.LimTimeStart == None:
            raise RuntimeError("❗Limit timer is not active. First, start the limit timer: Timer().limit(YourLimit)")
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
class Benchmark():
    benchmarkValues = {}
    def __init__(self, name="_"):
        self.progTime = None
        self.timeStart = None
        self.name = name
    def __enter__(self):
        self.timeStart = t.perf_counter()
        return self
    def __exit__(self, exc_type,exc_val, exc_tb):
        self.progTime = t.perf_counter() - self.timeStart
        self.timeStart = None
        Benchmark.benchmarkValues[self.name] = self.progTime
        print(f"⏰Benchmark '{self.name}' completed in {self.progTime:.6f} sec.")
        return False
    def compar(self):
        if len(Benchmark.benchmarkValues) < 2:
            raise ValueError("⚠Insufficient data for comparison: minimum number of benchmarks 2.")
        else:
            slowestBenchmark = max(Benchmark.benchmarkValues, key=Benchmark.benchmarkValues.get)
            fastestBenchmark = min(Benchmark.benchmarkValues, key=Benchmark.benchmarkValues.get)
            print(f"⏰Benchmarks: {Benchmark.benchmarkValues}.")
            print(f"🐢The slowest benchmark is: {slowestBenchmark}.")
            print(f"🐎The fastest benchmark is: {fastestBenchmark}.")
    @classmethod
    def reset(cls):
        cls.benchmarkValues = {}
        return "✅Benchmarks reset!"
class Analyze():
    def __init__(self):
        self.timeStart = None
        self.check = []
        self.numElif = 0
        self.numChildIf = 0
    def checkpoint(self):
        if self.timeStart == None:
            raise RuntimeError("❗Timer is not active. First, start the timer: Timer().done() or Timer().done('start') or Timer().start().")
        else:
            current_time = t.perf_counter() - self.timeStart  
            self.check.append(current_time)
            return f"📌Checkpoint recorded at {current_time:.6f} sec."
    def getAdvice(self):
        if len(self.check) < 4:
            raise ValueError("⚠Insufficient data for analysis: minimum number of checkpoints 4.")
        else:
            self.intervals = []
            for number in range(1, len(self.check)):
                self.intervals.append(self.check[number] - self.check[number-1])
            self.minValue = min(self.intervals)
            self.maxValue = max(self.intervals)
            self.averageValue = sum(self.intervals) / len(self.intervals)
            print(f"🏴Checkpoint's intervals: {self.intervals}.\n🐢The slowest part: {self.intervals.index(max(self.intervals))+1} checkpoint.\n🐎Fastest  part: {self.intervals.index(min(self.intervals))+1} checkpoint.")
            if self.maxValue > 1.0:
                print(f"Pattern: 🐢very long operations.")
            elif self.minValue > 0.000001 and self.maxValue / self.minValue > 8:
                print(f"Pattern: 🔁strong time jumps.")
            elif self.averageValue < 0.01:
                print(f"Pattern: 🏃lots of quick reps.")
            else:
                self.normalAdvice = ["💪The code works stably!", "🎯Keep up the good work!", "✅Runtime looks ok!"]
                print(rand.choice(self.normalAdvice))
    def code(self, yourCode):
        if yourCode == None:
            raise TypeError("⚠️The code for analysis is not found. First enter the code: Analyze.code('yourCode').")
        else:
            codeTree = ast.parse(yourCode)
            print("✅Start code analysis.")
            for node in ast.walk(codeTree):
                if isinstance(node, (ast.For, ast.While)):
                    for child in ast.walk(node):
                        if isinstance(child, ast.Assign):
                            print(f"🧠Perhaps creating objects in a loop on line {child.lineno}.\n💡Advice: 🫸Avoid creating objects in a loop.\n")
                        if isinstance(child, ast.Call):
                            if isinstance(child.func, ast.Attribute) and child.func.attr == "append":
                                print(f"🧠Perhaps method append in loop on line {child.lineno}.\n💡Advice: 🔁Replace regular loops with list comprehension, it will be faster.\n")
                        if isinstance(child, ast.BinOp):
                            print(f"🧠Perhaps calculation in a loop on line {child.lineno}.\n💡Advice: 📤Try to move the calculations outside the loop.\n")
                        if isinstance(child, ast.Name) and child.id == "self" or isinstance(child, ast.Global):
                            print(f"🧠Perhaps self/global in a loop on line {child.lineno}.\n💡Advice: 🏠Use local variables more often, they are faster.\n")
                        if isinstance(child, ast.AugAssign) and isinstance(child.op, ast.Add):
                            print(f"🧠Perhaps adding strings(+=) in a loop on line {child.lineno}.\n💡Advice: 🔗Use join instead of += in loop.\n")
                if isinstance(node, ast.While):
                    for child in ast.walk(node):
                        if isinstance(child, ast.Call):
                            if isinstance(child.func, ast.Name) and child.func.id == "range":
                                for arguments in child.args:  
                                    print(f"🧠Perhaps while loop with comparison on line {child.lineno}.\n💡Advice: 🔃Try replacing the while loop with for loop.\n")
                if isinstance(node, ast.If):
                    numChildIf = 0
                    for child in ast.iter_child_nodes(node):
                        if isinstance(child, ast.If) and child is not node:
                            numChildIf += 1
                            if numChildIf > 1:
                                print(f"🧠Perhaps nested conditions(if) on line {child.lineno}.\n💡Advice: 🗑Avoid nesting and chaining.\n")
                                numChildIf = 0
                if isinstance(node, ast.If):
                    for nextIf in node.orelse:
                         if isinstance(nextIf, ast.If):
                            self.numElif += 1
                            for nextNextIf in nextIf.orelse:
                                if isinstance(nextNextIf, ast.If):
                                    self.numElif += 1
                                    if self.numElif >= 2:
                                        print(f"🧠Perhaps elif on line {nextNextIf.lineno}.\n💡Advice: 🆕Try use match-case instead of if-elif.\n")
                                        self.numElif = 0
                if isinstance(node, ast.FunctionDef):
                    for child in ast.iter_child_nodes(node):
                        if isinstance(child, (ast.Import, ast.ImportFrom)):
                            print(f"🧠Perhaps import in function on line {child.lineno}.\n💡Advice: 📦Move the import from the function to the top of the file.\n")
