from typing import List, Dict, Any, Optional
import os
import json
from pathlib import Path
from ..issues import IssueManager
from ..api_client import OneCoderAPIClient

class GitHubIssueSync:
    """Service to sync local issues with GitHub/API, filtering for unresolved ones."""
    
    def __init__(self, client: OneCoderAPIClient, project_id: str):
        self.client = client
        self.project_id = project_id
        self.manager = IssueManager()

    async def sync_unresolved(self) -> Dict[str, Any]:
        """Sync local issues that are not resolved."""
        issues_dir = self.manager.issues_dir
        if not issues_dir.exists():
            return {"synced": 0, "skipped": 0}

        unresolved_issues = []
        skipped_count = 0
        
        for item in issues_dir.iterdir():
            if item.is_file() and item.suffix == ".md" and item.name != "README.md":
                content = item.read_text()
                # Parse issue info
                issue_data = self.manager._parse_issue(item.stem, content)
                if not issue_data:
                    continue
                
                # Filter for unresolved only
                if issue_data.get("status") in ["resolved", "ignored"]:
                    skipped_count += 1
                    continue
                    
                unresolved_issues.append({
                    "id": issue_data["id"],
                    "title": issue_data["title"],
                    "content": content,
                    "status": "open"
                })

        if unresolved_issues:
            # Sync to API (which can then push to GitHub Actions/Issues if configured)
            await self.client.sync_issues({
                "projectId": self.project_id,
                "issues": unresolved_issues
            })

        return {"synced": len(unresolved_issues), "skipped": skipped_count}
