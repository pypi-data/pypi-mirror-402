import time as t
from typing import Optional, Dict
class Benchmark():
    benchmarkValues = {}
    def __init__(self, name="_"):
        self.progTime: Optional[float] = None
        self.timeStart: Optional[float] = None
        self.name: str = name
        self.maxVal: Optional[float] = None
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
            print("📊Plotting...")
            print("-"*100 + "fast-")
            self.maxVal = Benchmark.benchmarkValues[slowestBenchmark]
            if self.maxVal is None:
                print("Plotting a graph is impossible: the maximum value is ZERO.")
            for key, value in Benchmark.benchmarkValues.items():
                percentInt = int((1 - value / self.maxVal) * 100)
                percent = (1 - value / self.maxVal) * 100
                if percentInt == 0:
                    print(f"{key} : | {percent}%\n")
                else:
                    print(f"{key} : " + "█"*percentInt + f" {percent}%\n")
    @classmethod
    def reset(cls):
        cls.benchmarkValues = {}
        return "✅Benchmarks reset!"
