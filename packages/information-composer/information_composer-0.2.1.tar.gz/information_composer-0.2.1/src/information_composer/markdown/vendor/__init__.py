"""
Vendor code for markdown processing.
This package contains third-party code that is bundled with the project.
The code in this package is not modified and is excluded from quality checks.
"""

# Import CommonMark for external use
from . import CommonMark

__all__ = ["CommonMark"]
