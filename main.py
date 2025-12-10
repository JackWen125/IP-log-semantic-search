from database import Database
import filedialpy
import os
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext


class GUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("csv searcher")
        self.geometry("800x600")
        self.current_screen = "DataScreen"

        self.database = Database()

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
        self.current_screen = frame_class.__name__
        self.frames[DataScreen].create_menu_bar()
        # Call the on_show method if it exists (for initialization)
        if hasattr(frame, 'on_show'):
            frame.on_show()

    def open_csv_file(self, option):
        if (option == "filediag"):
            self.csv_file_path = filedialpy.openFile()
        if (option == "default"):
            main_dir = Path(__file__).absolute().parent
            self.csv_file_path = main_dir / 'csv files' / 'sampleURLs.csv'
        self.frames[DataScreen].status.set(f"Opening {self.csv_file_path}")
        response = self.database.load_csv_file(self.csv_file_path)
        self.frames[DataScreen].status.set(response)
        self.frames[DataScreen].create_menu_bar()

    def open_db_file(self, db_dir):
        self.frames[DataScreen].status.set(f"Opening {db_dir}")
        self.database.open_db_file(db_dir)
        if hasattr(self.frames[DataScreen], 'tree_frame'):
            self.frames[DataScreen].tree_frame.destroy()
        self.frames[DataScreen].status.set(f"Generating tree view")
        response = self.frames[DataScreen].create_tree_view(self.database)
        self.frames[DataScreen].status.set(response)

    def generate_embedding(self):
        self.frames[DataScreen].status.set(f"Generating embedding")
        response = self.database.generate_embeddings(status_bar=self.frames[DataScreen].status)
        self.frames[DataScreen].status.set(response)
        if hasattr(self.frames[DataScreen], 'tree_frame'):
            self.frames[DataScreen].tree_frame.destroy()
        self.frames[DataScreen].create_tree_view(self.database)
        """
        try:
            response = self.database.generate_embeddings()
            self.frames[DataScreen].status.set(response)
        except Exception:
            self.frames[DataScreen].status.set(Exception)
        """

    def white_space_delimiter(self): # Not used
        self.database.split(" ")
        # file_name = os.path.basename(self.csv_file_path).rsplit('.')[0]
        db_file_dir = os.path.join(os.path.split(os.path.split(self.csv_file_path)[0])[0], os.path.basename(self.csv_file_path).rsplit('.')[0] + ".db")
        # db_file_dir = self.csv_file_path.rstrip(db_file_name) + ".db"
        self.database.open_db_file(db_file_dir)
        self.frames[DataScreen].status.set(f"Opening {self.csv_file_path}")
        csv = self.database.query_entire_database()
        if csv:
            self.frames[DataScreen].tree_frame.destroy()
            self.frames[DataScreen].create_tree_view(csv)
            self.frames[DataScreen].status.set(f"updated {self.csv_file_path}")
        else:
            self.frames[DataScreen].status.set("No database loaded")

    def delete_db(self, db_name):
        if hasattr(self.frames[DataScreen], 'tree_frame') and hasattr(self.database, "db_name"):
            if self.database.db_name == db_name:
                self.frames[DataScreen].tree_frame.destroy()
        if hasattr(self.database, "conn"):
            self.database.conn.commit()
            self.database.cursor.close()
            self.database.conn.close()
        db_dir = Path(__file__).absolute().parent / "db files"
        os.chdir(db_dir)
        os.remove(db_name + ".db")
        self.frames[DataScreen].create_menu_bar()

    def query(self, query):
        response = self.database.query(query)
        self.frames[HomeScreen].insert_to_output_box(f"Query: {query}\n")
        for row in response:
            url, distance = row
            line = f"Distance: {distance:.4f}, URL: {url}\n"
            self.frames[HomeScreen].insert_to_output_box(line)
        self.frames[HomeScreen].insert_to_output_box("\n")

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
        self.label.update_idletasks()

    def clear(self):
        self.label.config(text="")

class HomeScreen(BaseScreen):
    """Main home screen"""

    def setup_ui(self):
        # Title
        title = tk.Label(self, text="Search database", font=("Arial", 24, "bold"))
        title.pack(pady=20)
        # the input text field and button
        self.txt = tk.Entry(self, width=150)
        self.txt.pack()
        btn = tk.Button(self, text="Search", command=self.enter_key_pressed)
        self.txt.bind("<Return>",lambda event: self.enter_key_pressed())
        btn.pack()
        # THe output field
        self.output_box = scrolledtext.ScrolledText(self, width=80, height=20)
        self.output_box.pack(fill=tk.BOTH, expand=True)

    def insert_to_output_box(self, text):
        self.output_box.insert(tk.END, text)
        self.output_box.see(tk.END)

    def enter_key_pressed(self):
        if not hasattr(self.controller.database, "db_name"):
            return
        text = self.txt.get()
        if text:
            self.controller.query(text)
            self.txt.delete(0, tk.END)

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
        self.create_menu_bar()
        self.status = StatusBar(self)
        self.status.set("hello")

        # Data content frame
        # self.data_frame = tk.Frame(self, relief="sunken")
        # self.data_frame.pack(side='top', pady=5, padx=5, fill="both", expand=True)
    def create_menu_bar(self):
        menu_bar = tk.Menu(self.controller)
        file_button = tk.Menu(menu_bar, tearoff=0)
        edit_button = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label='file', menu=file_button)
        file_button.add_command(label='Open csv file', command=lambda: self.controller.open_csv_file("filediag"))
        file_button.add_command(label='Open default csv file', command=lambda: self.controller.open_csv_file("default"))

        db_files_dir = Path(__file__).absolute().parent / "db files"
        for file in db_files_dir.iterdir():
            if file.suffix.lower() == ".db":
                db_name = os.path.basename(file).split('.')[0]
                file_button.add_command(label='Open ' + db_name + ' database',
                                        command=lambda: self.controller.open_db_file(db_name))
                file_button.add_command(label='Delete ' + db_name + ' database',
                                        command=lambda: self.controller.delete_db(db_name))

        file_button.add_command(label='delete db', command=lambda: self.controller.delete_db())
        menu_bar.add_command(label='generate embedding for db', command=lambda: self.controller.generate_embedding())
        # edit_button.add_command(label='use white space delimiter', command=lambda: self.controller.white_space_delimiter())
        if self.controller.current_screen == "DataScreen":
            menu_bar.add_command(label='go to semantic search', command=lambda: self.controller.show_frame(HomeScreen))
        if self.controller.current_screen == "HomeScreen":
            menu_bar.add_command(label='go to data screen', command=lambda: self.controller.show_frame(DataScreen))
        self.controller.config(menu=menu_bar)

    def create_tree_view(self, database):
        self.tree_frame = tk.Frame(self)
        self.tree_frame.pack(fill="both", expand=True)
        scroll_bar = ttk.Scrollbar(self.tree_frame, orient='vertical')
        tree = ttk.Treeview(self.tree_frame, yscrollcommand=scroll_bar.set, show="headings")
        tree.pack(fill="both", expand=True)
        scroll_bar.config(command=tree.yview)
        tree['columns'] = ["index", "id", "url", "hash id"]
        columns_num = len(tree['columns'])
        # column_width = int((3000 - 15)/columns_num)

        tree.column(f"#{1}", anchor="w", stretch=tk.NO, width=130)
        tree.column(f"#{2}", anchor="w", stretch=tk.NO, width=500)
        tree.column(f"#{3}", anchor="w", stretch=tk.NO, width=170)
        tree.heading("#1", anchor="w", text="ID")
        tree.heading("#2", text="URL")
        tree.heading("#3", text="embedding")

        # insert regular table first
        if hasattr(database, "db_name"):
            url_table_data = database.query_entire_database(database.db_name)
            zero_embedding = database.serialize_f32([0.0] * 768)
            for i, row in enumerate(url_table_data):
                embedding_status = database.check_if_embedding_exists(row[0], zero_embedding)
                if embedding_status == 0: embedded_column = "No"
                if embedding_status == 1: embedded_column = "Yes"
                if embedding_status == 2: embedded_column = "Bad URL"

                tree.insert(parent='', index='end', iid=str(i), text='',
                            values=(row[0], row[1], embedded_column))
            return "successfully loaded tree view"
        else:
            return "No valid database loaded"

if __name__ == "__main__":
    root = GUI()
    root.mainloop()
