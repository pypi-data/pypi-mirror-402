# /// script
# requires-python = ">=3.12"
# dependencies = [
# ]
# ///

import tkinter as tk
from tkinter import messagebox

class TodoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple Todo List")
        
        self.tasks = []
        
        # UI Elements
        self.entry = tk.Entry(root, width=40)
        self.entry.pack(pady=10)
        
        self.add_button = tk.Button(root, text="Add Task", command=self.add_task)
        self.add_button.pack()
        
        self.listbox = tk.Listbox(root, width=40, height=10)
        self.listbox.pack(pady=10)
        
        self.delete_button = tk.Button(root, text="Delete Task", command=self.delete_task)
        self.delete_button.pack()
        
    def add_task(self):
        task = self.entry.get()
        if task:
            self.tasks.append(task)
            self.listbox.insert(tk.END, task)
            self.entry.delete(0, tk.END)
        else:
            messagebox.showwarning("Warning", "You must enter a task.")

    def delete_task(self):
        try:
            index = self.listbox.curselection()[0]
            self.listbox.delete(index)
            self.tasks.pop(index)
        except IndexError:
            messagebox.showwarning("Warning", "You must select a task to delete.")

if __name__ == "__main__":
    root = tk.Tk()
    app = TodoApp(root)
    root.mainloop()
