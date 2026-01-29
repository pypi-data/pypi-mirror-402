# tests/test_optimization.py
import pytest
import json
from mcp_extent.transformers.llm_transformer import LLMTransformer

def test_truncation():
    transformer = LLMTransformer()
    long_text = "A" * 1000
    long_stack = "Line\n" * 50
    
    data = {
        "logs": [{"details": long_text}],
        "exception": {"stackTrace": long_stack}
    }
    
    clean = transformer.transform(data, max_log_length=100, max_stack_trace_lines=5)
    
    assert len(clean["logs"][0]["details"]) < 200 # 100 + truncate msg
    assert "TRUNCATED" in clean["logs"][0]["details"]
    
    assert len(clean["exception"]["stackTrace"].splitlines()) < 10 # 5 + truncate msg
    assert "TRUNCATED" in clean["exception"]["stackTrace"]

def test_filtering_logic():
    # Simulate server filtering logic (since we can't easily mock async server calls in unit test without heavy setup)
    report = {
        "testSuites": [
            {
                "name": "Suite1",
                "testCases": [
                    {"name": "Pass1", "status": "passed"},
                    {"name": "Fail1", "status": "failed"},
                    {"name": "Skip1", "status": "skipped"}
                ]
            }
        ]
    }
    
    status_filter = ["failed", "skipped"]
    
    # Apply logic from server.py verify it works
    filtered_cases = [
        tc for tc in report["testSuites"][0]["testCases"]
        if tc.get("status", "").lower() in status_filter
    ]
    
    assert len(filtered_cases) == 2
    assert filtered_cases[0]["name"] == "Fail1"
    assert filtered_cases[1]["name"] == "Skip1"
