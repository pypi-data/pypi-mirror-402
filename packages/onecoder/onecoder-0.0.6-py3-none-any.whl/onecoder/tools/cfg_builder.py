
from pathlib import Path
from typing import Dict, Any

class CFGBuilder:
    def __init__(self, tool):
        self.tool = tool

    def generate(self, file_path: str, function_name: str) -> Dict[str, Any]:
        """Generate a simplified CFG for a function in Mermaid format."""
        
        # Re-use tools internal helpers via self.tool
        # But wait, accessing protected methods _get_parser need specific access or we duplicate logic?
        # Better: pass the parser and query or use public methods if available.
        # Actually, let's keep it simple: Standard standalone function or class that accepts necessary components.
        
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
            
            # Iterate to find exact function
            for node, name in captures:
                if name.endswith(".def"):
                    # check name
                    name_node = node.child_by_field_name('name')
                    if name_node:
                        func_name = content[name_node.start_byte:name_node.end_byte].decode("utf-8")
                        if func_name == function_name:
                            target_node = node
                            break
            
            if not target_node:
                return {"error": f"Function '{function_name}' not found"}

            # 2. Build CFG (Simplified)
            # We will use the complexity query to identify control flow structures
            comp_query = self.tool._get_query(lang_name, "complexity")
            
            # Basic Mermaid Graph construction
            # We track nodes and connections.
            # Node ID: "N" + node.id
            
            nodes = {} # id -> label
            
            start_id = f"N{target_node.id}"
            nodes[start_id] = f"Start: {function_name}"
            
            flow_captures = comp_query.captures(target_node)
            
            # Map node IDs to flow types
            flow_map = {n.id: tag for n, tag in flow_captures} # tag is @branch usually
            
            mermaid_lines = ["graph TD"]
            mermaid_lines.append(f"    {start_id}[\"Start: {function_name}\"]")
            
            sorted_flow = sorted([n for n, tag in flow_captures], key=lambda x: x.start_byte)
            
            for flow_node in sorted_flow:
                nid = f"N{flow_node.id}"
                node_text = content[flow_node.start_byte:flow_node.end_byte].decode("utf-8").split('\n')[0][:20] + "..."
                # clean text for mermaid label
                node_text = node_text.replace('"', "'").replace('[', '(').replace(']', ')')
                
                node_type = flow_node.type
                
                shape_start = "["
                shape_end = "]"
                if "if" in node_type or "while" in node_type:
                    shape_start = "{"
                    shape_end = "}"
                
                nodes[nid] = f"{shape_start}\"{node_type}: {node_text}\"{shape_end}"
                mermaid_lines.append(f"    {nid}{nodes[nid]}")
                
                # Heuristic parent linking
                curr = flow_node.parent
                parent_flow_id = start_id
                while curr and curr.id != target_node.id:
                    if curr.id in flow_map:
                        parent_flow_id = f"N{curr.id}"
                        break
                    curr = curr.parent
                
                mermaid_lines.append(f"    {parent_flow_id} --> {nid}")

            # Return the graph
            return {
                "file": file_path,
                "function": function_name,
                "mermaid": "\n".join(mermaid_lines)
            }

        except Exception as e:
            return {"file": file_path, "error": str(e)}
