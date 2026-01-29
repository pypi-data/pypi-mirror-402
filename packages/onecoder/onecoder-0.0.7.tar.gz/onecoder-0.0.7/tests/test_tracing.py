import unittest
from unittest.mock import patch, MagicMock
from onecoder.tracing import setup_tracing, trace_span
import mlflow

class TestTracing(unittest.TestCase):
    def test_setup_tracing(self):
        with patch("mlflow.set_tracking_uri") as mock_set_uri, \
             patch("mlflow.set_experiment") as mock_set_exp:
            setup_tracing("file:./test_runs")
            mock_set_uri.assert_called_with("file:./test_runs")
            mock_set_exp.assert_called_with("OneCoder-CLI")

    @patch("onecoder.tracing._tracing_enabled", True)
    def test_trace_span(self):
        # Mock mlflow.start_span
        mock_span = MagicMock()
        mock_ctx = MagicMock()
        mock_ctx.__enter__.return_value = mock_span

        with patch("mlflow.start_span", return_value=mock_ctx) as mock_start_span:
            @trace_span(name="test_func")
            def my_func(a, b):
                return a + b

            result = my_func(1, 2)

            self.assertEqual(result, 3)
            mock_start_span.assert_called_with(name="test_func", span_type="chain")
            mock_span.set_inputs.assert_called()
            mock_span.set_outputs.assert_called()

if __name__ == "__main__":
    unittest.main()
