from database import Database
import filedialpy
import os
import tkinter as tk
from tkinter import ttk
import sqlite3

class GUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("log searcher")
        self.geometry("800x600")

        # Container frame that will hold all screens
        container = tk.Frame(self)
        container.pack(fill="both", expand=True)

        # Dictionary to store all screens
        self.frames = {}

        # Create all screens
        for F in (HomeScreen, SettingsScreen, DataScreen):
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # Configure grid weights
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # Show initial screen
        self.show_frame(DataScreen)

    def show_frame(self, frame_class):
        """Switch to a different screen"""
        frame = self.frames[frame_class]
        frame.tkraise()

        # Call the on_show method if it exists (for initialization)
        if hasattr(frame, 'on_show'):
            frame.on_show()

    def open_log_file(self):
        self.database = Database()

        self.log_file_dir = filedialpy.openFile()
        self.frames[DataScreen].status.set(f"Opening {self.log_file_dir}")
        self.database.load_log_file(self.log_file_dir)
        log = self.database.query_entire_database()
        if log:
            self.frames[DataScreen].create_tree_view(log)
            self.frames[DataScreen].status.set(f"Opened {self.log_file_dir}")
        else:
            self.frames[DataScreen].status.set("No database loaded")

    def open_default_log_file(self):
        self.database = Database()
        self.log_file_dir = "D:\semantic DNS search\log files\dns.log"
        self.frames[DataScreen].status.set(f"Opening {self.log_file_dir}")
        self.database.load_log_file(self.log_file_dir)
        log = self.database.query_entire_database()
        if log:
            self.frames[DataScreen].create_tree_view(log)
            self.frames[DataScreen].status.set(f"Opened {self.log_file_dir}")
        else:
            self.frames[DataScreen].status.set("No database loaded")

    def white_space_delimiter(self):
        self.database.split(" ")
        # file_name = os.path.basename(self.log_file_dir).rsplit('.')[0]
        db_file_dir = os.path.join(os.path.split(os.path.split(self.log_file_dir)[0])[0], os.path.basename(self.log_file_dir).rsplit('.')[0] + ".db")
        # db_file_dir = self.log_file_dir.rstrip(db_file_name) + ".db"
        self.database.open_db_file(db_file_dir)
        self.frames[DataScreen].status.set(f"Opening {self.log_file_dir}")
        log = self.database.query_entire_database()
        if log:
            self.frames[DataScreen].tree_frame.destroy()
            self.frames[DataScreen].create_tree_view(log)
            self.frames[DataScreen].status.set(f"updated {self.log_file_dir}")
        else:
            self.frames[DataScreen].status.set("No database loaded")

    def delete_db(self):
        sql = 'DELETE FROM log'
        self.log_file_dir = "D:\semantic DNS search\log files\dns.log"
        if not self.database.conn:
            self.database.conn = sqlite3.connect(self.log_file_dir.rsplit('.')[0] + '.db')
        self.database.cursor = self.database.conn.cursor()
        self.database.cursor.execute(sql)
        self.database.conn.commit()
        self.database.conn.close()

class BaseScreen(tk.Frame):
    """Base class for all screens with common functionality"""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.setup_ui()

    def setup_ui(self):
        """Override this method in subclasses to setup the UI"""
        pass

    def on_show(self):
        """Called when this screen is shown"""
        pass


class StatusBar(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        self.label = tk.Label(self)
        self.label.pack(side=tk.LEFT)
        self.pack(side=tk.BOTTOM, fill=tk.X)

    def set(self, newText):
        self.label.config(text=newText)

    def clear(self):
        self.label.config(text="")

class HomeScreen(BaseScreen):
    """Main home screen"""

    def setup_ui(self):
        # Title
        title = tk.Label(self, text="Home Screen", font=("Arial", 24, "bold"))
        title.pack(pady=20)

        # Navigation buttons
        nav_frame = tk.Frame(self)
        nav_frame.pack(pady=20)

        tk.Button(nav_frame, text="Go to Settings",
                  command=lambda: self.controller.show_frame(SettingsScreen),
                  width=20, height=2).pack(pady=5)

        tk.Button(nav_frame, text="Go to Data",
                  command=lambda: self.controller.show_frame(DataScreen),
                  width=20, height=2).pack(pady=5)

        # Some interactive widgets
        content_frame = tk.Frame(self, relief="sunken", bd=2)
        content_frame.pack(pady=20, padx=20, fill="both", expand=True)

        tk.Label(content_frame, text="Welcome to the Home Screen!",
                 font=("Arial", 14)).pack(pady=10)

        # Counter example
        self.counter = 0
        self.counter_label = tk.Label(content_frame, text=f"Counter: {self.counter}",
                                      font=("Arial", 12))
        self.counter_label.pack(pady=10)

        tk.Button(content_frame, text="Increment Counter",
                  command=self.increment_counter).pack(pady=5)

    def increment_counter(self):
        """Update the counter label"""
        self.counter += 1
        self.counter_label.config(text=f"Counter: {self.counter}")


class SettingsScreen(BaseScreen):
    """Settings screen with various widgets"""

    def setup_ui(self):
        # Title
        title = tk.Label(self, text="Settings Screen", font=("Arial", 24, "bold"))
        title.pack(pady=20)

        # Back button
        tk.Button(self, text="Back to Home",
                  command=lambda: self.controller.show_frame(HomeScreen),
                  width=20, height=2).pack(pady=10)

        # Settings content
        settings_frame = tk.Frame(self, relief="sunken", bd=2)
        settings_frame.pack(pady=20, padx=20, fill="both", expand=True)

        # Theme selection
        tk.Label(settings_frame, text="Theme:", font=("Arial", 12)).pack(pady=5)

        self.theme_var = tk.StringVar(value="light")
        themes = ["light", "dark", "blue"]
        theme_menu = ttk.Combobox(settings_frame, textvariable=self.theme_var,
                                  values=themes, state="readonly")
        theme_menu.pack(pady=5)
        theme_menu.bind("<<ComboboxSelected>>", self.on_theme_change)

        # Font size slider
        tk.Label(settings_frame, text="Font Size:", font=("Arial", 12)).pack(pady=5)

        self.font_size = tk.IntVar(value=12)
        font_slider = tk.Scale(settings_frame, from_=8, to=24, orient="horizontal",
                               variable=self.font_size, command=self.on_font_change)
        font_slider.pack(pady=5)

        # Checkbox example
        self.notifications_var = tk.BooleanVar(value=True)
        notifications_cb = tk.Checkbutton(settings_frame, text="Enable Notifications",
                                          variable=self.notifications_var,
                                          command=self.on_notification_toggle)
        notifications_cb.pack(pady=10)

        # Status label that gets updated
        self.status_label = tk.Label(settings_frame, text="Settings loaded",
                                     font=("Arial", 10), fg="blue")
        self.status_label.pack(pady=10)

    def on_theme_change(self, event):
        """Handle theme change"""
        theme = self.theme_var.get()
        self.status_label.config(text=f"Theme changed to: {theme}")

    def on_font_change(self, value):
        """Handle font size change"""
        self.status_label.config(text=f"Font size: {value}")

    def on_notification_toggle(self):
        """Handle notification toggle"""
        status = "enabled" if self.notifications_var.get() else "disabled"
        self.status_label.config(text=f"Notifications {status}")


class DataScreen(BaseScreen):
    """Data display and manipulation screen"""

    def setup_ui(self):
        menu_bar = tk.Menu(self.controller)
        file_button = tk.Menu(menu_bar, tearoff=0)
        edit_button = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label='file', menu=file_button)
        file_button.add_command(label='Open log file', command=lambda: self.controller.open_log_file())
        file_button.add_command(label='Open default file', command=lambda: self.controller.open_default_log_file())
        file_button.add_command(label='delete db', command=lambda: self.controller.delete_db())
        file_button.add_separator()
        file_button.add_command(label='Back', command=lambda: self.controller.show_frame(HomeScreen))
        menu_bar.add_cascade(label='edit', menu=edit_button)
        edit_button.add_command(label='use white space delimiter', command=lambda: self.controller.white_space_delimiter())
        self.controller.config(menu=menu_bar)

        self.status = StatusBar(self)
        self.status.set("hello")

        # Data content frame
        # self.data_frame = tk.Frame(self, relief="sunken")
        # self.data_frame.pack(side='top', pady=5, padx=5, fill="both", expand=True)

    def create_tree_view(self, data):
        # Create a scrollable text widget
        self.tree_frame = tk.Frame(self)
        self.tree_frame.pack(fill="both", expand=True)

        scroll_bar = ttk.Scrollbar(self.tree_frame, orient='vertical')

        tree = ttk.Treeview(self.tree_frame, yscrollcommand=scroll_bar.set, show="headings")
        tree.pack(fill="both", expand=True)
        scroll_bar.config(command=tree.yview)

        columns = ["index"]
        for i in range(len(data[0])):
            columns.append(f"col_{i}")

        columns_num = len(columns)
        column_width = int((3000 - 15)/columns_num)

        tree['columns'] = columns

        for i in range(columns_num):
            if i == 1:
                tree.column(f"#{i}", anchor=tk.W, stretch=tk.NO, width=30)
            else:
                tree.column(f"#{i}", anchor=tk.W, stretch=tk.NO, width=column_width)

        for i in range(columns_num):
            if i == 0:
                tree.heading("#0", anchor=tk.W, text="ID")
            else:
                tree.heading(f"#{i}", text=f"col_{i}")

        # insert
        for i, row in enumerate(data):
            tree.insert(parent='', index='end', iid=str(i), text='', values=row)


if __name__ == "__main__":

    # log_file_dir = "D:\semantic DNS search\log files\dns.log"
    # conn = sqlite3.connect(log_file_dir.rsplit('.')[0] + '.db')
    # sql_query = """SELECT name FROM sqlite_master WHERE type='table';"""
    # cursor = conn.cursor()
    # cursor.execute(sql_query)
    # print(cursor.fetchall())

    root = GUI()
    root.mainloop()
