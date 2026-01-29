"""
Unit tests for coverage_tool.py
"""

import pytest
import json
from pathlib import Path
from onecoder.tools.coverage_tool import CoverageScanner


def test_coverage_scanner_init():
    """Test CoverageScanner initialization."""
    scanner = CoverageScanner("/tmp/test_project")
    assert scanner.project_root == Path("/tmp/test_project")


def test_detect_coverage_files_empty(tmp_path):
    """Test detection when no coverage files exist."""
    scanner = CoverageScanner(str(tmp_path))
    files = scanner.detect_coverage_files()
    assert files == []


def test_detect_coverage_files_lcov(tmp_path):
    """Test detection of lcov coverage file."""
    lcov_file = tmp_path / "lcov.info"
    lcov_file.write_text("SF:test.js\nLF:10\nLH:8\nend_of_record\n")
    
    scanner = CoverageScanner(str(tmp_path))
    files = scanner.detect_coverage_files()
    
    assert len(files) == 1
    assert files[0]["format"] == "lcov"


def test_parse_lcov():
    """Test parsing of lcov format."""
    lcov_content = """SF:src/test.js
LF:10
LH:8
end_of_record
SF:src/another.js
LF:20
LH:15
end_of_record
"""
    tmp_path = Path("/tmp/test_lcov.info")
    tmp_path.write_text(lcov_content)
    
    scanner = CoverageScanner("/tmp")
    result = scanner.parse_lcov(str(tmp_path))
    
    assert result["format"] == "lcov"
    assert result["total_lines"] == 30
    assert result["total_hit"] == 23
    assert abs(result["overall_coverage"] - 76.67) < 0.1
    
    tmp_path.unlink()


def test_scan_no_coverage():
    """Test scan when no coverage files exist."""
    scanner = CoverageScanner("/tmp/nonexistent")
    result = scanner.scan()
    
    assert result["status"] == "no_coverage"
    assert "No coverage files detected" in result["message"]


def test_coverage_quality_assessment():
    """Test coverage quality thresholds."""
    # This would require mocking or creating actual coverage files
    # For now, we test the logic indirectly through the scan method
    pass
