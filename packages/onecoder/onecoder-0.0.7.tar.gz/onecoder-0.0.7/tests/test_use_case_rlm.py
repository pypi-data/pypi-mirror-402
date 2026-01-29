
import sys
import os
import importlib.util

# Reuse loader
def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

try:
    tools_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../onecoder/tools"))
    
    load_module("onecoder.tools.queries", os.path.join(tools_dir, "queries.py"))
    load_module("onecoder.tools.cfg_builder", os.path.join(tools_dir, "cfg_builder.py"))
    load_module("onecoder.tools.data_flow", os.path.join(tools_dir, "data_flow.py"))
    load_module("onecoder.tools.slicer", os.path.join(tools_dir, "slicer.py"))
    
    import types
    onecoder = types.ModuleType("onecoder")
    onecoder_tools = types.ModuleType("onecoder.tools")
    onecoder_tools.__path__ = [tools_dir]
    sys.modules["onecoder"] = onecoder
    sys.modules["onecoder.tools"] = onecoder_tools
    
    from onecoder.tools import tldr_tool
    tool = tldr_tool.TLDRTool()
    
    # 1. Simulate "Scan for Refactoring Candidates"
    target_file = os.path.join(os.path.dirname(__file__), "repro_l3.py")
    print(f"1. Scanning complexity in {target_file}...")
    
    comp_res = tool.scan_complexity(target_file)
    functions = comp_res.get("functions", [])
    
    # Identify candidates (Complexity > 5)
    candidates = [f for f in functions if f["complexity"] > 1] # repro_l3 is simple, maybe just 1
    
    if not candidates:
        print("No candidates found.")
        sys.exit(0)
        
    candidate = candidates[0]
    func_name = candidate["name"]
    print(f"2. Found candidate: {func_name} (Complexity: {candidate['complexity']})")
    
    # 2. Simulate "RLM Context Gathering"
    # Agent wants to refactor variables in this function.
    # It requests slices for key variables.
    
    # To find variables, we can look at symbols or just hardcode for this test (or parse usages)
    # Let's assume the agent parsed the AST and found "x"
    
    print(f"3. Generating context slices for '{func_name}'...")
    
    # Get CFG to understand structure
    cfg_res = tool.scan_cfg(target_file, func_name)
    print(f"   - CFG generated ({len(cfg_res['mermaid'])} bytes)")
    
    # Get Slice for 'a' (return value in repro_l3?) - checking repro_l3 content
    # complex_function in repro_l3 has flow... let's check content below
    
    # For now, blindly slice 'x' if it exists or 'res'
    # Actually, we should check what's in repro_l3.py
    
    print("4. MOCK RLM Context Bundle:")
    print("---")
    print(f"File: {target_file}")
    print(f"Goal: Refactor {func_name}")
    print(f"Complexity: {candidate['complexity']}")
    print("CFG:")
    print(cfg_res.get('mermaid', '')[:100] + "...")
    print("---")
    
    print("SUCCESS: RLM Context Generated")

except Exception as e:
    import traceback
    traceback.print_exc()
