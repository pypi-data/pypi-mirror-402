from pathlib import Path
from bs4 import BeautifulSoup
import json
import re
from typing import Optional, Dict, List, Any
from .base import BaseParser

class ExtentHtmlParser(BaseParser):
    """Parser for Extent Spark HTML reports."""
    
    def __init__(self, report_path: str):
        self.report_path = Path(report_path)
        if self.report_path.is_dir():
            self.report_path = self.report_path / "index.html"
    
    def parse(self) -> dict:
        """Parse the HTML report and extract test data."""
        if not self.report_path.exists():
            raise FileNotFoundError(f"Report file not found: {self.report_path}")

        with open(self.report_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        
        return {
            "reportInfo": self._extract_report_info(soup),
            "summary": self._extract_summary(soup),
            "testSuites": self._extract_test_suites(soup),
            "systemInfo": self._extract_system_info(soup)
        }
    
    def _extract_report_info(self, soup: BeautifulSoup) -> dict:
        """Extract report metadata."""
        title = soup.find('title')
        report_name = soup.find('span', class_='report-name')
        
        # Try to find timestamps from the report
        start_time = self._find_timestamp(soup, 'start')
        end_time = self._find_timestamp(soup, 'end')
        
        return {
            "reportName": report_name.text.strip() if report_name else "Extent Report",
            "title": title.text.strip() if title else "",
            "startTime": start_time,
            "endTime": end_time
        }
    
    def _extract_summary(self, soup: BeautifulSoup) -> dict:
        """Extract test summary statistics."""
        # Look for dashboard statistics
        stats: Dict[str, int] = {}
        
        # Common patterns in Extent Spark reports
        stat_cards = soup.find_all('div', class_='card-panel')
        for card in stat_cards:
            text = card.get_text(strip=True)
            if 'passed' in text.lower():
                stats['passed'] = self._extract_number(text)
            elif 'failed' in text.lower():
                stats['failed'] = self._extract_number(text)
            elif 'skipped' in text.lower():
                stats['skipped'] = self._extract_number(text)
        
        total = stats.get('passed', 0) + stats.get('failed', 0) + stats.get('skipped', 0)
        pass_rate = f"{(stats.get('passed', 0) / total * 100):.1f}%" if total > 0 else "0%"
        
        return {
            "totalTests": total,
            "passed": stats.get('passed', 0),
            "failed": stats.get('failed', 0),
            "skipped": stats.get('skipped', 0),
            "passRate": pass_rate
        }
    
    def _extract_test_suites(self, soup: BeautifulSoup) -> list:
        """Extract test suites and their test cases."""
        suites = []
        
        # Find test containers - varies by Extent version
        test_containers = soup.find_all('li', class_='test-item')
        
        for container in test_containers:
            suite = self._parse_test_container(container)
            if suite:
                suites.append(suite)
        
        return suites
    
    def _parse_test_container(self, container) -> Optional[dict]:
        """Parse a single test container."""
        name_elem = container.find('span', class_='test-name')
        if not name_elem:
            return None
        
        status_class = container.get('class', [])
        status = 'passed'
        if 'fail' in ' '.join(status_class):
            status = 'failed'
        elif 'skip' in ' '.join(status_class):
            status = 'skipped'
        elif 'pass' in ' '.join(status_class):
            status = 'passed'
        else:
             # Fallback if class doesn't explicitly say pass/fail (rare)
             status_span = container.find('span', class_='status')
             if status_span:
                 status = status_span.text.lower()

        # Extract steps
        steps = []
        step_elements = container.find_all('li', class_='log-item') # Varies by version, sometimes tr inside table
        
        # Fallback for table based logs (common in v3/v4/Spark)
        if not step_elements:
             rows = container.find_all('tr')
             for row in rows:
                 # Check if it's a log row
                 if row.find('td', class_='status'):
                     step_elements.append(row)

        for i, step_elem in enumerate(step_elements, 1):
            steps.append(self._parse_step(step_elem, i))
        
        return {
            "name": name_elem.text.strip(),
            "status": status,
            "testCases": [{
                "name": name_elem.text.strip(),
                "status": status,
                "steps": steps,
                "screenshots": self._extract_screenshots(container)
            }]
        }
    
    def _parse_step(self, step_elem, step_number: int) -> dict:
        """Parse a single test step."""
        status_elem = step_elem.find('span', class_='status') or step_elem.find('td', class_='status')
        status = status_elem.text.strip().lower() if status_elem else 'info'
        
        details_elem = step_elem.find('div', class_='step-details') or step_elem.find('td', class_='step-details')
        if not details_elem:
            # Fallback for simple tables
            tds = step_elem.find_all('td')
            if len(tds) > 1:
                details_elem = tds[-1]

        details = details_elem.text.strip() if details_elem else ""
        
        return {
            "stepNumber": step_number,
            "status": status,
            "details": details
        }
    
    def _extract_system_info(self, soup: BeautifulSoup) -> dict:
        """Extract system/environment information."""
        system_info = {}
        
        # Look for system info table
        info_table = soup.find('div', class_='sysenv-container')
        if info_table:
             table = info_table.find('table')
             if table:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        key = cells[0].text.strip()
                        value = cells[1].text.strip()
                        system_info[key] = value
        
        return system_info
    
    def _extract_number(self, text: str) -> int:
        """Extract number from text."""
        match = re.search(r'\d+', text)
        return int(match.group()) if match else 0
    
    def _find_timestamp(self, soup: BeautifulSoup, time_type: str) -> str:
        """Find timestamp in report."""
        # Implementation depends on Extent version
        # Placeholder as per guide
        return ""

    def _extract_screenshots(self, container) -> List[Dict[str, str]]:
        """Extract screenshots from HTML container."""
        screenshots = []
        
        # Look for <a> tags with data-featherlight='image' (Spark reports)
        # or similar image links
        
        # Spark / v4+
        img_links = container.find_all('a', {'data-featherlight': 'image'})
        if not img_links:
            # Fallback patterns
            img_links = container.find_all('a', class_='view-screenshot')
        
        for link in img_links:
            href = link.get('href', '')
            # If href is base64
            if href.startswith('data:image'):
                screenshots.append({
                    "name": "screenshot",
                    "base64": href.split(',')[-1]
                })
            # If standard <img> tags inside
            img = link.find('img')
            if img:
                src = img.get('src', '')
                if src.startswith('data:image'):
                     screenshots.append({
                        "name": "screenshot",
                        "base64": src.split(',')[-1]
                     })

        # Look for raw img tags if not in links
        imgs = container.find_all('img', class_='r-img')
        for img in imgs:
             src = img.get('src', '')
             if src.startswith('data:image'):
                 screenshots.append({
                    "name": "embedded-screenshot",
                    "base64": src.split(',')[-1]
                 })

        return screenshots
