import sqlite3
from datetime import datetime
from termcolor import colored

connection = sqlite3.connect("memory.db")
cursor = connection.cursor()
mem_debug = True

def term_print(input, color):
    print(colored(f"memory > {input}", color))

def create_if_empty():
    cursor.execute("CREATE TABLE IF NOT EXISTS memory(role TEXT, content TEXT, timestamp TEXT)")
    cursor.commit()
    if mem_debug:
        term_print("Created memory db if not existing", "cyan")
    
    
def add_conversation(role, content):
    cursor.execute("INSERT INTO memory VALUES(?, ?, ?)", (role, content, str(datetime.now())))
    cursor.commit()
    if mem_debug:
        term_print("Added conversation to memory", "cyan")