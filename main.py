from database import Database
import filedialpy
import os
from pathlib import Path
import tkinter as tk
from tkinter import ttk
import sqlite3
import sqlite_vec
import requests
import ollama
import semchunk
import re
from bs4 import BeautifulSoup

class GUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("csv searcher")
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

    def open_csv_file(self, option):
        self.database = Database()
        if (option == "filediag"):
            self.csv_file_dir = filedialpy.openFile()
        if (option == "default"):
            main_dir = Path(__file__).absolute().parent
            self.csv_file_dir = main_dir / 'csv files' / 'sampleURLs.csv'
        self.frames[DataScreen].status.set(f"Opening {self.csv_file_dir}")
        response = self.database.load_csv_file(self.csv_file_dir)
        self.frames[DataScreen].setup_ui()
        self.frames[DataScreen].status.set(response)

    def open_db_file(self, db_dir):
        self.database = Database()
        csv = self.database.query_entire_database(Path(db_dir).name)
        if csv:
            self.frames[DataScreen].create_tree_view(csv)
            self.frames[DataScreen].status.set(f"Opened {Path(db_dir).name}")
        else:
            self.frames[DataScreen].status.set("could not open database")

    def generate_embedding(self):
        return

    def white_space_delimiter(self): # Not used
        self.database.split(" ")
        # file_name = os.path.basename(self.csv_file_dir).rsplit('.')[0]
        db_file_dir = os.path.join(os.path.split(os.path.split(self.csv_file_dir)[0])[0], os.path.basename(self.csv_file_dir).rsplit('.')[0] + ".db")
        # db_file_dir = self.csv_file_dir.rstrip(db_file_name) + ".db"
        self.database.open_db_file(db_file_dir)
        self.frames[DataScreen].status.set(f"Opening {self.csv_file_dir}")
        csv = self.database.query_entire_database()
        if csv:
            self.frames[DataScreen].tree_frame.destroy()
            self.frames[DataScreen].create_tree_view(csv)
            self.frames[DataScreen].status.set(f"updated {self.csv_file_dir}")
        else:
            self.frames[DataScreen].status.set("No database loaded")

    def delete_db(self):
        sql = 'DELETE FROM csv'
        self.csv_file_dir = r"D:\semantic DNS search\csv files\dns.csv"
        if not self.database.conn:
            self.database.conn = sqlite3.connect(self.csv_file_dir.rsplit('.')[0] + '.db')
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
        file_button.add_command(label='Open csv file', command=lambda: self.controller.open_csv_file("filediag"))
        file_button.add_command(label='Open default csv file', command=lambda: self.controller.open_csv_file("default"))

        db_files_dir = Path(__file__).absolute().parent / "db files"
        for file in db_files_dir.iterdir():
            if file.suffix.lower() == ".db":
                file_button.add_command(label='Open ' + os.path.basename(file).split('.')[0] + ' database', command=lambda: self.controller.open_db_file(file))

        file_button.add_command(label='delete db', command=lambda: self.controller.delete_db())
        menu_bar.add_command(label='generate embedding for db', command=lambda: self.controller.generate_embedding())
        # edit_button.add_command(label='use white space delimiter', command=lambda: self.controller.white_space_delimiter())
        menu_bar.add_command(label='go to semantic search', command=lambda: self.controller.show_frame(HomeScreen))
        menu_bar.add_command(label='go to data screen', command=lambda: self.controller.show_frame(DataScreen))
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

        columns = ["index", "id", "url", "hash id"]

        columns_num = len(columns)
        # column_width = int((3000 - 15)/columns_num)

        tree['columns'] = columns

        """
        for i in range(columns_num):
            if i == 1:
                tree.column(f"#{i}", anchor=tk.W, stretch=tk.NO, width=120)
            else:
                tree.column(f"#{i}", anchor=tk.W, stretch=tk.NO, width=column_width)

        for i in range(columns_num):
            if i == 0:
                tree.heading("#0", anchor=tk.W, text="ID")
            else:
                tree.heading(f"#{i}", text=f"col_{i}")"""

        tree.column(f"#{1}", anchor=tk.W, stretch=tk.NO, width=130)
        tree.column(f"#{2}", anchor=tk.W, stretch=tk.NO, width=500)
        tree.column(f"#{3}", anchor=tk.W, stretch=tk.NO, width=170)
        tree.heading("#1", anchor=tk.W, text="ID")
        tree.heading("#2", text="URL")
        tree.heading("#3", text="embedding")

        # insert
        for i, row in enumerate(data):
            tree.insert(parent='', index='end', iid=str(i), text='', values=row)


if __name__ == "__main__":
    """
    url = 'https://www.reddit.com/r/Volkswagen/comments/106d8cc/oil_sensor_service_vehicle_light/'
    try:
        r = requests.get(url)
    except requests.exceptions.RequestException as e:
        print(f"exception: {e}")
    divider = r"==============================================================================================="

    # Parse the source code using BeautifulSoup
    text = BeautifulSoup(r.text, 'html.parser')

    # Extract the plain text content
    """

    # text_cleaned = re.sub(r"(\n|\s{2,})", " ", text.get_text(separator=" "))
    """
    print(text_cleaned)
    print(f"length of text_cleaned: {len(text_cleaned)}")

    text_chunks = semchunk.chunkerify(lambda text_cleaned: len(text_cleaned) / 4, 500)(text_cleaned, overlap=0.2)

    print(f"number of chunks: {len(text_chunks)}")

    embeddings = ollama.embed(model='nomic-embed-text', input=text_chunks)

    print(f"number of vectors: {len(embeddings["embeddings"][0])}")
    """

    root = GUI()
    root.mainloop()
