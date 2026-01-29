import pytest
from pathlib import Path
from typing import Dict, Any
from ai_sprint.sync_engine import sync_tasks_from_todo
from ai_sprint.state import SprintStateManager
import os
import shutil

@pytest.fixture
def temp_sprint_dir(tmp_path):
    sprint_dir = tmp_path / ".sprint" / "test-sprint"
    sprint_dir.mkdir(parents=True)
    return sprint_dir

def test_sync_tasks_from_todo_cleaning(temp_sprint_dir):
    """Verify that recursive IDs are stripped and format is standardized."""
    todo_file = temp_sprint_dir / "TODO.md"
    # Messy content with recursive IDs in different formats
    content = """# Tasks
## Implementation
- [ ] Task Title (task-001) (task-001) <!-- id: task-001 -->
- [/] Active Task (task-002) <!-- id: task-002 -->
- [x] Done Task (task-003) (task-003)
"""
    todo_file.write_text(content)
    
    state = {"tasks": []}
    new_state = sync_tasks_from_todo(temp_sprint_dir, state)
    
    # Check state titles are clean
    assert new_state["tasks"][0]["title"] == "Task Title"
    assert new_state["tasks"][1]["title"] == "Active Task"
    assert new_state["tasks"][2]["title"] == "Done Task"
    
    # Check TODO.md titles are clean and standardized
    cleaned_content = todo_file.read_text()
    assert "Task Title <!-- id: task-001 -->" in cleaned_content
    assert "(task-001)" not in cleaned_content
    assert "Active Task <!-- id: task-002 -->" in cleaned_content
    assert "Done Task <!-- id: task-003 -->" in cleaned_content

def test_sync_tasks_from_todo_idempotency(temp_sprint_dir):
    """Verify that sync_tasks_from_todo doesn't write if no change."""
    todo_file = temp_sprint_dir / "TODO.md"
    content = "# Tasks\n- [ ] Normal Task <!-- id: task-001 -->\n"
    todo_file.write_text(content)
    
    # Record mtime
    mtime_before = todo_file.stat().st_mtime_ns
    
    state = {"tasks": [{"id": "task-001", "title": "Normal Task", "status": "todo"}]}
    sync_tasks_from_todo(temp_sprint_dir, state)
    
    # Check if mtime changed (it shouldn't)
    assert todo_file.stat().st_mtime_ns == mtime_before

def test_sync_todo_from_state_standardization(temp_sprint_dir):
    """Verify that state.py correctly generates TODO.md with HTML comments."""
    state_manager = SprintStateManager(temp_sprint_dir)
    state = state_manager.create_initial_state("test-sprint")
    state["tasks"] = [
        {"id": "task-001", "title": "State Task", "status": "todo"}
    ]
    state_manager.save(state)
    state_manager.sync_todo_from_state()
    
    todo_file = temp_sprint_dir / "TODO.md"
    assert todo_file.exists()
    content = todo_file.read_text()
    assert "State Task <!-- id: task-001 -->" in content
    assert "(task-001)" not in content

def test_sync_todo_from_state_idempotency(temp_sprint_dir):
    """Verify that sync_todo_from_state doesn't write if no change."""
    state_manager = SprintStateManager(temp_sprint_dir)
    state = state_manager.create_initial_state("test-sprint")
    state["tasks"] = [{"id": "task-001", "title": "Steady State", "status": "todo"}]
    state_manager.save(state)
    
    todo_file = temp_sprint_dir / "TODO.md"
    state_manager.sync_todo_from_state()
    
    mtime_before = todo_file.stat().st_mtime_ns
    
    # Run again
    state_manager.sync_todo_from_state()
    
    assert todo_file.stat().st_mtime_ns == mtime_before

