from typing import List, Optional, Any
from pydantic import BaseModel, Field

class Screenshot(BaseModel):
    name: str = "screenshot"
    base64: str

class TestStep(BaseModel):
    stepNumber: int
    name: str = "" # Can be empty if just a status
    status: str
    timestamp: str = ""
    details: str = ""

class TestException(BaseModel):
    type: str = "Unknown"
    message: str = ""
    stackTrace: str = ""

class TestCase(BaseModel):
    name: str
    description: str = ""
    status: str
    severity: str = "normal"
    startTime: Any = None
    endTime: Any = None
    duration: str = ""
    categories: List[str] = []
    authors: List[str] = []
    devices: List[str] = []
    steps: List[TestStep] = []
    screenshots: List[Screenshot] = []
    exception: Optional[TestException] = None

class TestSuite(BaseModel):
    name: str
    status: str = "passed"
    testCases: List[TestCase] = []

class ReportSummary(BaseModel):
    totalTests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    passRate: str = "0%"

class ReportInfo(BaseModel):
    reportName: str = "Extent Report"
    title: str = ""
    startTime: str = ""
    endTime: str = ""

class ExtentReport(BaseModel):
    reportInfo: ReportInfo = Field(default_factory=ReportInfo)
    summary: ReportSummary = Field(default_factory=ReportSummary)
    testSuites: List[TestSuite] = []
    systemInfo: dict = {}
