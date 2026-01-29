
import re
from pathlib import Path
from typing import Dict, Any, List, Set

class GhostMapper:
    def __init__(self, tool):
        self.tool = tool

    def generate_map(self, spec_path: str, code_root: str) -> Dict[str, Any]:
        """
        Compare SPECIFICATION.md terms with codebase symbols.
        Returns a map of {term: {found: bool, locations: []}}
        """
        spec_terms = self._extract_spec_terms(spec_path)
        
        # We want to find if these terms exist as symbols in the codebase
        # We can do a mass scan or just search. 
        # Search is O(N*M), identifying all symbols first is O(N).
        # Let's Scan the directory first to get all symbols.
        
        print(f"[GhostMap] Scanning codebase at {code_root}...")
        all_files = self.tool.scan_directory(code_root, recursive=True)
        
        # Build symbol set for fast lookup
        # We map symbol_name -> list of locations
        code_symbols: Dict[str, List[str]] = {}
        
        for f in all_files:
            for s in f.get("symbols", []):
                name = s["name"]
                if name not in code_symbols:
                    code_symbols[name] = []
                code_symbols[name].append(f"{f['file']}:{s['line']}")
                
        # Compare
        results = {}
        
        print(f"[GhostMap] Verifying {len(spec_terms)} terms against {len(code_symbols)} symbols...")
        
        for term in spec_terms:
            # Exact match? Case insensitive? Partial?
            # Terms might be "onecoder task refine" -> likely not a symbol name.
            # Terms might be "scan_cfg" -> yes.
            # Terms might be "TLDRTool" -> yes.
            
            # Start with exact match logic, maybe fuzzy later.
            # Clean term (remove arguments/brackets)
            clean_term = term.split('(')[0].strip()
            
            found = False
            locations = []
            
            # Check exact match
            if clean_term in code_symbols:
                found = True
                locations = code_symbols[clean_term]
            else:
                # Check if it's a command like "onecoder task refine"
                # This won't be a symbol name (function names involve underscores).
                # Convert "task refine" to "task_refine"? no.
                pass
            
            results[term] = {
                "found": found,
                "locations": locations
            }
            
        return results

    def _extract_spec_terms(self, spec_path: str) -> Set[str]:
        """Extract code-like terms from markdown (backticks)."""
        terms = set()
        try:
            with open(spec_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Regex for backticks `...`
            matches = re.findall(r'`([^`]+)`', content)
            for m in matches:
                # Filter out obvious non-code or very short items
                if len(m) < 4: continue
                if " " in m and len(m.split()) > 3: continue # Sentences in backticks
                
                terms.add(m)
        except Exception as e:
            print(f"[GhostMap] Error reading spec: {e}")
            
        return terms
