# tests/test_advanced_analysis.py
import pytest
from mcp_extent.server import analyze_test_failures

def test_semantic_failure_analysis():
    # Mock report with generic exceptions but specific log messages
    mock_report = {
        "testSuites": [
            {
                "name": "SearchSuite",
                "testCases": [
                    {
                        "name": "TestSearchTimeout",
                        "status": "failed",
                        "exception": {
                            "type": "Exception",
                            "message": "Something went wrong"
                        },
                        "steps": [
                            {"name": "Clicked search button", "status": "pass"},
                            {"name": "Wait for element timed out after 30s", "status": "fail"}
                        ]
                    },
                    {
                        "name": "TestElementGone",
                        "status": "failed",
                        "exception": {
                            "type": "Unknown",
                            "message": "Stale Element Reference Exception"
                        },
                        "steps": []
                    }
                ]
            }
        ]
    }
    
    analysis = analyze_test_failures(mock_report)
    
    patterns = {p["type"]: p["count"] for p in analysis["failurePatterns"]}
    
    # Should detect "Timeout" from log message
    assert "Timeout" in patterns
    assert patterns["Timeout"] == 1
    
    # Should detect "Stale Element" from exception message
    assert "Stale Element" in patterns
    assert patterns["Stale Element"] == 1
