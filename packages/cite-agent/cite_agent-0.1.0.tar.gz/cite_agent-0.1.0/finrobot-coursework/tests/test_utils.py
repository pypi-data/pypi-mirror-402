"""Unit tests for finrobot.utils module."""

import unittest
import tempfile
import json
import os
from pathlib import Path
from datetime import datetime, date, timedelta
import pandas as pd

from finrobot.utils import (
    save_output,
    get_current_date,
    register_keys_from_json,
    get_next_weekday,
)
from finrobot.errors import ValidationError


class TestSaveOutput(unittest.TestCase):
    """Test save_output function."""
    
    def setUp(self):
        """Create temporary directory for tests."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
    
    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()
    
    def test_save_dataframe_to_csv(self):
        """Test saving DataFrame to CSV."""
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        save_path = self.temp_path / "test.csv"
        
        save_output(df, "test_df", save_path=str(save_path))
        
        self.assertTrue(save_path.exists())
        result_df = pd.read_csv(save_path, index_col=0)
        pd.testing.assert_frame_equal(result_df, df)
    
    def test_save_dict_to_json(self):
        """Test saving dictionary to JSON."""
        data = {"key1": "value1", "key2": "value2"}
        save_path = self.temp_path / "test.json"
        
        save_output(data, "test_dict", save_path=str(save_path))
        
        self.assertTrue(save_path.exists())
        with open(save_path) as f:
            result = json.load(f)
        self.assertEqual(result, data)
    
    def test_save_list_to_json(self):
        """Test saving list to JSON."""
        data = [1, 2, 3, "test"]
        save_path = self.temp_path / "test_list.json"
        
        save_output(data, "test_list", save_path=str(save_path))
        
        self.assertTrue(save_path.exists())
        with open(save_path) as f:
            result = json.load(f)
        self.assertEqual(result, data)
    
    def test_save_none_path_skips_save(self):
        """Test that None path skips saving."""
        df = pd.DataFrame({"a": [1, 2, 3]})
        # Should not raise exception
        save_output(df, "test_df", save_path=None)
    
    def test_save_invalid_tag_raises_error(self):
        """Test that invalid tag raises ValidationError."""
        df = pd.DataFrame({"a": [1, 2, 3]})
        save_path = self.temp_path / "test.csv"
        
        with self.assertRaises(ValidationError):
            save_output(df, "", save_path=str(save_path))
    
    def test_save_invalid_data_type_raises_error(self):
        """Test that invalid data type raises ValidationError."""
        save_path = self.temp_path / "test.csv"
        
        with self.assertRaises(ValidationError):
            save_output(123, "test", save_path=str(save_path))


class TestGetCurrentDate(unittest.TestCase):
    """Test get_current_date function."""
    
    def test_returns_string(self):
        """Test that function returns string."""
        result = get_current_date()
        self.assertIsInstance(result, str)
    
    def test_correct_format(self):
        """Test that date is in correct format."""
        result = get_current_date()
        # Should be able to parse as datetime
        parsed = datetime.strptime(result, "%Y-%m-%d")
        self.assertIsInstance(parsed, datetime)
    
    def test_returns_today(self):
        """Test that function returns today's date."""
        result = get_current_date()
        today = date.today().strftime("%Y-%m-%d")
        self.assertEqual(result, today)


class TestRegisterKeysFromJson(unittest.TestCase):
    """Test register_keys_from_json function."""
    
    def setUp(self):
        """Create temporary directory for tests."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
    
    def tearDown(self):
        """Clean up temporary directory and env vars."""
        self.temp_dir.cleanup()
        # Clean up any test environment variables
        for key in ["TEST_KEY_1", "TEST_KEY_2"]:
            os.environ.pop(key, None)
    
    def test_register_keys_success(self):
        """Test successful key registration."""
        config_file = self.temp_path / "config.json"
        config_data = {"TEST_KEY_1": "value1", "TEST_KEY_2": "value2"}
        
        with open(config_file, "w") as f:
            json.dump(config_data, f)
        
        result = register_keys_from_json(config_file)
        
        self.assertEqual(os.environ.get("TEST_KEY_1"), "value1")
        self.assertEqual(os.environ.get("TEST_KEY_2"), "value2")
        self.assertEqual(len(result), 2)
    
    def test_register_keys_nonexistent_file(self):
        """Test with nonexistent file."""
        config_file = self.temp_path / "nonexistent.json"
        
        with self.assertRaises(ValidationError):
            register_keys_from_json(config_file)
    
    def test_register_keys_invalid_json(self):
        """Test with invalid JSON."""
        config_file = self.temp_path / "invalid.json"
        
        with open(config_file, "w") as f:
            f.write("{invalid json}")
        
        with self.assertRaises(ValidationError):
            register_keys_from_json(config_file)
    
    def test_register_keys_not_dict(self):
        """Test with JSON that is not a dictionary."""
        config_file = self.temp_path / "list.json"
        
        with open(config_file, "w") as f:
            json.dump([1, 2, 3], f)
        
        with self.assertRaises(ValidationError):
            register_keys_from_json(config_file)


class TestGetNextWeekday(unittest.TestCase):
    """Test get_next_weekday function."""
    
    def test_monday_returns_same_day(self):
        """Test that Monday returns the same day."""
        # Monday is 0
        monday = datetime(2024, 1, 1)  # Jan 1, 2024 is Monday
        result = get_next_weekday(monday)
        self.assertEqual(result, monday)
    
    def test_friday_returns_same_day(self):
        """Test that Friday returns the same day."""
        # Friday is 4
        friday = datetime(2024, 1, 5)  # Jan 5, 2024 is Friday
        result = get_next_weekday(friday)
        self.assertEqual(result, friday)
    
    def test_saturday_returns_monday(self):
        """Test that Saturday returns next Monday."""
        # Saturday is 5
        saturday = datetime(2024, 1, 6)  # Jan 6, 2024 is Saturday
        result = get_next_weekday(saturday)
        expected = datetime(2024, 1, 8)  # Monday
        self.assertEqual(result, expected)
    
    def test_sunday_returns_monday(self):
        """Test that Sunday returns next Monday."""
        # Sunday is 6
        sunday = datetime(2024, 1, 7)  # Jan 7, 2024 is Sunday
        result = get_next_weekday(sunday)
        expected = datetime(2024, 1, 8)  # Monday
        self.assertEqual(result, expected)
    
    def test_string_date_format(self):
        """Test with string date input."""
        result = get_next_weekday("2024-01-01")  # Monday
        self.assertEqual(result.strftime("%Y-%m-%d"), "2024-01-01")
    
    def test_date_object_input(self):
        """Test with date object input."""
        input_date = date(2024, 1, 1)  # Monday
        result = get_next_weekday(input_date)
        self.assertEqual(result.date(), input_date)
    
    def test_invalid_date_string_format(self):
        """Test with invalid date string format."""
        with self.assertRaises(ValidationError):
            get_next_weekday("01/01/2024")  # Wrong format
    
    def test_invalid_date_type(self):
        """Test with invalid date type."""
        with self.assertRaises(ValidationError):
            get_next_weekday(123)


if __name__ == "__main__":
    unittest.main()
