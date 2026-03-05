import os
import sqlite3
import pandas as pd
import glob

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
DB_PATH = BASE_PATH + r"\transfermarkt.db"

conn = sqlite3.connect(DB_PATH)

for csv_file in glob.glob(BASE_PATH + r"\**\*.csv", recursive=True):
    table_name = csv_file.split("\\")[-2]
    df = pd.read_csv(csv_file, low_memory=False)
    df.to_sql(table_name, conn, if_exists="replace", index=False)

conn.close()

