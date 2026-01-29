# tests/test_parsers.py
import pytest
import os
from pathlib import Path
from mcp_extent.parsers.json_parser import ExtentJsonParser
from mcp_extent.parsers.html_parser import ExtentHtmlParser

SAMPLE_JSON = Path(__file__).parent / "sample_reports/json_report/extent.json"
SAMPLE_HTML = Path(__file__).parent / "sample_reports/spark_report/index.html"

class TestJsonParser:
    def test_parse_simple_report(self):
        if not SAMPLE_JSON.exists():
            pytest.skip("Sample JSON not found")
            
        parser = ExtentJsonParser(SAMPLE_JSON)
        result = parser.parse()
        
        assert "summary" in result
        assert result["summary"]["totalTests"] > 0
        assert result["summary"]["failed"] == 1
    
    def test_parse_failed_tests(self):
        if not SAMPLE_JSON.exists():
            pytest.skip("Sample JSON not found")

        parser = ExtentJsonParser(SAMPLE_JSON)
        result = parser.parse()
        
        # Verify exception details are captured
        failed_suite = next(
            s for s in result["testSuites"] 
            if s["status"] == "failed"
        )
        assert failed_suite is not None
        
        failed_test = next(
            tc for tc in failed_suite["testCases"] 
            if tc["status"] == "failed"
        )
        assert failed_test["exception"] is not None
        assert "AssertionError" in failed_test["exception"]["type"]

class TestHtmlParser:
    def test_parse_spark_report(self):
        if not SAMPLE_HTML.exists():
            pytest.skip("Sample HTML not found")

        parser = ExtentHtmlParser(SAMPLE_HTML)
        result = parser.parse()
        
        assert "testSuites" in result
        assert len(result["testSuites"]) > 0
        assert result["summary"]["failed"] >= 1
