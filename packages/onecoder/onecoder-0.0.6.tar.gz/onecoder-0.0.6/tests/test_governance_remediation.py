import pytest
import subprocess
import os
from pathlib import Path
import sys
from pathlib import Path

# Add the package root to sys.path
package_root = Path(__file__).parent.parent / "sprint-cli" / "src"
sys.path.append(str(package_root))

from ai_sprint.preflight import SprintPreflight

@pytest.fixture
def repo_with_large_file(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
    
    # Create a 500-line file
    large_file = repo / "large_file.py"
    large_file.write_text("\n" * 500)
    subprocess.run(["git", "add", "large_file.py"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit with large file"], cwd=repo, check=True)
    
    sprint_dir = repo / ".sprint" / "sprint-001"
    sprint_dir.mkdir(parents=True)
    sprint_json = {
        "$schema": "https://onecoder.dev/schemas/sprint.json",
        "version": "1.0.0",
        "sprintId": "sprint-001",
        "name": "sprint-001",
        "status": {
            "phase": "implementation",
            "state": "active",
            "message": None
        },
        "metadata": {
            "createdAt": "2026-01-10T00:00:00.000000",
            "updatedAt": "2026-01-10T00:00:00.000000",
            "createdBy": None,
            "parentComponent": "test",
            "gitBranch": None,
            "labels": []
        },
        "goals": {
            "primary": "Test sprint",
            "secondary": []
        },
        "tasks": [
            {"id": "task-001", "title": "Task 1", "status": "todo", "type": "implementation", "priority": "medium", "startedAt": None, "completedAt": None},
            {"id": "task-002", "title": "Task 2", "status": "todo", "type": "implementation", "priority": "medium", "startedAt": None, "completedAt": None}
        ],
        "artifacts": {
            "walkthrough": None,
            "media": []
        },
        "git": {
            "branch": None,
            "lastCommit": None,
            "hasUncommittedChanges": False
        },
        "hooks": {
            "onInit": [],
            "onTaskStart": [],
            "onTaskComplete": [],
            "onSprintClose": []
        }
    }
    import json
    (sprint_dir / "sprint.json").write_text(json.dumps(sprint_json))
    (sprint_dir / "README.md").write_text("# Sprint 001\nSpec-Id: SPEC-XXX-01")
    (sprint_dir / "TODO.md").write_text("# TODO\n- [ ] Task 1")
    
    return repo, sprint_dir

def test_no_regression_policy_pass(repo_with_large_file):
    repo, sprint_dir = repo_with_large_file
    preflight = SprintPreflight(sprint_dir, repo)
    
    # Run preflight on the large file - it should pass because it's not growing
    score, results = preflight.run_all(files=["large_file.py"])
    loc_check = next(r for r in results if r["name"] == "LOC Limit Enforcement")
    assert loc_check["status"] == "passed"

def test_no_regression_policy_fail(repo_with_large_file):
    repo, sprint_dir = repo_with_large_file
    
    # Increase the size of the large file
    large_file = repo / "large_file.py"
    large_file.write_text("\n" * 510)
    
    preflight = SprintPreflight(sprint_dir, repo)
    score, results = preflight.run_all(files=["large_file.py"])
    loc_check = next(r for r in results if r["name"] == "LOC Limit Enforcement")
    assert loc_check["status"] == "failed"
    assert "large_file.py (510 lines)" in loc_check["message"]

def test_secret_scanning_placeholders(repo_with_large_file):
    repo, sprint_dir = repo_with_large_file
    doc_file = repo / "DOCS.md"
    doc_file.write_text("Use key: sk-ant-api03-xxxxxxxxxxxx")
    
    preflight = SprintPreflight(sprint_dir, repo)
    score, results = preflight.run_all(files=["DOCS.md"])
    secret_check = next(r for r in results if r["name"] == "Secret Scanning")
    assert secret_check["status"] == "passed"

def test_secret_scanning_real_key(repo_with_large_file):
    repo, sprint_dir = repo_with_large_file
    secret_file = repo / "secrets.env"
    # A realistic looking high-entropy key
    secret_file.write_text("ANTHROPIC_KEY=sk-ant-api03-a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6")
    
    preflight = SprintPreflight(sprint_dir, repo)
    score, results = preflight.run_all(files=["secrets.env"])
    secret_check = next(r for r in results if r["name"] == "Secret Scanning")
    assert secret_check["status"] == "failed"

def test_staged_mode(repo_with_large_file):
    repo, sprint_dir = repo_with_large_file
    
    # Create a new file but don't stage it
    unstaged_file = repo / "unstaged.py"
    unstaged_file.write_text("\n" * 500)
    
    preflight = SprintPreflight(sprint_dir, repo)
    # Check staged mode - it should pass because unstaged.py is not staged
    score, results = preflight.run_all(staged=True)
    loc_check = next(r for r in results if r["name"] == "LOC Limit Enforcement")
    assert loc_check["status"] == "passed"
    
    # Stage it
    subprocess.run(["git", "add", "unstaged.py"], cwd=repo, check=True)
    score, results = preflight.run_all(staged=True)
    loc_check = next(r for r in results if r["name"] == "LOC Limit Enforcement")
    assert loc_check["status"] == "failed"

def test_archive_ignored(repo_with_large_file):
    repo, sprint_dir = repo_with_large_file
    archive_dir = repo / "archive"
    archive_dir.mkdir()
    legacy_file = archive_dir / "legacy.py"
    legacy_file.write_text("\n" * 500)
    subprocess.run(["git", "add", "archive/legacy.py"], cwd=repo, check=True)
    
    preflight = SprintPreflight(sprint_dir, repo)
    # Global check should ignore archive/
    score, results = preflight.run_all()
    loc_check = next(r for r in results if r["name"] == "LOC Limit Enforcement")
    assert loc_check["status"] == "passed"
