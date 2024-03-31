from typing import Callable
from pathlib import Path
import tkinter as tk
from tkinter import filedialog as fd

GUI_WIDTH = 900
GUI_HEIGHT = 700
SEARCH_WIDTH = GUI_WIDTH
SEARCH_HEIGHT = 40
BOTTOM_WIDTH = GUI_WIDTH
BOTTOM_HEIGHT = GUI_HEIGHT - SEARCH_HEIGHT
INFO_WIDTH = int(GUI_WIDTH * 20 / 100)
INFO_HEIGHT = BOTTOM_HEIGHT
LIST_WIDTH = int(GUI_WIDTH * 30 / 100)
LIST_HEIGHT = BOTTOM_HEIGHT
EDIT_WIDTH = GUI_WIDTH - INFO_WIDTH - LIST_WIDTH
EDIT_HEIGHT = BOTTOM_HEIGHT

SEARCH_BG_COLOR = 'green'

NO_FILE_NAME = 'None'


class Gui:

    def __init__(self):
        self.root = tk.Tk()
        self.search_frame = None
        self.info_frame = None
        self.list_frame = None
        self.item_frame = None
        # search
        self.search_pattern = tk.StringVar(value='')
        self.search_name = tk.BooleanVar(value=True)
        self.search_tag = tk.BooleanVar(value=False)
        self.search_field_name = tk.BooleanVar(value=False)
        self.search_field_value = tk.BooleanVar(value=False)
        self.search_note = tk.BooleanVar(value=False)
        # file
        self.directory = Path.home()
        self.file_name = tk.StringVar(value=NO_FILE_NAME)
        self.password = tk.StringVar(value='')
        self.password.trace('w', self.dump_trace)

    def dump_trace(self, variable_name: str, index: str, operation: str):
        print('trace',  variable_name, operation, self.password.get(), index)

    def select_files(self, title: str, file_type: tuple):
        f_types = (file_type, ('All files', '*.*'))
        name = fd.askopenfilename(title=title, initialdir=self.directory, filetypes=f_types)
        self.file_name.set(name)

    def file_dialog(self, title: str, file_type: tuple | None, ok_action: Callable, password_flag=True):
        w = tk.Toplevel()
        w.wm_title(title)

        # File name
        f = tk.Frame(master=w)
        f.pack(fill=tk.X, side=tk.TOP)
        if file_type is None:  # create
            tk.Label(f, text='File name').pack(fill='x', side=tk.LEFT)
            tk.Entry(f, textvariable=self.file_name).pack(fill='x', side=tk.LEFT)
        else:  # open
            tk.Button(f, text="Select file", command=lambda: self.select_files(title, file_type)).pack(side=tk.LEFT)
            tk.Label(f, textvariable=self.file_name).pack(side=tk.LEFT)

        # Password
        if password_flag:
            self.password.set('')
            p = tk.Frame(master=w)
            p.pack(fill=tk.X, side=tk.TOP)
            tk.Label(p, text='Password').pack(fill='x', side=tk.LEFT)
            tk.Entry(p, textvariable=self.password).pack(fill='x', side=tk.LEFT)

        # Buttons
        b = tk.Frame(master=w)
        b.pack(fill=tk.X, side=tk.BOTTOM)
        tk.Button(b, text="Ok", command=lambda: ok_action(w)).pack(fill='x', padx=10, side=tk.LEFT)
        tk.Button(b, text="Cancel", command=w.destroy).pack(fill='x', padx=10, side=tk.RIGHT)

    def create_menu_callback(self):
        self.file_dialog('Create', None, self.create_action)

    def create_action(self, w: tk.Toplevel):
        print('action', self.file_name.get(), self.password.get())
        w.destroy()

    def open_action(self, w: tk.Toplevel):
        print('action', self.file_name.get(), self.password.get())
        w.destroy()

    def open_menu_callback(self):
        self.file_dialog('Open', ('Database', '*.db'), self.open_action)

    def search_callback(self):
        print('search callback', self.search_pattern.get())

    def init_menu_bar(self, root: tk.Tk):
        menu_bar = tk.Menu(root)
        root.config(menu=menu_bar)

        file_menu = tk.Menu(menu_bar)
        tag_menu = tk.Menu(menu_bar)
        field_menu = tk.Menu(menu_bar)

        # add menu items to the File menu
        file_menu.add_command(label='Create...', command=self.create_menu_callback)
        file_menu.add_command(label='Open...', command=self.open_menu_callback)
        file_menu.add_command(label='Save')
        file_menu.add_command(label='Save as...')
        file_menu.add_command(label='Import...')
        file_menu.add_command(label='Export...')
        file_menu.add_command(label='Exit')

        tag_menu.add_command(label='Add')
        tag_menu.add_command(label='Rename')
        tag_menu.add_command(label='Delete')
        tag_menu.add_separator()
        tag_menu.add_command(label='Import')
        tag_menu.add_command(label='Export')

        field_menu.add_command(label='Add')
        field_menu.add_command(label='Rename')
        field_menu.add_command(label='Delete')
        field_menu.add_separator()
        field_menu.add_command(label='Import')
        field_menu.add_command(label='Export')

        menu_bar.add_cascade(label="File", menu=file_menu)
        menu_bar.add_cascade(label="Tag", menu=tag_menu)
        menu_bar.add_cascade(label="Field", menu=file_menu)

    def init_search_frame(self, root: tk.Tk, width: int, height: int, bg_color: str) -> tk.Frame:
        f = tk.Frame(master=root, width=width, height=height, bg=bg_color)

        tk.Entry(f, textvariable=self.search_pattern).pack(fill='x', side=tk.LEFT, expand=True)

        tk.Button(f, text="Search", command=self.search_callback).pack(fill='x', side=tk.LEFT)

        tk.Checkbutton(f, text="Name", var=self.search_name).pack(fill='x', side=tk.LEFT)
        tk.Checkbutton(f, text="Tag", var=self.search_tag).pack(fill='x', side=tk.LEFT)
        tk.Checkbutton(f, text="Field name", var=self.search_field_name).pack(fill='x', side=tk.LEFT)
        tk.Checkbutton(f, text="Field value", var=self.search_field_value).pack(fill='x', side=tk.LEFT)
        tk.Checkbutton(f, text="Note", var=self.search_note).pack(fill='x', side=tk.LEFT)

        f.pack(fill=tk.X, side=tk.TOP, expand=False)  # do not expand in y

        return f

    def start_gui(self):
        self.root.title('Mypass')

        self.init_menu_bar(self.root)

        self.search_frame = self.init_search_frame(self.root, SEARCH_WIDTH, SEARCH_HEIGHT, SEARCH_BG_COLOR)

        bottom_frame = tk.Frame(master=self.root, width=BOTTOM_WIDTH, height=BOTTOM_HEIGHT)
        bottom_frame.pack(fill=tk.BOTH, side=tk.TOP, expand=True)

        self.info_frame = tk.Frame(master=bottom_frame, width=INFO_WIDTH, height=INFO_HEIGHT, bg='red')
        self.info_frame.pack(fill=tk.BOTH, side=tk.LEFT, expand=True)

        self.list_frame = tk.Frame(master=bottom_frame, width=LIST_WIDTH, bg='yellow')
        self.list_frame.pack(fill=tk.BOTH, side=tk.LEFT, expand=True)

        self.item_frame = tk.Frame(master=bottom_frame, width=EDIT_WIDTH, bg='blue')
        self.item_frame.pack(fill=tk.BOTH, side=tk.LEFT, expand=True)

        self.root.mainloop()

    @staticmethod
    def clear_frame(frame: tk.Frame):
        for widget in frame.winfo_children():
            widget.destroy()
        frame.pack_forget()


if __name__ == '__main__':
    gui = Gui()
    gui.start_gui()
