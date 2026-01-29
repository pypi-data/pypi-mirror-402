import os
import glob
from pathlib import Path
from typing import List, Dict, Any, Optional
from .queries import QUERIES

try:
    import tree_sitter_languages
    HAS_TREE_SITTER = True
except ImportError:
    HAS_TREE_SITTER = False

class TLDRTool:
    """
    TLDR Tool (Token-Efficient Lightweight Deep Retrieval) implementation.
    This tool extracts structure and symbols from code using tree-sitter.
    """

    def __init__(self):
        self.parsers = {}
        self.queries = {}
        self.supported_languages = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".jsx": "javascript",
            ".go": "go",
            ".rs": "rust",
            ".java": "java",
            ".c": "c",
            ".cpp": "cpp",
        }

    def _get_parser(self, lang_name: str):
        """Get or create a parser for the given language."""
        if not HAS_TREE_SITTER:
            raise ImportError("tree-sitter-languages is not installed.")
        if lang_name not in self.parsers:
            parser = tree_sitter_languages.get_parser(lang_name)
            self.parsers[lang_name] = parser
        return self.parsers[lang_name]

    def _get_query(self, lang_name: str, query_type: str = "symbols"):
        """Get the tree-sitter query for extracting symbols."""
        key = (lang_name, query_type)
        if key in self.queries:
            return self.queries[key]

        query_str = QUERIES.get(query_type, {}).get(lang_name, "")

        if query_str:
            if not HAS_TREE_SITTER:
                 raise ImportError("tree-sitter-languages is not installed.")
            language = tree_sitter_languages.get_language(lang_name)
            query = language.query(query_str)
            self.queries[key] = query
            return query
        return None

    def scan_file(self, file_path: str) -> Dict[str, Any]:
        """Scan a single file and extract symbols."""
        path = Path(file_path)
        ext = path.suffix
        if ext not in self.supported_languages:
            return {}

        lang_name = self.supported_languages[ext]
        try:
            parser = self._get_parser(lang_name)
            with open(file_path, "rb") as f:
                content = f.read()

            tree = parser.parse(content)
            query = self._get_query(lang_name, "symbols")

            symbols = []
            if query:
                captures = query.captures(tree.root_node)
                
                # First pass: Map definition nodes to their names
                def_names = {}
                definitions = []

                for node, capture_name in captures:
                    if capture_name.endswith(".def"):
                        definitions.append((node, capture_name))
                    elif capture_name.endswith(".name") or capture_name == "impl.type":
                        parent = node.parent
                        if parent:
                            def_names[parent.id] = content[node.start_byte:node.end_byte].decode("utf-8")
                
                seen_ids = set()
                for node, capture_name in definitions:
                    if node.id in seen_ids:
                        continue
                    seen_ids.add(node.id)

                    name = def_names.get(node.id, "<anonymous>")
                    kind_tag = capture_name.split(".")[0]
                    line = node.start_point[0] + 1
                    
                    symbols.append({
                        "name": name,
                        "kind": kind_tag,
                        "line": line,
                        "file": file_path
                    })

            return {
                "file": file_path,
                "language": lang_name,
                "symbols": symbols
            }
        except Exception as e:
            return {"file": file_path, "error": str(e)}

    def scan_calls(self, file_path: str) -> Dict[str, Any]:
        """Scan a single file and extract function calls."""
        path = Path(file_path)
        ext = path.suffix
        if ext not in self.supported_languages:
            return {}

        lang_name = self.supported_languages[ext]
        try:
            parser = self._get_parser(lang_name)
            with open(file_path, "rb") as f:
                content = f.read()

            tree = parser.parse(content)
            query = self._get_query(lang_name, "calls")

            calls = []
            if query:
                captures = query.captures(tree.root_node)
                for node, capture_name in captures:
                    line = node.start_point[0] + 1
                    name = content[node.start_byte:node.end_byte].decode("utf-8")
                    calls.append({
                        "name": name,
                        "line": line,
                        "file": file_path
                    })

            return {
                "file": file_path,
                "calls": calls
            }
        except Exception as e:
            return {"file": file_path, "error": str(e)}

    def scan_complexity(self, file_path: str) -> Dict[str, Any]:
        """Scan a file and estimate cyclomatic complexity for functions."""
        path = Path(file_path)
        ext = path.suffix
        if ext not in self.supported_languages:
            return {}

        lang_name = self.supported_languages[ext]
        try:
            parser = self._get_parser(lang_name)
            with open(file_path, "rb") as f:
                content = f.read()

            tree = parser.parse(content)

            sym_query = self._get_query(lang_name, "symbols")
            comp_query = self._get_query(lang_name, "complexity")

            if not sym_query or not comp_query:
                return {}

            sym_captures = sym_query.captures(tree.root_node)
            results = []
            definitions = [node for node, name in sym_captures if name.endswith(".def")]

            for def_node in definitions:
                func_name = "unknown"
                name_node = def_node.child_by_field_name('name')
                if name_node:
                    func_name = content[name_node.start_byte:name_node.end_byte].decode("utf-8")

                branches = comp_query.captures(def_node)
                complexity = 1 + len(branches)

                results.append({
                    "name": func_name,
                    "complexity": complexity,
                    "line": def_node.start_point[0] + 1,
                    "end_line": def_node.end_point[0] + 1
                })

            return {
                "file": file_path,
                "functions": results
            }

        except Exception as e:
            return {"file": file_path, "error": str(e)}


    def scan_directory(self, directory: str, recursive: bool = True) -> List[Dict[str, Any]]:
        """Scan a directory for symbols."""
        results = []
        pattern = "**/*" if recursive else "*"
        for file_path in glob.glob(os.path.join(directory, pattern), recursive=recursive):
            if os.path.isfile(file_path):
                 res = self.scan_file(file_path)
                 if res:
                     if "error" in res or ("symbols" in res and res["symbols"]):
                         results.append(res)
        return results

    def find_callers(self, directory: str, symbol_name: str) -> List[Dict[str, Any]]:
        """Find where a symbol is called."""
        results = []
        pattern = "**/*"
        for file_path in glob.glob(os.path.join(directory, pattern), recursive=True):
            if os.path.isfile(file_path):
                res = self.scan_calls(file_path)
                if res and "calls" in res:
                    for call in res["calls"]:
                        if call["name"] == symbol_name:
                            results.append(call)
        return results

    def analyze_complexity(self, directory: str) -> List[Dict[str, Any]]:
        """Analyze complexity for all files in directory."""
        results = []
        pattern = "**/*"
        for file_path in glob.glob(os.path.join(directory, pattern), recursive=True):
            if os.path.isfile(file_path):
                res = self.scan_complexity(file_path)
                if res and "functions" in res and res["functions"]:
                    results.append(res)
        return results

    def search(self, directory: str, query: str) -> List[Dict[str, Any]]:
        """Search for symbols matching the query."""
        all_symbols = self.scan_directory(directory)
        matches = []
        for file_res in all_symbols:
            for symbol in file_res.get("symbols", []):
                if query.lower() in symbol["name"].lower():
                    matches.append(symbol)
        return matches

    def scan_cfg(self, file_path: str, function_name: str) -> Dict[str, Any]:
        """Generate a simplified CFG for a function in Mermaid format."""
        from .cfg_builder import CFGBuilder
        return CFGBuilder(self).generate(file_path, function_name)

    def scan_data_flow(self, file_path: str, function_name: str, variable_name: str) -> Dict[str, Any]:
        """Track data flow for a variable in a function."""
        from .data_flow import DataFlowAnalyzer
        return DataFlowAnalyzer(self).analyze(file_path, function_name, variable_name)

    def scan_slice(self, file_path: str, function_name: str, variable_name: str) -> Dict[str, Any]:
        """Extract an executable subset (slice) relevant to the variable."""
        from .slicer import Slicer
        return Slicer(self).slice(file_path, function_name, variable_name)

    def calculate_debt_score(self, directory: str) -> Dict[str, Any]:
        """Aggregate complexity metrics to calculate a project-wide debt score."""
        complexity_results = self.analyze_complexity(directory)
        total_complexity = 0
        high_complexity_funcs = []
        file_count = 0
        
        for file_res in complexity_results:
            file_count += 1
            for func in file_res.get("functions", []):
                total_complexity += func["complexity"]
                if func["complexity"] > 10:
                    high_complexity_funcs.append({
                        "file": file_res["file"],
                        "name": func["name"],
                        "complexity": func["complexity"]
                    })
        
        avg_complexity = total_complexity / file_count if file_count > 0 else 0
        # Debt score: Total complexity + (penalty for high complexity)
        debt_score = total_complexity + (len(high_complexity_funcs) * 10)
        
        return {
            "total_complexity": total_complexity,
            "average_complexity": avg_complexity,
            "high_complexity_functions_count": len(high_complexity_funcs),
            "high_complexity_functions": high_complexity_funcs,
            "debt_score": debt_score,
            "file_count": file_count
        }
