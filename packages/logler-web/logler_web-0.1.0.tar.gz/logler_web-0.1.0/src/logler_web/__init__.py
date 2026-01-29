"""
Logler Web - Web interface for log viewing with thread tracking and analysis.
"""

__version__ = "0.1.0"

from .app import create_app, app

__all__ = ["create_app", "app", "__version__"]
