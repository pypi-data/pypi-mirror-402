import time as t
import random as rand
import ast
from typing import Optional, Dict
class Analyze():
    def __init__(self):
        self.timeStart: Optional[float] = None
        self.check: Dict[str, float] = {}
        self.startCheckpoint: Optional[str] = None
        self.AiKey: Optional[str] = None
        self.ans: Optional[str] = None
        numChildIf: int = 0
        numElif: int = 0
    def checkpoint(self, name):
        if name is None:
            raise ValueError("⚠The checkpoint name is not specified. Specify the checkpoint name: Analyze().checkpoint('NAME').")
        if self.timeStart is None:
            self.timeStart = t.perf_counter()
            self.startCheckpoint = name
            return "✅Checkpoint started!"
        else:
            current_time = t.perf_counter() - self.timeStart  
            self.check[name] = current_time
            self.timeStart = t.perf_counter()
            return f"📌Checkpoint recorded at {current_time:.6f} sec."
    def getAdvice(self):
        if len(self.check) < 4:
            raise ValueError("⚠Insufficient data for analysis: minimum number of checkpoints 4.")
        else:
            self.minValue = min(self.check.values())
            self.maxValue = max(self.check.values())
            self.averageValue = sum(self.check.values()) / len(self.check)
            print(f"🏴Checkpoint's intervals: {self.check}.\n🐢The slowest part: {max(self.check, key=self.check.get)} checkpoint.\n🐎Fastest  part: {min(self.check, key=self.check.get)} checkpoint.")
            print("📊Plotting...")
            print("-"*100 + "fast-")
            print(f"{self.startCheckpoint} : | Start(None)% \n")
            if self.maxValue is None:
                print("Plotting a graph is impossible: the maximum value is ZERO.")
            else:
                for key, value in self.check.items():
                    percentInt = int((1 - value / self.maxValue) * 100)
                    percent = (1 - value / self.maxValue) * 100
                    if percentInt == 0:
                        print(f"{key} : | {percent}%\n")
                    else:
                        print(f"{key} : " + "█"*percentInt + f" {percent}%\n")
            if self.maxValue > 1.0:
                print(f"Pattern: 🐢very long operations.")
            elif self.minValue > 0.000001 and self.maxValue / self.minValue > 8:
                print(f"Pattern: 🔁strong time jumps.")
            elif self.averageValue < 0.01:
                print(f"Pattern: 🏃lots of quick reps.")
            else:
                self.normalAdvice = ["💪The code works stably!", "🎯Keep up the good work!", "✅Runtime looks ok!"]
                print(rand.choice(self.normalAdvice))
    def AiCode(self, code):
        if code is None:
            raise ValueError("Code for AI analysis not found. First provide the code for analysis: Analyze().code('YOUR CODE').")
        from google import genai
        import keyring
        import getpass
        self.AiKey = keyring.get_password("wisetimer", "wisetimer_for_google_gemini")
        if self.AiKey == None:
            print("👋🏻Hello, I am a master of installing and configuring the Google Gemeni AI!")
            print("To use Google Gemeni, you will need to purchase a key.")
            print("There's nothing to worry about, and here's why:\n - The key is completely FREE! \n - It only takes 3 minutes to receive. \nThis is necessary for your code to be analyzed by Google's powerful and modern AI model!")
            print("Instructions for obtaining a key in 3 minutes:\n 1) I will open (or you will open) the website https://ai.google.dev/gemini-api/docs/quickstart?hl=ru#python \n 2) Click on the button to create a Gemini API key and copy it")
            self.ans = input("Open the website https://ai.google.dev/gemini-api/docs/quickstart?hl=ru#python ?(y/n):")
            if self.ans == "y":
                import webbrowser as web
                print("I open the website...")
                web.open("https://ai.google.dev/gemini-api/docs/quickstart?hl=ru#python")
                print("Click on the Create API Key button and copy it")
            else:
                print("OK, open the website yourself https://ai.google.dev/gemini-api/docs/quickstart?hl=ru#python, click on the Create API Key button and copy it.")
            self.AiKey = getpass.getpass("Enter Google Gemeni AI key (characters will be hidden):").strip()
            keyring.set_password("wisetimer", "wisetimer_for_google_gemini", self.AiKey)
            print("Google Gemini AI key saved.")
        else:
            try:
                client = genai.Client(self.AiKey)
                print("🧠Google Gemeni AI generates a response...")
                respon = client.models.generate_content(model="gemini-3-pro", contents=f"You are expert in Python code optimization. Analyze this code: {code} \nfor optimization errors, suggest a faster, more productive version of the code")
                print(respon.text)
            except Exception as e:
                print(f"Google Gemeni API Error: {e}")
    def AstCode(self, yourCode):
        numElif = 0
        if yourCode is None:
            raise TypeError("⚠️The code for analysis is not found. First enter the code: Analyze.code('YOUR CODE').")
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
                            numElif += 1
                            for nextNextIf in nextIf.orelse:
                                if isinstance(nextNextIf, ast.If):
                                    numElif += 1
                                    if numElif >= 2:
                                        print(f"🧠Perhaps elif on line {nextNextIf.lineno}.\n💡Advice: 🆕Try use match-case instead of if-elif.\n")
                                        numElif = 0
                if isinstance(node, ast.FunctionDef):
                    for child in ast.iter_child_nodes(node):
                        if isinstance(child, (ast.Import, ast.ImportFrom)):
                            print(f"🧠Perhaps import in function on line {child.lineno}.\n💡Advice: 📦Move the import from the function to the top of the file.\n")
    def delAiKey(self):
        try:
            keyring.delete_password("wisetimer", "wisetimer_for_google_gemini")
            print("Google Gemini AI key deleted successfully.")
        except keyring.errors.PasswordDeleteError:
            print("API key not found. Nothing to delete.")
    

