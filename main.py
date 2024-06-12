import tkinter as tk
from tkinter import filedialog, colorchooser
import threading
import queue
import json
import os

class FileViewerApp:
    def __init__(self, root):
        self.root = root
        self.file_path = None
        self.file_content = []
        self.lines_per_page = 20
        self.page_index = 0
        self.scroll_queue = queue.Queue()
        self.is_topmost = False  # 窗口是否置顶的标志

        # 默认配置
        self.config = {
            "width": 600,
            "height": 400,
            "bg_color": "black",
            "fg_color": "lime",
            "alpha": 0.5,
            "alpha_step": 0.01,
            "files": {},  # 用于记录文件路径和上次读取的行数
        }

        # 读取配置文件
        self.load_config()

        # 设置窗口的样式
        self.root.overrideredirect(True)
        self.root.geometry(f'{self.config["width"]}x{self.config["height"]}')
        self.root.attributes('-alpha', self.config["alpha"])
        self.root.config(bg=self.config["bg_color"])

        # 创建自定义标题栏
        self.title_bar = tk.Frame(self.root, bg='black', relief='raised', bd=2)
        self.title_bar.pack(fill=tk.X)
        self.title_label = tk.Label(self.title_bar, text="File Viewer", bg='black', fg='white')
        self.title_label.pack(side=tk.LEFT, padx=10)
        self.close_button = tk.Button(self.title_bar, text='X', command=self.on_close, bg='black', fg='white', bd=0)
        self.close_button.pack(side=tk.RIGHT)

        # 允许拖动窗口
        self.title_bar.bind('<Button-1>', self.start_move)
        self.title_bar.bind('<B1-Motion>', self.on_move)

        # 设置黑色背景和亮绿色字体颜色
        self.text_widget = tk.Text(root, wrap=tk.WORD, state='disabled', bg=self.config["bg_color"],
                                   fg=self.config["fg_color"])
        self.text_widget.pack(expand=True, fill=tk.BOTH)

        self.root.bind('<Control-o>', self.select_file)
        self.root.bind('<Control-Up>', self.increase_transparency)
        self.root.bind('<Control-Down>', self.decrease_transparency)
        self.root.bind('<Control-b>', self.change_bg_color)
        self.root.bind('<Control-f>', self.change_fg_color)
        self.root.bind('<Control-h>', self.toggle_help)
        self.root.bind('<Control-t>', self.toggle_topmost)
        #self.root.bind('<Control-plus>', self.increase_size)
        #self.root.bind('<Control-minus>', self.decrease_size)
        self.root.bind('<Control-Shift-Up>', self.increase_alpha_step)
        self.root.bind('<Control-Shift-Down>', self.decrease_alpha_step)
        self.text_widget.bind('<KeyPress-space>', self.next_page)
        self.text_widget.bind('<KeyPress-r>', self.previous_page)

        self.root.after(200, self.process_queue)

        # 显示帮助信息
        self.help_text = (
            "快捷键说明：\n"
            "Ctrl+O: 选择文件\n"
            "Ctrl+Up: 增加透明度\n"
            "Ctrl+Down: 减少透明度\n"
            "Ctrl+B: 修改背景颜色\n"
            "Ctrl+F: 修改字体颜色\n"
            "Ctrl+H: 显示/隐藏帮助信息\n"
            "Ctrl+T: 切换窗口置顶\n"
            #"Ctrl+Plus: 增大窗口\n"
            #"Ctrl+Minus: 减小窗口\n"
            "Ctrl+Shift+Up: 增加透明度修改粒度\n"
            "Ctrl+Shift+Down: 减少透明度修改粒度\n"
            "空格: 翻页\n"
            "R: 上一页\n"
        )
        self.show_help()

    def load_config(self):
        try:
            with open("config.json", "r") as config_file:
                self.config.update(json.load(config_file))
        except FileNotFoundError:
            pass

    def save_config(self):
        with open("config.json", "w") as config_file:
            json.dump(self.config, config_file)

    def show_help(self):
        self.text_widget.config(state='normal')
        self.text_widget.delete(1.0, tk.END)
        self.text_widget.insert(tk.END, self.help_text)
        self.text_widget.config(state='disabled')

    def select_file(self, event=None):
        self.file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if self.file_path:
            threading.Thread(target=self.load_file).start()

    def load_file(self):
        self.page_index = self.config["files"].get(self.file_path, 0) // self.lines_per_page
        with open(self.file_path, 'r', encoding='utf-8') as file:
            self.file_content = file.readlines()
        self.scroll_queue.put("update_page")

    def update_page(self):
        self.text_widget.config(state='normal')
        self.text_widget.delete(1.0, tk.END)
        start = self.page_index * self.lines_per_page
        end = start + self.lines_per_page
        for line in self.file_content[start:end]:
            self.text_widget.insert(tk.END, line)
        self.text_widget.config(state='disabled')

    def next_page(self, event=None):
        total_lines = len(self.file_content)
        total_pages = (total_lines + self.lines_per_page - 1) // self.lines_per_page  # 计算总页数
        if self.page_index < total_pages - 1:
            self.page_index += 1
            self.scroll_queue.put("update_page")

    def previous_page(self, event=None):
        if self.page_index > 0:
            self.page_index -= 1
            self.scroll_queue.put("update_page")

    def process_queue(self):
        try:
            msg = self.scroll_queue.get_nowait()
            if msg == "update_page":
                self.update_page()
        except queue.Empty:
            pass
        self.root.after(200, self.process_queue)

    def increase_transparency(self, event=None):
        current_alpha = self.root.attributes('-alpha')
        new_alpha = min(current_alpha + self.config["alpha_step"], 1.0)  # 增加透明度，但不超过 1.0
        self.root.attributes('-alpha', new_alpha)
        self.config["alpha"] = new_alpha
        self.save_config()

    def decrease_transparency(self, event=None):
        current_alpha = self.root.attributes('-alpha')
        new_alpha = max(current_alpha - self.config["alpha_step"], 0.01)  # 减少透明度，但不低于 0.01
        self.root.attributes('-alpha', new_alpha)
        self.config["alpha"] = new_alpha
        self.save_config()

    def change_bg_color(self, event=None):
        color = colorchooser.askcolor(title="选择背景颜色")[1]
        if color:
            self.text_widget.config(bg=color)
            self.config["bg_color"] = color
            self.save_config()

    def change_fg_color(self, event=None):
        color = colorchooser.askcolor(title="选择字体颜色")[1]
        if color:
            self.text_widget.config(fg=color)
            self.config["fg_color"] = color
            self.save_config()

    def toggle_help(self, event=None):
        if self.text_widget.get(1.0, tk.END).strip() == self.help_text.strip():
            self.text_widget.config(state='normal')
            self.text_widget.delete(1.0, tk.END)
            self.text_widget.config(state='disabled')
        else:
            self.show_help()

    def toggle_topmost(self, event=None):
        self.is_topmost = not self.is_topmost
        self.root.attributes('-topmost', self.is_topmost)

    def increase_size(self, event=None):
        current_width = self.root.winfo_width()
        current_height = self.root.winfo_height()
        new_width = current_width + 20
        new_height = current_height + 20
        self.root.geometry(f'{new_width}x{new_height}')
        self.config["width"] = new_width
        self.config["height"] = new_height
        self.save_config()
        self.update_lines_per_page()

    def decrease_size(self, event=None):
        current_width = self.root.winfo_width()
        current_height = self.root.winfo_height()
        new_width = max(current_width - 20, 100)
        new_height = max(current_height - 20, 100)
        self.root.geometry(f'{new_width}x{new_height}')
        self.config["width"] = new_width
        self.config["height"] = new_height
        self.save_config()
        self.update_lines_per_page()

    def increase_alpha_step(self, event=None):
        self.config["alpha_step"] = min(self.config["alpha_step"] + 0.01, 1.0)
        self.save_config()

    def decrease_alpha_step(self, event=None):
        self.config["alpha_step"] = max(self.config["alpha_step"] - 0.01, 0.01)
        self.save_config()

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def on_move(self, event):
        x = event.x_root - self.x
        y = event.y_root - self.y
        self.root.geometry(f"+{x}+{y}")

    def save_last_line(self):
        if self.file_path:
            self.config["files"][self.file_path] = self.page_index * self.lines_per_page
            self.save_config()

    def on_close(self):
        self.save_last_line()
        self.root.destroy()

    def update_lines_per_page(self):
        self.text_widget.config(state='normal')
        lines = self.text_widget.index('end-1c').split('.')[0]
        self.lines_per_page = int(lines) - 1
        self.text_widget.config(state='disabled')
        self.scroll_queue.put("update_page")

if __name__ == "__main__":
    root = tk.Tk()
    app = FileViewerApp(root)
    root.mainloop()
