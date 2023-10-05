import tkinter as tk
from tkinter import filedialog, Text, messagebox, simpledialog
import json
import os

class JSONEditor(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("IFN-Transprt Settings")
        self.geometry("600x400")
        self.fileName = 'settings.json'
        self.iconbitmap('ifn-transport.ico')  # Set the icon

        # Text widget for editing
        self.text_widget = Text(self, wrap='word')
        self.text_widget.pack(expand=1, fill='both')

        # Menu
        self.menu = tk.Menu(self, tearoff=0)
        self.config(menu=self.menu)

        file_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open", command=self.load_json)
        file_menu.add_command(label="Save", command=self.save_default)
        file_menu.add_command(label="Save As...", command=self.save_json)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)

        edit_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Reformat", command=self.reformat_json)
        edit_menu.add_command(label="Search", command=self.search_text)
        edit_menu.add_command(label="Search Next", command=self.search_next)

        # Load the default file upon start
        if os.path.exists(self.fileName):
            self.load_default()

    def load_default(self):
        with open(self.fileName, 'r') as file:
            content = file.read()
            self.text_widget.delete(1.0, tk.END)
            self.text_widget.insert(tk.END, content)

    def save_default(self):
        with open(self.fileName, 'w') as file:
            content = self.text_widget.get(1.0, tk.END)
            file.write(content)

    def load_json(self):
        file_path = filedialog.askopenfilename(initialfile=self.fileName, filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if file_path:
            with open(file_path, 'r') as file:
                content = file.read()
                self.text_widget.delete(1.0, tk.END)
                self.text_widget.insert(tk.END, content)

    def save_json(self):
        file_path = filedialog.asksaveasfilename(initialfile=self.fileName, defaultextension=".json", filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if file_path:
            with open(file_path, 'w') as file:
                content = self.text_widget.get(1.0, tk.END)
                file.write(content)

    def reformat_json(self):
        try:
            content = self.text_widget.get(1.0, tk.END)
            data = json.loads(content)
            formatted_json = json.dumps(data, indent=4)
            self.text_widget.delete(1.0, tk.END)
            self.text_widget.insert(tk.END, formatted_json)
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Invalid JSON format!")

    def search_text(self):
        self.search_word = simpledialog.askstring("Search", "Enter word to search:")
        if self.search_word:
            self.text_widget.tag_remove("search", 1.0, tk.END)
            self.search_next()

    def search_next(self):
        if not hasattr(self, 'search_word'):
            messagebox.showerror("Error", "Please use 'Search' before 'Search Next'.")
            return

        start = self.text_widget.search(self.search_word, tk.INSERT, stopindex=tk.END, nocase=True)
        if start:
            end = f"{start}+{len(self.search_word)}c"
            self.text_widget.tag_remove("search", 1.0, tk.END)
            self.text_widget.tag_add("search", start, end)
            self.text_widget.tag_configure("search", background="yellow")
            self.text_widget.mark_set(tk.INSERT, end)
            self.text_widget.see(tk.INSERT)
        else:
            messagebox.showinfo("Search", "No more matches found.")

    def on_closing(self):
        self.destroy()

if __name__ == "__main__":
    app = JSONEditor()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
