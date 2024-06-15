import tkinter as tk
import subprocess

def run_script1():
    subprocess.run(["python", "main.py"])

def run_script2():
    subprocess.run(["python", "GUI.py"])


root = tk.Tk()
root.title("選擇馬丁格爾回撤版本")

root.geometry("400x200")

button1 = tk.Button(root, text="股數版本", command=run_script1, width=20, height=2)
button1.pack(pady=20) 

button2 = tk.Button(root, text="金額版本", command=run_script2, width=20, height=2)
button2.pack(pady=20)


root.mainloop()
