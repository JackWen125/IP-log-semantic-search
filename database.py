import tkinter as tk
import sqlite3
from tkinter import messagebox
import os

class Database:
    def __init__(self):
        # Create a database or connect to an existing one
        # self.conn = sqlite3.connect("testdb.db")
        # self.cursor = self.conn.cursor()

        # Create a table if it doesn't exist
        # self.cursor.execute('''CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, task TEXT)''')
        # self.conn.commit()
        return

    def add_task(self):
        task = self.task_entry.get()
        if task:
            self.cursor.execute("INSERT INTO tasks (task) VALUES (?)", (task,))
            self.conn.commit()
            self.load_tasks()
            self.task_entry.delete(0, tk.END)
        else:
            messagebox.showwarning("Warning", "Please input a task.")

    def load_tasks(self):
        self.task_listbox.delete(0, tk.END)
        self.cursor.execute("SELECT * FROM tasks")
        tasks = self.cursor.fetchall()
        for row in tasks:
            self.task_listbox.insert(tk.END, row[1])

    def delete_task(self):
        selected_task = self.task_listbox.get(tk.ACTIVE)
        if selected_task:
            self.cursor.execute("DELETE FROM tasks WHERE task=?", (selected_task,))
            self.conn.commit()
            self.load_tasks()
        else:
            messagebox.showwarning("Warning", "Please select a task to delete.")

    def insertRow(self, text_list):
        """
        :param text_list: will insert each element of the list as a cell/column element
        :return: none
        """
        front = "INSERT INTO log VALUES ("
        rest = ""
        for x in text_list:
            if isinstance(x, int):
                rest += str(x) + ","
            else:
                rest += str('"' + x + '"')
        rest += ')'
        self.cursor.execute(front + rest)

    def load_log_file(self, log_file_dir):
        file_name = os.path.basename(log_file_dir)
        os.chdir(log_file_dir.rstrip(file_name))
        os.chdir('..')
        loaded = False
        if os.path.isfile(file_name.rsplit('.')[0] + '.db'):
            loaded = True
        self.conn = sqlite3.connect(file_name.rsplit('.')[0] + '.db')
        self.cursor = self.conn.cursor()

        if not loaded:
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS log (id INTEGER PRIMARY KEY, col_1 TEXT)''')
            self.conn.commit()
            log_file = open(log_file_dir, mode='r')
            for i, line in enumerate(log_file):
                self.insertRow([i, line])
        self.conn.commit()

    def open_db_file(self, db_file_dir):
        self.conn = sqlite3.connect(db_file_dir)
        self.cursor = self.conn.cursor()

    def query_entire_database(self):
        if self.conn:
            self.cursor.execute("SELECT * FROM log")
            log = self.cursor.fetchall()
            return log
        else:
            return 0

    def split(self, delimiter):
        cur = self.cursor

        # 1. Get existing columns (in order)
        cur.execute("PRAGMA table_info(log);")
        cols_info = cur.fetchall()
        print(f"cols_info {cols_info}")
        # cols_info rows: (cid, name, type, notnull, dflt_value, pk)
        col_names = [c[1] for c in cols_info]

        if "id" not in col_names or "col_1" not in col_names:
            raise RuntimeError("Table 'log' must have columns 'id' and 'col_1'")

        # 2. Read all rows: id and col_1 only
        cur.execute("SELECT id, col_1 FROM log;")
        rows = cur.fetchall()  # list of (id, col_1_str)

        # 3. Determine maximum number of parts needed
        max_parts = 0
        split_cache = {}  # id -> list of parts

        for row_id, value in rows:
            if value is None:
                parts = []
            else:
                parts = str(value).split(delimiter)
            split_cache[row_id] = parts
            if len(parts) > max_parts:
                max_parts = len(parts)

        if max_parts == 0:
            # Nothing to split; no changes needed
            return

        # 4. Ensure we have enough columns col_1..col_{max_parts}
        # Figure out which col_i already exist
        existing_col_indices = {}
        for name in col_names:
            if name.startswith("col_"):
                try:
                    idx = int(name.split("_", 1)[1])
                    existing_col_indices[idx] = True
                except ValueError:
                    pass

        # Add missing columns
        # Note: SQLite allows ALTER TABLE ... ADD COLUMN only one at a time
        for i in range(1, max_parts + 1):
            col_name = f"col_{i}"
            if i not in existing_col_indices:
                # Add new TEXT column
                cur.execute(f'ALTER TABLE log ADD COLUMN "{col_name}" TEXT;')

        # 5. Update rows with split values
        # We'll update in batches to avoid many individual UPDATEs (optional optimization)
        # But for clarity, do per-row updates here.

        # Build the UPDATE statement template once (id + col_1..col_{max_parts})
        set_clauses = [f'col_{i} = ?' for i in range(1, max_parts + 1)]
        set_clause_str = ", ".join(set_clauses)
        update_sql = f"UPDATE log SET {set_clause_str} WHERE id = ?;"

        for row_id, parts in split_cache.items():
            # Pad or truncate parts to max_parts
            padded = parts[:max_parts] + [""] * (max_parts - len(parts))
            # Values: col_1..col_{max_parts}, then id for WHERE
            params = padded + [row_id]
            cur.execute(update_sql, params)
        self.conn.commit()

    def __del__(self):
        self.conn.close()