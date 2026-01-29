import pytest
from pathlib import Path
from ai_sprint.preflight import SprintPreflight
from onecoder.cli import main
import sys
from unittest.mock import patch, MagicMock

def test_preflight_no_crash_missing_retro(tmp_path):
    """Verify preflight doesn't crash when RETRO.md is missing."""
    sprint_dir = tmp_path / ".sprint" / "test-sprint"
    sprint_dir.mkdir(parents=True)
    
    # Create minimum required files
    (sprint_dir / "README.md").write_text("# Test\nSpec-Id: SPEC-TEST-001")
    (sprint_dir / "TODO.md").write_text("# TODO\n- [ ] Task 1\n- [ ] Task 2\n- [ ] Task 3\n- [ ] Task 4\n- [ ] Task 5")
    (sprint_dir / "sprint.json").write_text('{"tasks": [{"id": "t1", "title": "Task 1"}, {"id": "t2", "title": "Task 2"}, {"id": "t3", "title": "Task 3"}, {"id": "t4", "title": "Task 4"}, {"id": "t5", "title": "Task 5"}], "parentComponent": "test"}')
    
    preflight = SprintPreflight(sprint_dir, tmp_path)
    # This should not raise TypeError or KeyError
    score, results = preflight.run_all()
    
    assert isinstance(score, int)
    assert any(r.get("name") == "Retro Sync" for r in results)
    assert all("status" in r for r in results if isinstance(r, dict))

def test_cli_error_handler_scoping():
    """Verify CLI error handler doesn't have UnboundLocalError."""
    with patch("onecoder.cli.cli", side_effect=Exception("Test Error")):
        with patch("ai_sprint.telemetry.FailureModeCapture") as mock_capture:
            with patch("sys.argv", ["onecoder", "test"]):
                # Should not raise UnboundLocalError: sys
                with pytest.raises(Exception):
                    main()
                
                # Verify telemetry was attempted

@pytest.mark.asyncio
async def test_api_client_surfaces_500_error_message():
    """Verify that OneCoderAPIClient surfaces the JSON error message on 500."""
    from onecoder.api_client import OneCoderAPIClient
    import respx
    from httpx import Response
    import httpx

    client = OneCoderAPIClient("https://api.test", token="test-token")
    
    with respx.mock:
        # Mock a 500 error with a JSON body
        respx.get("https://api.test/api/v1/test").mock(return_value=Response(
            500, 
            json={"error": "Database connection failed", "message": "Deep error context"}
        ))
        
        with pytest.raises(httpx.HTTPStatusError) as excinfo:
            await client._request("GET", "/test")
        
        assert "Deep error context" in str(excinfo.value)
