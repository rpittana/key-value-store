import sys
import os


# ── Data Store ────────────────────────────────────────────────────────────────

# In-memory index: a list of [key, value] pairs used to track all SET operations.
# A built-in dict is intentionally avoided per assignment requirements.
# Last-write-wins semantics are enforced by scanning the list in reverse order.
index: list[list[str]] = []

DB_FILE: str = "data.db"


# ── Index Operations ──────────────────────────────────────────────────────────

def index_set(key: str, value: str) -> None:
    """
    Append a new key-value pair to the in-memory index.

    Each call adds a new entry regardless of whether the key already exists.
    Last-write-wins semantics are enforced at read time by index_get().

    Args:
        key: The string key to store.
        value: The string value to associate with the key.
    """
    index.append([key, value])


def index_get(key: str) -> str | None:
    """
    Retrieve the most recent value associated with a key from the in-memory index.

    Scans the index in reverse order so that the last SET for a given key
    is always returned, enforcing last-write-wins semantics.

    Args:
        key: The string key to look up.

    Returns:
        The most recent value string for the key, or None if not found.
    """
    for i in range(len(index) - 1, -1, -1):
        if index[i][0] == key:
            return index[i][1]
    return None


# ── Persistence ───────────────────────────────────────────────────────────────

def persist_set(key: str, value: str) -> None:
    """
    Append a SET record to the append-only database file on disk.

    Each record is written as 'key:value' on its own line. After writing,
    the file buffer is flushed and fsync is called to guarantee the data
    is committed to disk before returning, protecting against data loss
    on unexpected program termination.

    Args:
        key: The string key to persist.
        value: The string value to persist.

    Raises:
        OSError: If the file cannot be opened or written to.
    """
    with open(DB_FILE, 'a') as f:
        f.write(f"{key}:{value}\n")
        f.flush()
        os.fsync(f.fileno())


def load_db() -> None:
    """
    Rebuild the in-memory index by replaying the append-only database file.

    Called once at startup. Each line in the file represents a previously
    persisted SET operation. Lines are replayed in order so that the index
    reflects the correct last-write-wins state after all entries are loaded.
    If the database file does not exist, this function returns without error,
    treating it as a fresh start.

    Raises:
        OSError: If the file exists but cannot be opened or read.
    """
    if not os.path.exists(DB_FILE):
        return
    with open(DB_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            key, value = line.split(':', 1)
            index_set(key, value)


# ── Command Handling ──────────────────────────────────────────────────────────

def handle_set(key: str, value: str) -> None:
    """
    Execute a SET command by persisting the key-value pair and updating the index.

    Writes to disk before updating memory to ensure durability. Prints 'OK'
    to stdout on success and flushes immediately for compatibility with
    automated black-box testing.

    Args:
        key: The string key to set.
        value: The string value to associate with the key.
    """
    persist_set(key, value)
    index_set(key, value)
    print("OK")
    sys.stdout.flush()


def handle_get(key: str) -> None:
    """
    Execute a GET command by looking up a key in the in-memory index.

    Prints the associated value if the key exists. Prints an empty line
    if the key has not been set, signaling absence without an error message.
    Output is flushed immediately for compatibility with automated testing.

    Args:
        key: The string key to retrieve.
    """
    value = index_get(key)
    print(value if value is not None else "")
    sys.stdout.flush()


def handle_command(line: str) -> None:
    """
    Parse a single line of input and dispatch to the appropriate command handler.

    Supports three commands:
        SET <key> <value>  — store a key-value pair
        GET <key>          — retrieve the value for a key
        EXIT               — terminate the program cleanly

    Command names are case-insensitive. Malformed SET or GET commands raise
    a ValueError rather than printing an error, allowing callers to handle
    control flow as needed.

    Args:
        line: A raw input string from stdin, including any trailing newline.

    Raises:
        ValueError: If a SET or GET command is missing required arguments.
    """
    parts = line.strip().split(' ', 2)
    if not parts or parts[0] == '':
        return

    cmd = parts[0].upper()

    if cmd == "SET":
        if len(parts) != 3:
            raise ValueError(f"SET requires <key> <value>, got: {line.strip()!r}")
        handle_set(parts[1], parts[2])

    elif cmd == "GET":
        if len(parts) < 2:
            raise ValueError(f"GET requires <key>, got: {line.strip()!r}")
        handle_get(parts[1])

    elif cmd == "EXIT":
        sys.exit(0)


# ── Entry Point ───────────────────────────────────────────────────────────────

def main() -> None:
    """
    Entry point for the key-value store.

    Loads any previously persisted data from disk by replaying the append-only
    log, then enters a read-eval-print loop reading commands from stdin line
    by line. Designed to work correctly with both interactive terminal use and
    automated black-box testing via piped input.

    Raises:
        OSError: If the database file cannot be read on startup or written during SET.
        ValueError: If a malformed command is received during the input loop.
    """
    load_db()
    for line in sys.stdin:
        handle_command(line)


if __name__ == "__main__":
    main()