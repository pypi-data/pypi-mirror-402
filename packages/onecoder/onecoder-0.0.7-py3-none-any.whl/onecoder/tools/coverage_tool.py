"""
Coverage Tool for OneCoder Governance Review.

This module detects and parses test coverage reports from various formats:
- Lcov (JavaScript/TypeScript)
- Cobertura (Python, Java, etc.)
- Coverage.py JSON format
- pytest-cov output
"""

import os
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging


class CoverageScanner:
    """Scans for and parses test coverage reports."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.logger = logging.getLogger("onecoder.coverage")

    def detect_coverage_files(self) -> List[Dict[str, str]]:
        """
        Detect coverage files in the project.
        
        Returns:
            List of dicts with 'path' and 'format' keys.
        """
        coverage_files = []
        
        # Common coverage file patterns
        patterns = {
            "lcov.info": "lcov",
            "coverage/lcov.info": "lcov",
            "coverage.xml": "cobertura",
            "coverage/coverage.xml": "cobertura",
            ".coverage": "coverage.py",
            "coverage.json": "coverage.py-json",
            "htmlcov/index.html": "html",
        }
        
        for pattern, fmt in patterns.items():
            path = self.project_root / pattern
            if path.exists():
                coverage_files.append({"path": str(path), "format": fmt})
        
        return coverage_files

    def parse_lcov(self, lcov_path: str) -> Dict[str, Any]:
        """Parse LCOV format coverage file."""
        try:
            with open(lcov_path, "r") as f:
                content = f.read()
            
            files_coverage = {}
            current_file = None
            
            for line in content.split("\n"):
                line = line.strip()
                if line.startswith("SF:"):
                    current_file = line[3:]
                    files_coverage[current_file] = {
                        "lines_found": 0,
                        "lines_hit": 0,
                        "line_coverage": 0.0,
                    }
                elif line.startswith("LF:"):
                    if current_file:
                        files_coverage[current_file]["lines_found"] = int(line[3:])
                elif line.startswith("LH:"):
                    if current_file:
                        files_coverage[current_file]["lines_hit"] = int(line[3:])
                elif line == "end_of_record":
                    if current_file and files_coverage[current_file]["lines_found"] > 0:
                        files_coverage[current_file]["line_coverage"] = (
                            files_coverage[current_file]["lines_hit"]
                            / files_coverage[current_file]["lines_found"]
                        ) * 100
                    current_file = None
            
            total_lines = sum(f["lines_found"] for f in files_coverage.values())
            total_hit = sum(f["lines_hit"] for f in files_coverage.values())
            overall_coverage = (total_hit / total_lines * 100) if total_lines > 0 else 0.0
            
            return {
                "format": "lcov",
                "overall_coverage": overall_coverage,
                "files": files_coverage,
                "total_lines": total_lines,
                "total_hit": total_hit,
            }
        except Exception as e:
            self.logger.error(f"Error parsing LCOV file: {e}")
            return {"error": str(e)}

    def parse_cobertura(self, xml_path: str) -> Dict[str, Any]:
        """Parse Cobertura XML format coverage file."""
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            files_coverage = {}
            
            for package in root.findall(".//package"):
                for cls in package.findall(".//class"):
                    filename = cls.get("filename")
                    lines = cls.findall(".//line")
                    
                    lines_found = len(lines)
                    lines_hit = sum(1 for line in lines if int(line.get("hits", 0)) > 0)
                    
                    files_coverage[filename] = {
                        "lines_found": lines_found,
                        "lines_hit": lines_hit,
                        "line_coverage": (lines_hit / lines_found * 100) if lines_found > 0 else 0.0,
                    }
            
            # Get overall coverage from root
            line_rate = float(root.get("line-rate", 0))
            overall_coverage = line_rate * 100
            
            total_lines = sum(f["lines_found"] for f in files_coverage.values())
            total_hit = sum(f["lines_hit"] for f in files_coverage.values())
            
            return {
                "format": "cobertura",
                "overall_coverage": overall_coverage,
                "files": files_coverage,
                "total_lines": total_lines,
                "total_hit": total_hit,
            }
        except Exception as e:
            self.logger.error(f"Error parsing Cobertura XML: {e}")
            return {"error": str(e)}

    def parse_coverage_py_json(self, json_path: str) -> Dict[str, Any]:
        """Parse coverage.py JSON format."""
        try:
            with open(json_path, "r") as f:
                data = json.load(f)
            
            files_coverage = {}
            
            for filename, file_data in data.get("files", {}).items():
                summary = file_data.get("summary", {})
                files_coverage[filename] = {
                    "lines_found": summary.get("num_statements", 0),
                    "lines_hit": summary.get("covered_lines", 0),
                    "line_coverage": summary.get("percent_covered", 0.0),
                }
            
            totals = data.get("totals", {})
            overall_coverage = totals.get("percent_covered", 0.0)
            
            return {
                "format": "coverage.py-json",
                "overall_coverage": overall_coverage,
                "files": files_coverage,
                "total_lines": totals.get("num_statements", 0),
                "total_hit": totals.get("covered_lines", 0),
            }
        except Exception as e:
            self.logger.error(f"Error parsing coverage.py JSON: {e}")
            return {"error": str(e)}

    def scan(self) -> Dict[str, Any]:
        """
        Scan for coverage and return a unified report.
        
        Returns:
            Dict with coverage summary and file-level details.
        """
        detected_files = self.detect_coverage_files()
        
        if not detected_files:
            return {
                "status": "no_coverage",
                "message": "No coverage files detected. Run tests with coverage enabled.",
            }
        
        # Parse the first detected coverage file
        coverage_file = detected_files[0]
        fmt = coverage_file["format"]
        path = coverage_file["path"]
        
        if fmt == "lcov":
            result = self.parse_lcov(path)
        elif fmt == "cobertura":
            result = self.parse_cobertura(path)
        elif fmt == "coverage.py-json":
            result = self.parse_coverage_py_json(path)
        else:
            return {
                "status": "unsupported_format",
                "message": f"Coverage format '{fmt}' is not yet supported.",
            }
        
        if "error" in result:
            return {
                "status": "parse_error",
                "message": result["error"],
            }
        
        # Assess coverage quality
        overall = result["overall_coverage"]
        status = "excellent" if overall >= 80 else "good" if overall >= 60 else "poor"
        
        return {
            "status": status,
            "overall_coverage": overall,
            "total_lines": result["total_lines"],
            "total_hit": result["total_hit"],
            "files": result["files"],
            "format": result["format"],
        }


def coverage_scanner_tool(project_root: str = ".") -> str:
    """
    Tool function for ADK agents to scan test coverage.
    
    Args:
        project_root: Path to the project root.
    
    Returns:
        JSON string with coverage report.
    """
    scanner = CoverageScanner(project_root)
    result = scanner.scan()
    return json.dumps(result, indent=2)
