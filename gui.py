from typing import Callable, Optional
from pathlib import Path
import tkinter as tk
from tkinter import filedialog as tk_fd
from tkinter import messagebox as tk_mb
from crypt import Crypt
from command import CommandProcessor
from response import Response, Severity

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
        # items
        self.item_mapping = {}
        self.item_listbox = None  # listbox
        # self.password.trace('w', self.dump_trace)
        self.cp = CommandProcessor(self.confirm_dialog, self.get_encryption_key)
        # info
        self.info_tag = tk.StringVar(value='')

    # def dump_trace(self, variable_name: tk.Variable, index: str, operation: str):
    #     print('trace', variable_name., operation, variable_name.get(), index)

    def get_encryption_key(self) -> Crypt | None:
        p = self.password.get()
        key = Crypt(p) if p else None
        self.password.set('')
        del p
        return key

    def select_files(self, title: str, file_type: tuple):
        f_types = (file_type, ('All files', '*.*'))
        name = tk_fd.askopenfilename(title=title, initialdir=self.directory, filetypes=f_types)
        self.file_name.set(name)

    @staticmethod
    def confirm_dialog(text: str):
        """
        :param text: message text
        :return: True if Yes, False if No.
        """
        return tk_mb.askyesno('Confirmation', text + '\n\n' + 'Do you want to proceed?')

    @staticmethod
    def message_dialog(r: Response):
        tk_mb.showinfo(str(r.severity), str(r.value))

    def file_dialog(self, title: str, file_type: tuple | None, ok_action: Callable, password_flag=True):
        """
        :param title: window title
        :param file_type: file types (when selecting files to open)
        :param ok_action: function to call if Ok button is selected
        :param password_flag: prompt for password?
        """
        w = tk.Toplevel()
        w.wm_title(title)

        # File name
        f = tk.Frame(master=w)
        f.pack(fill=tk.X, side=tk.TOP)
        self.file_name.set(NO_FILE_NAME)
        if file_type is None:
            tk.Label(f, text='File name').pack(fill='x', side=tk.LEFT)
            tk.Entry(f, textvariable=self.file_name).pack(fill='x', side=tk.LEFT)
        else:
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

    @staticmethod
    def format_item_list(item_list) -> list:
        return [(x[0], x[1]) for x in sorted(item_list, key=lambda x: x[1].lower())]

    @staticmethod
    def format_tag_list(tag_list) -> list:
        return [x for x in sorted(tag_list, key=lambda x: x[1].lower())]

    def update_item_list(self, pattern: Optional[str] = None, name_flag=False, tag_flag=False,
                         field_name_flag=False, field_value_flag=False, note_flag=False):
        if pattern is None:
            r = self.cp.item_list()
        else:
            r = self.cp.item_search(pattern, name_flag, tag_flag, field_name_flag, field_value_flag, note_flag)
        if r.is_ok and r.is_list:
            self.update_list_frame(self.format_item_list(r.value))
        else:
            self.message_dialog(r)

    def create_menu_callback(self):
        self.file_dialog('Create', None, self.create_action)

    def create_action(self, w: tk.Toplevel):
        print('action', self.file_name.get(), self.password.get())
        w.destroy()

    def open_menu_callback(self):
        self.file_dialog('Open', ('Database', '*.db'), self.open_action)

    def open_action(self, w: tk.Toplevel):
        w.destroy()
        print('action', self.file_name.get(), self.password.get())
        r = self.cp.database_read(self.file_name.get())
        if r.is_ok:
            self.init_info_frame()
            self.update_item_list()
        else:
            self.message_dialog(r)

    def search_callback(self):
        print('search callback', self.search_pattern.get())
        self.update_item_list(pattern=self.search_pattern.get(), name_flag=self.search_name.get(),
                              tag_flag=self.search_tag.get(), field_name_flag=self.search_field_name.get(),
                              field_value_flag=self.search_field_value.get(), note_flag=self.search_note.get())

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
        tk.Button(f, text="Clear", command=self.update_item_list).pack(fill='x', side=tk.LEFT)
        # tk.Button(f, text="Clear", command=self.clear).pack(fill='x', side=tk.LEFT)

        tk.Checkbutton(f, text="Name", variable=self.search_name).pack(fill='x', side=tk.LEFT)
        tk.Checkbutton(f, text="Tag", variable=self.search_tag).pack(fill='x', side=tk.LEFT)
        tk.Checkbutton(f, text="Field name", variable=self.search_field_name).pack(fill='x', side=tk.LEFT)
        tk.Checkbutton(f, text="Field value", variable=self.search_field_value).pack(fill='x', side=tk.LEFT)
        tk.Checkbutton(f, text="Note", variable=self.search_note).pack(fill='x', side=tk.LEFT)

        f.pack(fill=tk.X, side=tk.TOP, expand=False)  # do not expand in y

        return f

    def clear(self):
        self.info_tag.set('')
        self.update_item_list()

    def init_info_frame(self):
        top_frame = tk.Frame(master=self.info_frame, width=INFO_WIDTH)
        top_frame.pack(fill=tk.X, side=tk.TOP)
        r = self.cp.tag_table_list()
        if r.is_ok and r.is_list:
            n_row = 0
            for t_id, t_name, t_count in self.format_tag_list(r.value):
                t_name = t_name.strip()
                tk.Radiobutton(top_frame, text=f'{t_name:30s}', value=t_name, variable=self.info_tag, command=self.action,
                               tristatevalue=0, anchor=tk.W).grid(row=n_row, column=1, pady=1, sticky=tk.W)
                tk.Label(master=top_frame, text=f'{t_count:-3d}').grid(row=n_row, column=2, pady=1)
                n_row += 1
        # bottom_frame = tk.Frame(master=self.info_frame, width=INFO_WIDTH, bg='magenta')
        # bottom_frame.pack(fill=tk.BOTH, side=tk.TOP, expand=True)

    def action(self):
        print('action', self.info_tag.get())

    def item_select(self, event):
        n = self.item_listbox.curselection()[0]
        print(n, self.item_mapping[n], event)

    def update_list_frame(self, item_list: list):
        self.clear_frame(self.list_frame)

        self.item_listbox = tk.Listbox(self.list_frame, width=30, bg="yellow", selectmode=tk.SINGLE,
                                       activestyle='dotbox', fg="black")
        scrollbar = tk.Scrollbar(self.list_frame, orient=tk.VERTICAL, command=self.item_listbox.yview)
        self.item_listbox['yscrollcommand'] = scrollbar.set

        self.item_mapping = {}

        n = 0
        for i_id, i_name, in item_list:
            self.item_mapping[n] = i_id
            self.item_listbox.insert(n, f'{i_id:03d}  {i_name}')
            n += 1

        scrollbar.pack(side=tk.RIGHT, expand=True, fill=tk.Y)
        self.item_listbox.bind('<<ListboxSelect>>', self.item_select)
        self.item_listbox.pack(expand=True, fill=tk.BOTH, side=tk.LEFT)

        self.list_frame.pack(fill=tk.BOTH, side=tk.LEFT, expand=True)

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
        frame.pack()


if __name__ == '__main__':
    gui = Gui()
    gui.start_gui()
