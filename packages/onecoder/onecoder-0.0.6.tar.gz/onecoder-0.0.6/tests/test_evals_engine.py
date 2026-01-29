import unittest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import json
from onecoder.evaluation.evals_engine import EvalsEngine

class TestEvalsEngine(unittest.TestCase):
    def setUp(self):
        self.repo_root = Path("/tmp/test_repo")
        self.engine = EvalsEngine(repo_root=self.repo_root)

    @patch("builtins.open", new_callable=mock_open, read_data='{"cost": 0.05, "tokens": 100, "tool": "test"}\n{"cost": 0.10, "tokens": 200, "tool": "test"}\n')
    @patch("pathlib.Path.exists")
    def test_get_finops_summary(self, mock_exists, mock_file):
        mock_exists.return_value = True
        summary = self.engine._get_finops_summary("sprint-123")
        self.assertAlmostEqual(summary["total_cost"], 0.15)
        self.assertEqual(summary["total_tokens"], 300)

    @patch("mlflow.get_experiment_by_name")
    @patch("mlflow.tracking.MlflowClient")
    def test_get_trace_summaries(self, mock_client_cls, mock_get_exp):
        mock_exp = MagicMock()
        mock_exp.experiment_id = "1"
        mock_get_exp.return_value = mock_exp
        
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.search_runs.return_value = [] # Mock empty runs for now

        summary = self.engine._get_trace_summaries("sprint-123")
        self.assertEqual(summary["tool_counts"], {})

    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.exists")
    def test_get_sprint_metrics(self, mock_exists, mock_file):
        mock_exists.return_value = True
        sprint_data = {
            "tasks": [
                {"id": "T1", "ttuSeconds": 50, "startedAt": "2024-01-01T10:00:00Z", "completedAt": "2024-01-01T11:00:00Z"},
                {"id": "T2", "ttuSeconds": 150, "startedAt": "2024-01-01T12:00:00Z", "completedAt": "2024-01-01T14:00:00Z"}
            ]
        }
        mock_file.return_value.__enter__.return_value.read.return_value = json.dumps(sprint_data)
        
        metrics = self.engine._get_sprint_metrics("sprint-123")
        self.assertEqual(metrics["avg_ttu"], 100)
        self.assertEqual(metrics["avg_ttr"], 5400) # (3600 + 7200) / 2 = 5400

if __name__ == "__main__":
    unittest.main()
