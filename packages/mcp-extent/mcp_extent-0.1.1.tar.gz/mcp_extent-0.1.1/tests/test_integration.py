# tests/test_integration.py
import pytest
import json
from mcp_extent.server import parse_report, analyze_test_failures
from pathlib import Path

SAMPLE_JSON = Path(__file__).parent / "sample_reports/json_report/extent.json"

class TestIntegration:
    def test_full_report_parsing(self):
        if not SAMPLE_JSON.exists():
            pytest.skip("Sample JSON not found")
            
        result = parse_report(str(SAMPLE_JSON))
        
        # Verify structure
        assert "reportInfo" in result
        assert "summary" in result
        assert "testSuites" in result
        
        # Verify data quality
        summary = result["summary"]
        assert summary["totalTests"] == summary["passed"] + summary["failed"] + summary["skipped"]

    def test_failure_analysis(self):
        if not SAMPLE_JSON.exists():
            pytest.skip("Sample JSON not found")
            
        report = parse_report(str(SAMPLE_JSON))
        analysis = analyze_test_failures(report)
        
        assert analysis["totalFailures"] > 0
        assert len(analysis["failurePatterns"]) > 0
        assert analysis["failurePatterns"][0]["type"] == "java.lang.AssertionError"
