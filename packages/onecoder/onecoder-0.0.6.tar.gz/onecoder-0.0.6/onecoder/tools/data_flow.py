
from pathlib import Path
from typing import Dict, Any

class DataFlowAnalyzer:
    def __init__(self, tool):
        self.tool = tool

    def analyze(self, file_path: str, function_name: str, variable_name: str) -> Dict[str, Any]:
        """Track data flow for a variable in a function."""
        path = Path(file_path)
        ext = path.suffix
        if ext not in self.tool.supported_languages:
            return {"error": "Unsupported language"}

        lang_name = self.tool.supported_languages[ext]
        try:
            parser = self.tool._get_parser(lang_name)
            with open(file_path, "rb") as f:
                content = f.read()

            tree = parser.parse(content)
            
            # 1. Find the function definition
            sym_query = self.tool._get_query(lang_name, "symbols")
            if not sym_query:
                return {"error": "No symbol query"}
                
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
            
            if not target_node:
                return {"error": f"Function '{function_name}' not found"}

            # 2. Find all usages of variable
            usages = []
            
            # Naive recursive walk for identifiers
            def walk(n):
                if n.type == 'identifier':
                    name = content[n.start_byte:n.end_byte].decode("utf-8")
                    if name == variable_name:
                        # determine line content
                        line_no = n.start_point[0] + 1
                        line_content = content.splitlines()[n.start_point[0]].decode('utf-8').strip()
                        usages.append({
                            "line": line_no,
                            "content": line_content,
                            "type": "usage"
                        })
                for child in n.children:
                    walk(child)
            
            walk(target_node)
            
            return {
                "file": file_path,
                "function": function_name,
                "variable": variable_name,
                "usages": usages
            }

        except Exception as e:
            return {"file": file_path, "error": str(e)}
