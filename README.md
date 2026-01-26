# Overview

This project was created as a minimal local semantic search engine to search for the most relavent URL in a CSV. A simple GUI makes it so you don't have to use a CLI.
The original problem it was designed to solve was to search for websites inside of a DNS log of URLs visited by users on the network.

* Ollama for LLM vector embedding
* Sqlite3 and sqlite_vec extension for local vector DB
* tkinter GUI
* BeautifulSoup for HTML parsing and webscrapping
* Text chunking/processing via semchunk
* Text chunking/processing via semchunk

## How to use

Clone the repo

Install dependencies (see below for details)

Make sure Ollama is running and a embedding model is downloaded. The default embedding model is [nomic-embed-text](https://ollama.com/library/nomic-embed-text)
You can use any embedding model of your choosing as long as it produces a 768-dimension float vector.

```
ollama pull nomic-embed-text
```

If you choose to use a different embedding model, edit the line near the top of main.py "self.ollama_model = "nomic-embed-text"" to the embedding model you wish to use.

Run main.py

Go to **file > open csv file** , to open the .CSV file of URLs you wish to create the database off of. Or you can use the included **file > open default csv file** to test

A sqlite3 database will be created in the **db files** folder. Preview the database with **file > open [db name] database**

<img width="1001" height="816" alt="image" src="https://github.com/user-attachments/assets/d642ec0c-6c0b-4d03-a908-847625ca45a8" />

Click on **generate embedding for db** to start scrapping the web and generating embeddings.

<img width="1000" height="134" alt="image" src="https://github.com/user-attachments/assets/08f41757-080e-4b5f-99f2-e89446fa7e20" />

Once finished, click on **go to semantic search** to enter the querying screen.

<img width="1001" height="814" alt="image" src="https://github.com/user-attachments/assets/4c8c257d-2375-42fa-aa10-b8cdd8592a33" />

Delete databases from **file > delete [db name] database**

<img width="400" height="223" alt="image" src="https://github.com/user-attachments/assets/b888f8ca-9140-4b33-9067-050ae5ca3dc5" />

<details>
<summary>Click to expand folder layout</summary>

```text
.
├── main.py
├── database.py
├── csv files/ # drop your own csv files you wish to search through in here
│   ├── sampleURLcsv.csv
├── db files/ # database files will go here
├── requirements.txt
└── README.md
```

</details>

## Dependencies

* Python 3.X+
* sqlite_vec
* requests
* ollama
* semchunk
* beautifulsoup4 (for bs4)
* filedialpy

You can install them with pip:

```
pip install sqlite_vec requests ollama semchunk beautifulsoup4 filedialpy
```

Or install from requirements.txt

```
pip install -r requirements.txt
```


