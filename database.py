import tkinter as tk
import sqlite3
import sqlite_vec
from tkinter import messagebox
import csv
import os
from pathlib import Path
from typing import List
import struct
import requests
import ollama
import semchunk
import re
from bs4 import BeautifulSoup


def serialize_f32(vector: List[float]) -> bytes:
    """serializes a list of floats into a compact "raw bytes" format"""
    return struct.pack("%sf" % len(vector), *vector)

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

    def hashInsert(self, url_line): # UNFINISHED
        for url in url_line:
            hash_id = hash(url)
            self.cursor.execute("SELECT 1 FROM " + self.db_name + " WHERE id = ?", (hash_id,))
            exists = self.cursor.fetchone()
            if not exists:
                self.cursor.execute("INSERT INTO " + self.db_name + " VALUES (?)", (hash_id,))

        self.cursor.execute("INSERT INTO urls VALUES (?)", (url,))

    def load_csv_file(self, csv_file_path):
        file_name_with_type = os.path.basename(csv_file_path)
        file_name = file_name_with_type.split(".")[0]
        self.db_name = file_name
        db_dir = Path(__file__).absolute().parent / "db files"
        loaded = False
        if os.path.isfile(db_dir / f"{file_name}.db"):
            loaded = True
        os.chdir(db_dir)
        if hasattr(self, "conn"):
            self.conn.close()
        self.conn = sqlite3.connect(f"{file_name}.db")
        self.conn.enable_load_extension(True)
        sqlite_vec.load(self.conn)
        self.conn.enable_load_extension(False)
        self.cursor = self.conn.cursor()
        loaded = False
        if not loaded:
            self.cursor.execute("CREATE TABLE IF NOT EXISTS " + file_name + "(id INTEGER PRIMARY KEY, url TEXT)")
            self.conn.commit()
            with open(csv_file_path, mode='r') as file:
                csv_file = csv.reader(file)
                for line in csv_file:
                    for url in line:
                        hash_id = hash(url)
                        self.cursor.execute("INSERT INTO " + file_name + " VALUES (?, ?)", (hash_id, url))
        self.conn.commit()
        if loaded:
            return "db for csv file already exists"
        else:
            return "created db for csv file"

    def open_db_file(self, db_file_name):
        db_dir = Path(__file__).absolute().parent / "db files"
        os.chdir(db_dir)
        if hasattr(self, "conn"):
            self.conn.close()
        name_cleaned = os.path.basename(db_file_name).split(".")[0]
        self.db_name = name_cleaned
        self.conn = sqlite3.connect(f"{name_cleaned}.db")
        self.conn.enable_load_extension(True)
        sqlite_vec.load(self.conn)
        self.conn.enable_load_extension(False)
        self.cursor = self.conn.cursor()

    def query_entire_database(self, db_name):
        self.db_name = db_name
        db_dir = Path(__file__).absolute().parent / "db files"
        os.chdir(db_dir)
        self.conn.close()
        self.conn = sqlite3.connect(f"{db_name}.db")
        self.conn.enable_load_extension(True)
        sqlite_vec.load(self.conn)
        self.conn.enable_load_extension(False)
        self.cursor = self.conn.cursor()
        self.cursor.execute("SELECT * FROM " + db_name.split(".")[0])
        csv = self.cursor.fetchall()
        return csv

    def check_if_embedding_exists(self, id, zero_embedding=None):
        self.cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{self.db_name + "_vec"}'")
        if self.cursor.fetchone():
            self.cursor.execute(f"SELECT embedding FROM {self.db_name + "_vec"} WHERE id=? LIMIT 1", (id,))
            embedding = self.cursor.fetchone()
            if embedding:
                if zero_embedding is not None:
                    if embedding[0] == zero_embedding:
                        return 2
                if embedding[0]:
                    return 1
        return 0

    @staticmethod
    def serialize_f32(vector: List[float]) -> bytes:
        """serializes a list of floats into a compact "raw bytes" format"""
        return struct.pack("%sf" % len(vector), *vector)

    @staticmethod
    def deserialize_f32(blob: bytes) -> List[float]:
        return list(struct.unpack("%sf" % (len(blob) // 4), blob))

    def generate_embeddings(self, status_bar=None):
        if hasattr(self, "db_name"):
            data = self.query_entire_database(self.db_name)
            self.cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{self.db_name + "_vec"}'")
            if not self.cursor.fetchone():
                self.cursor.execute(f"CREATE VIRTUAL TABLE {self.db_name + "_vec"} USING vec0(id INTEGER, embedding float[768])")
            # count the number of urls without embeddings
            if status_bar is not None:
                embeddings_to_generate = self.cursor.execute(
                    f"""
                    SELECT COUNT(*) AS missing_count
                    FROM {self.db_name} AS t
                    LEFT JOIN {self.db_name}_vec AS v ON t.id = v.id
                    WHERE v.id IS NULL
                    """
                ).fetchone()[0]
            generating_index = 0
            zero_embedding = serialize_f32([0.0] * 768)
            deleted_rows = 0
            ollama_errors = 0
            for id, url in data:
                if status_bar is not None:
                    status_bar.set(f"Generating embedding (GUI might be frozen while generating) #{generating_index} out of {embeddings_to_generate}")
                self.cursor.execute(f"SELECT id FROM {self.db_name + "_vec"} WHERE id=? LIMIT 1", (id,))
                if not self.cursor.fetchone():
                    try:
                        generating_index += 1
                        r = requests.get(url)
                        text = BeautifulSoup(r.text, 'html.parser')
                        text_cleaned = re.sub(r'[^a-zA-Z0-9]', " ", text.get_text(separator=" "))
                        text_cleaned = re.sub(r"(\n|\s{2,})", " ", text_cleaned)
                        text_chunks = semchunk.chunkerify(lambda text_cleaned: len(text_cleaned) / 4, 500)(text_cleaned,
                                                                                                           overlap=0.2)
                    except Exception:
                        self.cursor.execute(f"DELETE FROM {self.db_name} WHERE id=?", (id,))
                        self.conn.commit()
                        deleted_rows += 1
                        continue

                    if text_chunks == []:
                        """self.cursor.execute(f"INSERT INTO {self.db_name + "_vec"}(id, embedding) VALUES (?, ?)",
                                            [id, zero_embedding, ])
                        self.conn.commit()"""
                        self.cursor.execute(f"DELETE FROM {self.db_name} WHERE id=?", (id,))
                        self.conn.commit()
                        deleted_rows += 1
                        continue
                    # break the text_chunks list in to smaller lists in case the computer doesn't have enough ram for large model queries
                    text_chunks_pieces = [text_chunks[i:i + 10] for i in range(0, len(text_chunks), 10)]
                    for piece in text_chunks_pieces:
                        try:
                            embeddings = ollama.embed(model='nomic-embed-text', input=piece)
                        except ConnectionError:
                            return "Ollama service not running, network issues, invalid host"
                        except ollama.RequestError:
                            return "Missing model"
                        except ollama.ResponseError:
                            ollama_errors += 1
                            self.cursor.execute(f"DELETE FROM {self.db_name} WHERE id=?", (id,))
                            self.conn.commit()
                            continue
                        for embedding in embeddings["embeddings"]:
                            self.cursor.execute(f"INSERT INTO {self.db_name + "_vec"}(id, embedding) VALUES (?, ?)", [id, serialize_f32(embedding), ])
                        self.conn.commit()
            return f"finished generating embeddings. {deleted_rows} rows deleted due to bad URL, {ollama_errors} ollama errors"
        else:
            return "open up a db file first"

    def query(self, input_query):
        sql = f"""
        WITH knn AS (
          SELECT
            v.id,
            v.distance
          FROM {self.db_name}_vec AS v
          WHERE v.embedding MATCH ?
            AND k = ?
          ORDER BY v.distance
        ),
        best_per_id AS (
          SELECT
            id,
            MIN(distance) AS best_distance
          FROM knn
          GROUP BY id
        )
        SELECT
          t.url,
          b.best_distance AS distance
        FROM best_per_id AS b
        JOIN {self.db_name} AS t
          ON t.id = b.id   -- or t.hash_id if that’s your column name
        ORDER BY distance
        LIMIT ?;           -- final number of unique URLs you want
        """

        query_vector = ollama.embed(model='nomic-embed-text', input=input_query)
        rows = self.cursor.execute(sql, [serialize_f32(query_vector["embeddings"][0]), 1000, 5]).fetchall()
        return rows