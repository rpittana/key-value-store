import sys
import os

#list of [key, value] pairs
index = []

DB_FILE = "data.db"

def index_set(key, value):
    """Append a key-value pair to the index."""
    index.append([key, value])

def index_get(key):
    """Search for a key in the index and return its value if found."""
    for i in range(len(index) - 1, -1, -1):
        if index[i][0] == key:
            return index[i][1]
    return None

def persist_set(key, value):
    """Persist a key-value pair to the database file."""
    with open(DB_FILE, 'a') as f:
        f.write(f"{key}:{value}\n")
        f.flush() # write to os buffer
        os.fsync(f.fileno()) # flush to disk

def load_db():
    """Load key-value pairs from the database file into the index."""
    if not os.path.exists(DB_FILE):
        return
    with open(DB_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            key, value = line.split(':', 1)
            index_set(key, value)

def handle_command(line):
    """Parse and execute a command."""
    parts = line.strip().split(' ', 2)
    if len(parts) < 2:
        print("Invalid command")
        return
    cmd, key = parts[0], parts[1]
    if cmd == "SET":
        if len(parts) != 3:
            print("Invalid SET command")
            return
        value = parts[2]
        index_set(key, value)
        persist_set(key, value)
        print("OK")
    elif cmd == "GET":
        value = index_get(key)
        if value is not None:
            print(value)
        else:
            print("NULL")
    else:
        print("Unknown command")

def main():
    """Main loop to read commands from stdin."""
    load_db()
    print("Welcome to the key-value store. Enter commands:")
    for line in sys.stdin:
        result = handle_command(line)
        if result is not None:
            print(result)
            sys.stdout.flush()
if __name__ == "__main__":
    main()