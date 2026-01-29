from abc import ABC, abstractmethod

class BaseParser(ABC):
    """Abstract base class for Extent Report parsers."""
    
    @abstractmethod
    def parse(self) -> dict:
        """Parse the report and return a dictionary with standardized structure."""
        pass
