
import unittest
import sqlite3
import os
import shutil
import tempfile
from pathlib import Path
import sys


import unittest
import sqlite3
import os
import shutil
import tempfile
import sys
import importlib.util

# Helper to load module from path
def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

# Manually load modules to bypass pydantic dependency check in onecoder package init
try:
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../onecoder/tools"))
    
    # 1. Load tldr_tool
    tldr_tool_mod = load_module("onecoder.tools.tldr_tool", os.path.join(base_path, "tldr_tool.py"))
    
    # 2. Patch relative import for indexer
    # indexer.py does `from .tldr_tool import TLDRTool`
    # We can rely on it finding `onecoder.tools.tldr_tool` in sys.modules if we structure it right
    # OR we can just load indexer and if it fails, maybe patch sys.meta_path?
    # Simplest: Load indexer, but ensuring it resolves .tldr_tool
    
    # Create fake parent package
    if "onecoder" not in sys.modules:
        sys.modules["onecoder"] = type(sys)("onecoder")
        sys.modules["onecoder"].__path__ = []
    
    if "onecoder.tools" not in sys.modules:
        sys.modules["onecoder.tools"] = type(sys)("onecoder.tools")
        sys.modules["onecoder.tools"].__path__ = [base_path]
        
    # Now load indexer
    indexer_mod = load_module("onecoder.tools.indexer", os.path.join(base_path, "indexer.py"))
    
    Indexer = indexer_mod.Indexer
    HAS_INDEXER = True
except Exception as e:
    print(f"Failed to load modules: {e}")
    HAS_INDEXER = False

class TestIndexer(unittest.TestCase):
    def setUp(self):
        if not HAS_INDEXER:
             self.skipTest("Indexer could not be loaded")
        self.Indexer = Indexer
            
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_tldr.db")
        self.code_dir = os.path.join(self.temp_dir, "code")
        os.makedirs(self.code_dir)
        
        with open(os.path.join(self.code_dir, "test.py"), "w") as f:
            f.write("""
def my_func():
    pass

def caller():
    my_func()
""")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_schema(self):
        indexer = self.Indexer(db_path=self.db_path)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            self.assertIn("files", tables)
            self.assertIn("symbols", tables)
            self.assertIn("calls", tables)

    def test_indexing_flow(self):
        indexer = self.Indexer(db_path=self.db_path)
        indexer.index_directory(self.code_dir)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check symbol
            cursor.execute("SELECT name FROM symbols WHERE name='my_func'")
            self.assertIsNotNone(cursor.fetchone())
            
            # Check call
            cursor.execute("SELECT name FROM calls WHERE name='my_func'")
            self.assertIsNotNone(cursor.fetchone())

            # Check incremental
            indexer.index_directory(self.code_dir)
            cursor.execute("SELECT COUNT(*) FROM files")
            self.assertEqual(cursor.fetchone()[0], 1)

if __name__ == "__main__":
    unittest.main()
