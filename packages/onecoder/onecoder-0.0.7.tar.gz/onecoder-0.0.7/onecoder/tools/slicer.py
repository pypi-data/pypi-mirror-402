
from pathlib import Path
from typing import Dict, Any, List, Set
# We might need to import CFGBuilder logic or re-implement similar traversal
# Ideally we reuse the tool's methods to get the tree

class Slicer:
    def __init__(self, tool):
        self.tool = tool

    def slice(self, file_path: str, function_name: str, variable_name: str) -> Dict[str, Any]:
        """Extract an executable subset (slice) relevant to the variable."""
        
        # 1. Get Variable Usages (Data Flow)
        # We can reuse scan_data_flow logic or call it if exposed
        # Let's call the public method if possible, or just re-import the analyzer
        
        from .data_flow import DataFlowAnalyzer
        df_res = DataFlowAnalyzer(self.tool).analyze(file_path, function_name, variable_name)
        
        if "error" in df_res:
            return df_res
            
        relevant_lines: Set[int] = set()
        for u in df_res.get("usages", []):
            relevant_lines.add(u["line"])
            
        # 2. Get Control Dependencies
        # For every line in relevant_lines, find its parent control structures (if/while/etc)
        # We need the tree for this.
        
        path = Path(file_path)
        ext = path.suffix
        lang_name = self.tool.supported_languages.get(ext)
        if not lang_name:
             return {"error": "Unsupported"}

        try:
            parser = self.tool._get_parser(lang_name)
            with open(file_path, "rb") as f:
                content = f.read()
            tree = parser.parse(content)
            
            # Re-find structure to map lines to nodes
            # Simplest way: Traverse tree, if node covers a relevant line, check its type. 
            # If it's a control structure, add its header line to relevant_lines.
            
            # Complexity query gives us branches.
            comp_query = self.tool._get_query(lang_name, "complexity")
            if comp_query:
                # Find the function node first to limit scope
                sym_query = self.tool._get_query(lang_name, "symbols")
                captures = sym_query.captures(tree.root_node)
                target_node = None
                for node, name in captures:
                    if name.endswith(".def"):
                        name_node = node.child_by_field_name('name')
                        if name_node:
                            func_name = content[name_node.start_byte:name_node.end_byte].decode("utf-8")
                            if func_name == function_name:
                                target_node = node
                                break
                
                if target_node:
                    branches = comp_query.captures(target_node)
                    # branches is list of (node, name)
                    
                    # For each relevant line, check if it is inside any branch
                    # If so, add the branch start line
                    
                    # Iterative approach to fixed point? 
                    # One pass is enough for direct control dependency.
                    
                    added_new = True
                    while added_new:
                        added_new = False
                        current_lines = list(relevant_lines)
                        
                        for branch_node, _ in branches:
                            b_start = branch_node.start_point[0] + 1
                            b_end = branch_node.end_point[0] + 1
                            
                            if b_start in relevant_lines:
                                continue # Already added
                                
                            # Check if branch contains any relevant line
                            contains_relevant = False
                            for line in current_lines:
                                if b_start < line <= b_end:
                                    contains_relevant = True
                                    break
                            
                            if contains_relevant:
                                relevant_lines.add(b_start)
                                added_new = True
            
            # 3. Format Output
            # Re-read lines from code
            lines = content.splitlines()
            slice_code = []
            sorted_lines = sorted(list(relevant_lines))
            
            for ln in sorted_lines:
                if 0 <= ln - 1 < len(lines):
                    slice_code.append(f"{ln}: {lines[ln-1].decode('utf-8')}")
            
            return {
                "file": file_path,
                "function": function_name,
                "variable": variable_name,
                "slice": slice_code
            }

        except Exception as e:
            return {"file": file_path, "error": str(e)}
