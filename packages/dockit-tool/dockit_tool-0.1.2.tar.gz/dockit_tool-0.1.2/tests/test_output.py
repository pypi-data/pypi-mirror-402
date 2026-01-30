import pytest
from unittest.mock import patch, MagicMock
from dockit.core.output import (
    print_table,
    print_json,
    print_error,
    print_success,
    print_info,
    print_warning,
)


@patch("dockit.core.output.console")
def test_print_table(mock_console):
    """Test print_table function"""
    headers = ["NAME", "STATUS"]
    rows = [["web", "running"]]
    
    print_table(headers, rows)
    
    mock_console.print.assert_called_once()


@patch("dockit.core.output.console")
def test_print_json(mock_console):
    """Test print_json function"""
    data = {"name": "web", "status": "running"}
    
    print_json(data)
    
    mock_console.print.assert_called_once()


@patch("dockit.core.output.console")
def test_print_error(mock_console):
    """Test print_error function"""
    print_error("Something went wrong")
    
    mock_console.print.assert_called_once()


@patch("dockit.core.output.console")
def test_print_success(mock_console):
    """Test print_success function"""
    print_success("Operation completed")
    
    mock_console.print.assert_called_once()


@patch("dockit.core.output.console")
def test_print_info(mock_console):
    """Test print_info function"""
    print_info("Information message")
    
    mock_console.print.assert_called_once()


@patch("dockit.core.output.console")
def test_print_warning(mock_console):
    """Test print_warning function"""
    print_warning("Warning message")
    
    mock_console.print.assert_called_once()
