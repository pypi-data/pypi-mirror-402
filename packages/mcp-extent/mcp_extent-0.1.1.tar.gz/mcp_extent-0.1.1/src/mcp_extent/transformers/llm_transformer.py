from typing import Dict, Any

class LLMTransformer:
    """Transforms raw report data into LLM-friendly format."""
    
    def transform(self, raw_data: Dict[str, Any], include_screenshots: bool = False, max_log_length: int = 500, max_stack_trace_lines: int = 15) -> Dict[str, Any]:
        """
        Clean and optimize report data for LLM consumption.
        
        Args:
            raw_data: The dictionary returned by parsers
            include_screenshots: Whether to include base64 screenshot data
            max_log_length: Maximum characters for log details
            max_stack_trace_lines: Maximum lines for stack traces
            
        Returns:
            Cleaned dictionary
        """
        # We will modify a deep copy to be safe if reusing data, 
        # but for performance in this context, in-place modification or shallow logic is fine 
        # as long as we don't need the original big data later.
        transformed = raw_data
        
        # 1. Filter screenshots if needed
        if not include_screenshots:
            self._remove_screenshots(transformed)
            
        # 2. Truncate heavy text fields
        self._truncate_fields(transformed, max_log_length, max_stack_trace_lines)
            
        return transformed

    def _remove_screenshots(self, data: Any):
        """Recursively remove screenshot fields/base64 data."""
        if isinstance(data, dict):
            if 'base64' in data:
                del data['base64']
            
            # Remove from 'screenshots' list if present
            if 'screenshots' in data and isinstance(data['screenshots'], list):
                # If we want to keep metadata, we iterate and clean. 
                # If 'include_screenshots' is False, we probably want to remove the base64 payload 
                # but keep the fact that a screenshot exists (name/title).
                for s in data['screenshots']:
                    if isinstance(s, dict) and 'base64' in s:
                        del s['base64']
            
            for key, value in data.items():
                self._remove_screenshots(value)
                
        elif isinstance(data, list):
            for item in data:
                self._remove_screenshots(item)

    def _truncate_fields(self, data: Any, max_log: int, max_stack: int):
        """Recursively truncate log details and stack traces."""
        if isinstance(data, dict):
            # Truncate 'details' in steps/logs
            if 'details' in data and isinstance(data['details'], str):
                if len(data['details']) > max_log:
                    data['details'] = data['details'][:max_log] + "... [TRUNCATED]"
            
            # Truncate 'stackTrace' in exceptions
            if 'stackTrace' in data and isinstance(data['stackTrace'], str):
                lines = data['stackTrace'].splitlines()
                if len(lines) > max_stack:
                    data['stackTrace'] = "\n".join(lines[:max_stack]) + f"\n... [TRUNCATED {len(lines)-max_stack} MORE LINES]"
            
            for key, value in data.items():
                self._truncate_fields(value, max_log, max_stack)
                
        elif isinstance(data, list):
            for item in data:
                self._truncate_fields(item, max_log, max_stack)
