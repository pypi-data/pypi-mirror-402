
import sqlite3
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from .tldr_tool import TLDRTool

class Indexer:
    """
    Background indexer for TLDR (L2 Analysis).
    Maintains a SQLite database of symbols and their callers.
    """
    
    SCHEMA = """
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        path TEXT UNIQUE,
        last_modified REAL
    );
    
    CREATE TABLE IF NOT EXISTS symbols (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        kind TEXT,
        file_id INTEGER,
        line INTEGER,
        FOREIGN KEY(file_id) REFERENCES files(id)
    );
    
    CREATE TABLE IF NOT EXISTS calls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        file_id INTEGER,
        line INTEGER,
        FOREIGN KEY(file_id) REFERENCES files(id)
    );
    
    CREATE INDEX IF NOT EXISTS idx_symbols_name ON symbols(name);
    CREATE INDEX IF NOT EXISTS idx_calls_name ON calls(name);
    """

    def __init__(self, db_path: str = ".onecode/tldr.db"):
        self.db_path = db_path
        self._ensure_db()
        self.tool = TLDRTool()

    def _ensure_db(self):
        """Initialize the database."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(self.SCHEMA)

    def index_directory(self, directory: str):
        """Index all files in a directory incrementally."""
        # Get all files currently on disk
        current_files = {}
        for root, dirs, files in os.walk(directory):
            if ".git" in dirs:
                dirs.remove(".git")
            if "node_modules" in dirs:
                dirs.remove("node_modules")
                
            for file in files:
                if Path(file).suffix not in self.tool.supported_languages:
                    continue
                    
                full_path = os.path.join(root, file)
                abs_path = os.path.abspath(full_path)
                current_files[abs_path] = os.path.getmtime(abs_path)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 1. Identify files to remove (in DB but not on disk)
            cursor.execute("SELECT id, path FROM files")
            existing_files = {row[1]: row[0] for row in cursor.fetchall()}
            
            to_remove = []
            for path, file_id in existing_files.items():
                if path not in current_files:
                    to_remove.append(file_id)
            
            if to_remove:
                placeholders = ','.join('?' * len(to_remove))
                cursor.execute(f"DELETE FROM symbols WHERE file_id IN ({placeholders})", to_remove)
                cursor.execute(f"DELETE FROM calls WHERE file_id IN ({placeholders})", to_remove)
                cursor.execute(f"DELETE FROM files WHERE id IN ({placeholders})", to_remove)

            # 2. Identify files to update/add
            for path, mtime in current_files.items():
                if path in existing_files:
                    # Check modification time
                    cursor.execute("SELECT last_modified FROM files WHERE id = ?", (existing_files[path],))
                    last_mod = cursor.fetchone()[0]
                    if mtime <= last_mod:
                        continue # Skip if unchanged
                    
                    # File changed: clear old data first
                    file_id = existing_files[path]
                    cursor.execute("DELETE FROM symbols WHERE file_id = ?", (file_id,))
                    cursor.execute("DELETE FROM calls WHERE file_id = ?", (file_id,))
                    cursor.execute("UPDATE files SET last_modified = ? WHERE id = ?", (mtime, file_id))
                else:
                    # New file
                    cursor.execute("INSERT INTO files (path, last_modified) VALUES (?, ?)", (path, mtime))
                    file_id = cursor.lastrowid
                
                # Scan content
                self._index_file(conn, file_id, path)

    def _index_file(self, conn, file_id: int, path: str):
        """Scan a single file and insert data into DB."""
        # Scan symbols
        res_sym = self.tool.scan_file(path)
        if res_sym and "symbols" in res_sym:
            for sym in res_sym["symbols"]:
                conn.execute(
                    "INSERT INTO symbols (name, kind, file_id, line) VALUES (?, ?, ?, ?)",
                    (sym["name"], sym["kind"], file_id, sym["line"])
                )
        
        # Scan calls
        res_call = self.tool.scan_calls(path)
        if res_call and "calls" in res_call:
            for call in res_call["calls"]:
                conn.execute(
                    "INSERT INTO calls (name, file_id, line) VALUES (?, ?, ?)",
                    (call["name"], file_id, call["line"])
                )

    def get_callers(self, symbol_name: str) -> List[Dict[str, Any]]:
        """Retrieve callers from index."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.name, f.path, c.line 
                FROM calls c 
                JOIN files f ON c.file_id = f.id 
                WHERE c.name = ?
            """, (symbol_name,))
            return [
                {"name": row[0], "file": row[1], "line": row[2]} 
                for row in cursor.fetchall()
            ]
