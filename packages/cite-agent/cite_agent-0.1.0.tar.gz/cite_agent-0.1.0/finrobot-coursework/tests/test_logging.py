"""Unit tests for finrobot.logging module."""

import unittest
import tempfile
import json
import logging
from pathlib import Path
from unittest.mock import Mock, patch

from finrobot.logging import (
    FinRobotLogger,
    JSONFormatter,
    MetricsCollector,
    setup_logging,
    get_logger,
    record_metric,
    get_metrics,
)


class TestJSONFormatter(unittest.TestCase):
    """Test JSONFormatter class."""
    
    def test_format_returns_json_string(self):
        """Test that formatter returns valid JSON."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        result = formatter.format(record)
        
        # Should be valid JSON
        data = json.loads(result)
        self.assertIn("timestamp", data)
        self.assertIn("level", data)
        self.assertIn("message", data)
        self.assertEqual(data["level"], "INFO")
        self.assertEqual(data["message"], "Test message")
    
    def test_format_includes_exception_info(self):
        """Test that formatter includes exception info."""
        formatter = JSONFormatter()
        
        try:
            raise ValueError("Test error")
        except ValueError:
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="test.py",
                lineno=10,
                msg="Error occurred",
                args=(),
                exc_info=True
            )
            record.exc_info = None  # Reset for this test
        
        result = formatter.format(record)
        data = json.loads(result)
        self.assertEqual(data["level"], "ERROR")


class TestFinRobotLogger(unittest.TestCase):
    """Test FinRobotLogger class."""
    
    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a logger."""
        logger_instance = FinRobotLogger()
        logger = logger_instance.get_logger("test")
        self.assertIsInstance(logger, logging.Logger)
    
    def test_setup_creates_logger(self):
        """Test that setup creates a logger with handlers."""
        temp_dir = tempfile.TemporaryDirectory()
        temp_path = Path(temp_dir.name)
        
        try:
            log_file = temp_path / "test.log"
            logger_instance = FinRobotLogger()
            logger_instance.setup(level="INFO", log_file=str(log_file))
            
            logger = logger_instance.get_logger("test")
            self.assertIsNotNone(logger)
            
            # Check that handlers were added
            self.assertGreater(len(logger_instance.root_logger.handlers), 0)
        
        finally:
            temp_dir.cleanup()
    
    def test_logger_logs_to_file(self):
        """Test that logger writes to file."""
        temp_dir = tempfile.TemporaryDirectory()
        temp_path = Path(temp_dir.name)
        
        try:
            log_file = temp_path / "test.log"
            logger_instance = FinRobotLogger()
            logger_instance.setup(level="INFO", log_file=str(log_file))
            
            logger = logger_instance.get_logger("test")
            logger.info("Test message")
            
            # Give time for file write
            import time
            time.sleep(0.1)
            
            # Check that file contains message
            if log_file.exists():
                with open(log_file) as f:
                    content = f.read()
                self.assertIn("Test message", content)
        
        finally:
            temp_dir.cleanup()
    
    def test_get_logger_same_name_returns_same_logger(self):
        """Test that multiple calls with same name return same logger."""
        logger_instance = FinRobotLogger()
        logger1 = logger_instance.get_logger("test")
        logger2 = logger_instance.get_logger("test")
        
        self.assertIs(logger1, logger2)


class TestMetricsCollector(unittest.TestCase):
    """Test MetricsCollector class."""
    
    def test_record_metric(self):
        """Test recording a metric."""
        collector = MetricsCollector()
        
        collector.record("accuracy", 0.95)
        
        metrics = collector.get("accuracy")
        self.assertGreater(len(metrics), 0)
        self.assertEqual(metrics[-1]["value"], 0.95)
    
    def test_record_multiple_metrics(self):
        """Test recording multiple metrics with same name."""
        collector = MetricsCollector()
        
        collector.record("accuracy", 0.95)
        collector.record("accuracy", 0.97)
        
        metrics = collector.get("accuracy")
        self.assertEqual(len(metrics), 2)
        self.assertEqual(metrics[0]["value"], 0.95)
        self.assertEqual(metrics[1]["value"], 0.97)
    
    def test_record_with_tags(self):
        """Test recording metric with tags."""
        collector = MetricsCollector()
        
        collector.record("latency", 0.5, tags={"agent": "test", "task": "analysis"})
        
        metrics = collector.get("latency")
        self.assertGreater(len(metrics), 0)
        self.assertEqual(metrics[-1]["value"], 0.5)
        self.assertIn("tags", metrics[-1])
        self.assertEqual(metrics[-1]["tags"]["agent"], "test")
    
    def test_get_latest_metric(self):
        """Test getting latest metric."""
        collector = MetricsCollector()
        
        collector.record("accuracy", 0.95)
        collector.record("accuracy", 0.97)
        
        latest = collector.get_latest("accuracy")
        self.assertEqual(latest, 0.97)
    
    def test_save_metrics(self):
        """Test saving metrics to file."""
        temp_dir = tempfile.TemporaryDirectory()
        temp_path = Path(temp_dir.name)
        
        try:
            collector = MetricsCollector()
            collector.record("accuracy", 0.95)
            collector.record("latency", 0.5)
            
            metrics_file = temp_path / "metrics.json"
            collector.save(str(metrics_file))
            
            self.assertTrue(metrics_file.exists())
            
            # Verify saved content
            with open(metrics_file) as f:
                data = json.load(f)
            
            self.assertIn("accuracy", data)
            self.assertIn("latency", data)
        
        finally:
            temp_dir.cleanup()
    
    def test_clear_metrics(self):
        """Test clearing all metrics."""
        collector = MetricsCollector()
        
        collector.record("accuracy", 0.95)
        collector.record("latency", 0.5)
        
        metrics_before = len(collector.metrics)
        self.assertGreater(metrics_before, 0)
        
        collector.clear()
        
        metrics_after = len(collector.metrics)
        self.assertEqual(metrics_after, 0)
    
    def test_compute_statistics(self):
        """Test computing statistics on metrics."""
        collector = MetricsCollector()
        
        # Record multiple values
        for value in [0.90, 0.92, 0.95, 0.88, 0.93]:
            collector.record("accuracy", value)
        
        metrics = collector.get("accuracy")
        accuracy_values = [m["value"] for m in metrics]
        
        # Compute basic stats
        mean = sum(accuracy_values) / len(accuracy_values)
        self.assertAlmostEqual(mean, 0.916, places=2)
        
        # Min and max
        self.assertEqual(min(accuracy_values), 0.88)
        self.assertEqual(max(accuracy_values), 0.95)


class TestGlobalLoggingFunctions(unittest.TestCase):
    """Test global logging utility functions."""
    
    def test_get_logger_returns_logger(self):
        """Test get_logger function."""
        logger = get_logger("test_module")
        self.assertIsInstance(logger, logging.Logger)
        self.assertIn("test_module", logger.name)
    
    def test_record_metric_function(self):
        """Test record_metric function."""
        record_metric("test_metric", 42)
        
        metrics_collector = get_metrics()
        metrics = metrics_collector.get("test_metric")
        self.assertGreater(len(metrics), 0)
        self.assertEqual(metrics[-1]["value"], 42)


if __name__ == "__main__":
    unittest.main()


class TestJSONFormatter(unittest.TestCase):
    """Test JSONFormatter class."""
    
    def test_format_returns_json_string(self):
        """Test that formatter returns valid JSON."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        result = formatter.format(record)
        
        # Should be valid JSON
        data = json.loads(result)
        self.assertIn("timestamp", data)
        self.assertIn("level", data)
        self.assertIn("message", data)
        self.assertEqual(data["level"], "INFO")
        self.assertEqual(data["message"], "Test message")
    
    def test_format_includes_exception_info(self):
        """Test that formatter includes exception info."""
        formatter = JSONFormatter()
        
        try:
            raise ValueError("Test error")
        except ValueError:
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="test.py",
                lineno=10,
                msg="Error occurred",
                args=(),
                exc_info=True
            )
            record.exc_info = None  # Reset for this test
        
        result = formatter.format(record)
        data = json.loads(result)
        self.assertEqual(data["level"], "ERROR")

