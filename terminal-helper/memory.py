import sqlite3
import json
from datetime import datetime
from termcolor import colored

connection = sqlite3.connect("memory.db")
cursor = connection.cursor()
mem_debug = True
conversation_limit = 5

def term_print(input, color):
    print(colored(f"memory > {input}", color))

def create_if_empty():
    cursor.execute("CREATE TABLE IF NOT EXISTS memory(role TEXT, content TEXT, timestamp TEXT)")
    connection.commit()
    if mem_debug:
        term_print("Created memory db if not existing", "cyan")
    
    
def add_conversation(role, content):
    cursor.execute("INSERT INTO memory VALUES(?, ?, ?)", (role, json.dumps(content), str(datetime.now())))
    connection.commit()
    if mem_debug:
        term_print("Added conversation to memory", "cyan")
        
def get_recent_conversations():
    conversations = []
    for row in cursor.execute("SELECT role, content, timestamp FROM memory ORDER BY timestamp DESC"):
        if len(conversations) > conversation_limit:
            break
        conversations.append({"role": row[0], "content": row[1], "timestamp": row[2]})
    if mem_debug:
        term_print(f"Selecting {conversation_limit} most recent converstations", "cyan")
    return conversations

def print_memory():
    term_print("================= Memory Contents Below =================", "cyan")
    for row in cursor.execute("SELECT role, content, timestamp FROM memory ORDER BY timestamp DESC"):
        term_print(json.dumps({"role": row[0], "content": row[1], "timestamp": row[2]}, indent=4), "cyan")
        
def write_memory_to_file(file_name):
    conversations = []
    for row in cursor.execute("SELECT role, content, timestamp FROM memory ORDER BY timestamp DESC"):
        conversations.append({"role": row[0], "content": row[1], "timestamp": row[2]}, "cyan")
    with open(f"{file_name}.json", "w") as fp:
        fp.write(json.dumps(conversations, indent=4))
    term_print(f"Wrote memory to file {file_name}", "cyan")
        
def clear_memory():
    cursor.execute("DROP TABLE IF EXISTS memory")
    term_print("Clearing memory", "cyan")
    connection.commit()
    create_if_empty()
    