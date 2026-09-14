import sqlite3
db_path = r'C:\Users\DSL\AppData\Local\Ollama\db.sqlite'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print('Tables:', tables)
for (t,) in tables:
    try:
        cursor.execute(f"SELECT * FROM [{t}] LIMIT 5")
        rows = cursor.fetchall()
        print(f"{t}: {rows}")
    except Exception as e:
        print(f"{t}: ERROR {e}")
conn.close()
