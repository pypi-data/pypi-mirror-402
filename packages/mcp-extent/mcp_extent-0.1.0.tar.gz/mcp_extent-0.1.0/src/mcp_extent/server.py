# src/mcp_extent/server.py
import json
import logging
from pathlib import Path
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

from .parsers.html_parser import ExtentHtmlParser
from .parsers.json_parser import ExtentJsonParser
from .transformers.llm_transformer import LLMTransformer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-extent")

# Initialize MCP server
server = Server("mcp-extent")

def detect_report_type(report_path: str) -> str:
    """Detect if report is HTML or JSON based on file extension or content."""
    path = Path(report_path)
    
    if path.is_dir():
        # Check for index.html (Spark report)
        if (path / "index.html").exists():
            return "html"
        # Check for extent.json
        json_files = list(path.glob("*.json"))
        if json_files:
            return "json"
    elif path.suffix.lower() == ".json":
        return "json"
    elif path.suffix.lower() in [".html", ".htm"]:
        return "html"
    
    raise ValueError(f"Cannot determine report type for: {report_path}")

def parse_report(report_path: str, include_screenshots: bool = False) -> dict:
    """Parse Extent Report and return structured data."""
    try:
        report_type = detect_report_type(report_path)
        
        if report_type == "json":
            parser = ExtentJsonParser(report_path)
        else:
            parser = ExtentHtmlParser(report_path)
        
        raw_data = parser.parse()
        
        # Transform to LLM-friendly format
        transformer = LLMTransformer()
        return transformer.transform(raw_data, include_screenshots=include_screenshots)
    except Exception as e:
        logger.error(f"Error parsing report {report_path}: {e}")
        raise

def analyze_test_failures(report: dict) -> dict:
    """Analyze failures for patterns and insights."""
    failed_tests = []
    failure_types = {}
    
    # Common semantic patterns to look for in logs if exception type is generic or missing
    semantic_patterns = {
        "Timeout": ["timeout", "timed out", "wait for element"],
        "Element Not Found": ["no such element", "element not found", "unable to locate"],
        "Stale Element": ["stale element", "element is not attached"],
        "Assertion Failure": ["expected [", "but found [", "assertion failed"],
        "API Error": ["500 internal server error", "404 not found", "api gateway"],
        "Database Error": ["sql exception", "database connection", "query failed"]
    }

    for suite in report.get("testSuites", []):
        for test in suite.get("testCases", []):
            if test.get("status") == "failed":
                exception = test.get("exception", {}) or {}
                failure_type = exception.get("type", "Unknown")
                failure_message = exception.get("message", "No message")
                
                # If failure type is generic, try to refine it using patterns
                if failure_type in ["Unknown", "Exception", "Error"]:
                    # Check message and logs
                    full_text = failure_message.lower()
                    for step in test.get("steps", []):
                         full_text += " " + step.get("name", "").lower()
                    
                    for category, keywords in semantic_patterns.items():
                        if any(k in full_text for k in keywords):
                            failure_type = category
                            break

                failed_tests.append({
                    "testName": test.get("name"),
                    "suiteName": suite.get("name"),
                    "failureType": failure_type,
                    "failureMessage": failure_message,
                })
                
                if failure_type not in failure_types:
                    failure_types[failure_type] = {"count": 0, "tests": []}
                failure_types[failure_type]["count"] += 1
                failure_types[failure_type]["tests"].append(test.get("name"))
    
    return {
        "totalFailures": len(failed_tests),
        "failedTests": failed_tests,
        "failurePatterns": [
            {"type": k, **v} for k, v in failure_types.items()
        ]
    }

def compare_test_reports(baseline: dict, current: dict) -> dict:
    """Compare two reports and identify changes."""
    baseline_tests = {}
    current_tests = {}
    
    for suite in baseline.get("testSuites", []):
        for test in suite.get("testCases", []):
            key = f"{suite.get('name')}.{test.get('name')}"
            baseline_tests[key] = test.get("status")
    
    for suite in current.get("testSuites", []):
        for test in suite.get("testCases", []):
            key = f"{suite.get('name')}.{test.get('name')}"
            current_tests[key] = test.get("status")
    
    new_failures = []
    fixed_tests = []
    new_tests = []
    removed_tests = []
    
    all_tests = set(baseline_tests.keys()) | set(current_tests.keys())
    
    for test in all_tests:
        baseline_status = baseline_tests.get(test)
        current_status = current_tests.get(test)
        
        if baseline_status is None:
            new_tests.append(test)
        elif current_status is None:
            removed_tests.append(test)
        elif baseline_status == "passed" and current_status == "failed":
            new_failures.append(test)
        elif baseline_status == "failed" and current_status == "passed":
            fixed_tests.append(test)
    
    return {
        "baselineSummary": baseline.get("summary", {}),
        "currentSummary": current.get("summary", {}),
        "newFailures": new_failures,
        "fixedTests": fixed_tests,
        "newTests": new_tests,
        "removedTests": removed_tests
    }

@server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools."""
    return [
        Tool(
            name="get_extent_report",
            description="Read and parse an Extent Report and return structured test data in LLM-friendly JSON format",
            inputSchema={
                "type": "object",
                "properties": {
                    "report_path": {
                        "type": "string",
                        "description": "Path to Extent Report file (HTML or JSON) or directory containing report files"
                    },
                    "include_screenshots": {
                        "type": "boolean",
                        "description": "Include base64 encoded screenshots in output",
                        "default": False
                    },
                    "status_filter": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter tests by status (e.g., ['failed', 'skipped'])"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max number of tests to return (useful for large reports)",
                        "default": 100
                    }
                },
                "required": ["report_path"]
            }
        ),
        Tool(
            name="get_test_summary",
            description="Get a concise summary of test execution results including pass/fail counts and duration",
            inputSchema={
                "type": "object",
                "properties": {
                    "report_path": {
                        "type": "string",
                        "description": "Path to Extent Report"
                    }
                },
                "required": ["report_path"]
            }
        ),
        Tool(
            name="get_failed_tests",
            description="Get detailed information about all failed tests including error messages and stack traces",
            inputSchema={
                "type": "object",
                "properties": {
                    "report_path": {
                        "type": "string",
                        "description": "Path to Extent Report"
                    },
                    "include_steps": {
                        "type": "boolean",
                        "description": "Include all test steps in output",
                        "default": True
                    }
                },
                "required": ["report_path"]
            }
        ),
        Tool(
            name="analyze_failures",
            description="Analyze test failures and provide patterns, common issues, and potential root causes",
            inputSchema={
                "type": "object",
                "properties": {
                    "report_path": {
                        "type": "string",
                        "description": "Path to Extent Report"
                    }
                },
                "required": ["report_path"]
            }
        ),
        Tool(
            name="compare_reports",
            description="Compare two test reports to identify new failures, fixed tests, and trends",
            inputSchema={
                "type": "object",
                "properties": {
                    "baseline_report": {
                        "type": "string",
                        "description": "Path to baseline/previous report"
                    },
                    "current_report": {
                        "type": "string",
                        "description": "Path to current report"
                    }
                },
                "required": ["baseline_report", "current_report"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    try:
        if name == "get_extent_report":
            report = parse_report(
                arguments["report_path"],
                arguments.get("include_screenshots", False)
            )
            
            # Apply filtering
            status_filter = arguments.get("status_filter")
            if status_filter:
                status_filter = [s.lower() for s in status_filter]
                for suite in report.get("testSuites", []):
                    suite["testCases"] = [
                        tc for tc in suite.get("testCases", [])
                        if tc.get("status", "").lower() in status_filter
                    ]
            
            # Apply limit per suite
            limit = arguments.get("limit", 100)
            for suite in report.get("testSuites", []):
                if len(suite["testCases"]) > limit:
                     suite["testCases"] = suite["testCases"][:limit]

            return [TextContent(type="text", text=json.dumps(report, indent=2))]
        
        elif name == "get_test_summary":
            report = parse_report(arguments["report_path"])
            summary = {
                "reportInfo": report.get("reportInfo", {}),
                "summary": report.get("summary", {})
            }
            return [TextContent(type="text", text=json.dumps(summary, indent=2))]
        
        elif name == "get_failed_tests":
            report = parse_report(arguments["report_path"])
            failed_tests = []
            for suite in report.get("testSuites", []):
                for test in suite.get("testCases", []):
                    if test.get("status") == "failed":
                        # Create shallow copy to avoid modifying original info
                        test_copy = test.copy()
                        if not arguments.get("include_steps", True):
                            test_copy.pop("steps", None)
                        failed_tests.append({
                            "suiteName": suite.get("name"),
                            **test_copy
                        })
            return [TextContent(type="text", text=json.dumps(failed_tests, indent=2))]
        
        elif name == "analyze_failures":
            report = parse_report(arguments["report_path"])
            analysis = analyze_test_failures(report)
            return [TextContent(type="text", text=json.dumps(analysis, indent=2))]
        
        elif name == "compare_reports":
            baseline = parse_report(arguments["baseline_report"])
            current = parse_report(arguments["current_report"])
            comparison = compare_test_reports(baseline, current)
            return [TextContent(type="text", text=json.dumps(comparison, indent=2))]
        
        else:
            raise ValueError(f"Unknown tool: {name}")
            
    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}")
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

def main_entry():
    """Synchronous entry point for the console script."""
    import asyncio
    asyncio.run(main())

if __name__ == "__main__":
    main_entry()
