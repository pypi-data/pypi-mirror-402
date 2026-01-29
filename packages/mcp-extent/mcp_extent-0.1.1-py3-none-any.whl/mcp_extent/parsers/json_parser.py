import json
from pathlib import Path
from typing import Optional, Union, List, Dict, Any
from .base import BaseParser

class ExtentJsonParser(BaseParser):
    """Parser for Extent JSON reports (from JsonFormatter)."""
    
    def __init__(self, report_path: Union[str, Path]):
        self.report_path = Path(report_path)
        if self.report_path.is_dir():
            # Find JSON file in directory
            json_files = list(self.report_path.glob("*.json"))
            if json_files:
                self.report_path = json_files[0]
            else:
                raise FileNotFoundError(f"No JSON files found in {report_path}")
    
    def parse(self) -> dict:
        """Parse the JSON report."""
        with open(self.report_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return self._transform_extent_json(data)
    
    def _transform_extent_json(self, data: Union[Dict, List]) -> dict:
        """Transform Extent JSON format to our standard format."""
        # Extent JSON structure varies by version
        # Handle both array and object formats
        
        if isinstance(data, list):
            # Array of tests (common format)
            return self._transform_test_array(data)
        else:
            # Object format with metadata
            return self._transform_test_object(data)
    
    def _transform_test_array(self, tests: list) -> dict:
        """Transform array of tests."""
        suites: Dict[str, Dict[str, Any]] = {}
        total = passed = failed = skipped = 0
        
        for test in tests:
            suite_name = test.get('bddType', test.get('className', 'Default Suite'))
            
            if suite_name not in suites:
                suites[suite_name] = {
                    "name": suite_name,
                    "testCases": []
                }
            
            test_case = self._transform_test_case(test)
            suites[suite_name]["testCases"].append(test_case)
            
            # Count stats
            total += 1
            status = test_case.get('status', '').lower()
            if status == 'passed' or status == 'pass':
                passed += 1
            elif status == 'failed' or status == 'fail':
                failed += 1
            else:
                skipped += 1
        
        # Determine suite status
        for suite in suites.values():
            statuses = [tc['status'] for tc in suite['testCases']]
            if 'failed' in statuses:
                suite['status'] = 'failed'
            elif 'skipped' in statuses and 'passed' not in statuses:
                suite['status'] = 'skipped'
            else:
                suite['status'] = 'passed'
        
        pass_rate = f"{(passed / total * 100):.1f}%" if total > 0 else "0%"
        
        return {
            "reportInfo": {},
            "summary": {
                "totalTests": total,
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "passRate": pass_rate
            },
            "testSuites": list(suites.values())
        }
    
    def _transform_test_object(self, data: dict) -> dict:
        """Transform object format with metadata."""
        tests = data.get('tests', data.get('testList', []))
        result = self._transform_test_array(tests)
        
        # Add report info if available
        result['reportInfo'] = {
            "reportName": data.get('reportName', 'Extent Report'),
            "startTime": data.get('startTime', ''),
            "endTime": data.get('endTime', '')
        }
        
        # Add system info if available
        result['systemInfo'] = data.get('systemInfo', {})
        
        return result
    
    def _transform_test_case(self, test: dict) -> dict:
        """Transform a single test case."""
        status = test.get('status', 'unknown').lower()
        if status == 'pass':
            status = 'passed'
        elif status == 'fail':
            status = 'failed'
        elif status == 'skip':
            status = 'skipped'
        
        # Extract exception info
        exception = None
        if status == 'failed':
            exception = self._extract_exception(test)
        
        # Extract steps
        steps = []
        log_entries = test.get('logs', test.get('logList', []))
        for i, log in enumerate(log_entries, 1):
            steps.append({
                "stepNumber": i,
                "name": log.get('details', log.get('message', '')),
                "status": log.get('status', 'info').lower(),
                "timestamp": log.get('timestamp', '')
            })
        
        return {
            "name": test.get('name', ''),
            "description": test.get('description', ''),
            "status": status,
            "severity": test.get('severity', 'normal').lower(),
            "startTime": test.get('startTime', ''),
            "endTime": test.get('endTime', ''),
            "duration": self._calculate_duration(test),
            "categories": test.get('categoryList', []),
            "authors": test.get('authorList', []),
            "devices": test.get('deviceList', []),
            "steps": steps,
            "screenshots": self._extract_screenshots(test),
            "exception": exception
        }
    
    def _extract_exception(self, test: dict) -> Optional[dict]:
        """Extract exception details from failed test."""
        # Look for exception in logs or dedicated field
        for log in test.get('logs', test.get('logList', [])):
            status = log.get('status', '').lower()
            if status in ['fail', 'failed', 'error']:
                exception_info = log.get('exceptionInfo', {})
                return {
                    "type": exception_info.get('className', 'Exception'),
                    "message": log.get('details', log.get('message', '')),
                    "stackTrace": exception_info.get('stackTrace', '')
                }
        return None
    
    def _calculate_duration(self, test: dict) -> str:
        """Calculate test duration."""
        start = test.get('startTime', 0)
        end = test.get('endTime', 0)
        
        if isinstance(start, (int, float)) and isinstance(end, (int, float)):
            duration_ms = end - start
            if duration_ms < 1000:
                return f"{duration_ms}ms"
            elif duration_ms < 60000:
                return f"{duration_ms / 1000:.1f}s"
            else:
                return f"{duration_ms / 60000:.1f}m"
        
        return ""

    def _extract_screenshots(self, test: dict) -> List[Dict[str, str]]:
        """Extract screenshots from test data."""
        screenshots = []
        
        # Method 1: Direct screenCapture list
        captures = test.get('screenCaptureList', [])
        for capture in captures:
            if isinstance(capture, dict):
                 # Base64 might be in 'base64' or 'screenCapture' field
                 base64_data = capture.get('base64', capture.get('screenCapture', ''))
                 if base64_data:
                     screenshots.append({
                         "name": capture.get('title', 'screenshot'),
                         "base64": base64_data
                     })

        # Method 2: Embedded in logs
        for log in test.get('logs', test.get('logList', [])):
             details = log.get('details', '')
             # Sometimes base64 is embedded in details (less common in JSON, but possible)
             # Check for media/screenCapture objects in log
             media = log.get('media', {})
             if media:
                 base64_data = media.get('base64', '')
                 if base64_data:
                     screenshots.append({
                         "name": "log-screenshot",
                         "base64": base64_data
                     })
        
        return screenshots
