"""
Mock DaVinci Resolve client wrapper for testing.

This is a mock version that doesn't require DaVinci Resolve to be running.
"""

import logging
from typing import Any, Dict, List, Optional


logger = logging.getLogger(__name__)


class DaVinciResolveError(Exception):
    """Base exception for DaVinci Resolve related errors."""

    pass


class DaVinciResolveNotRunningError(DaVinciResolveError):
    """Raised when DaVinci Resolve is not running."""

    pass


class DaVinciResolveConnectionError(DaVinciResolveError):
    """Raised when connection to DaVinci Resolve fails."""

    pass


class DaVinciResolveClient:
    """
    A mock interface to the DaVinci Resolve API for testing.

    This class simulates the connection to DaVinci Resolve without requiring
    the actual application to be running.
    """

    def __init__(self) -> None:
        self._is_connected = False
        self._mock_projects = ["Test Project 1", "Test Project 2"]
        self._mock_timelines = ["Timeline 1", "Timeline 2"]
        self._mock_media_clips = [
            {"name": "clip1.mp4", "duration": 1000, "fps": "24"},
            {"name": "clip2.mp4", "duration": 2000, "fps": "30"},
        ]

    def connect(self) -> None:
        """Mock connect to DaVinci Resolve."""
        self._is_connected = True
        logger.info("Mock connected to DaVinci Resolve")

    def disconnect(self) -> None:
        """Mock disconnect from DaVinci Resolve."""
        self._is_connected = False
        logger.info("Mock disconnected from DaVinci Resolve")

    def is_connected(self) -> bool:
        """Check if connected to DaVinci Resolve."""
        return self._is_connected

    def _ensure_connected(self) -> None:
        """Ensure we're connected to Resolve."""
        if not self._is_connected:
            raise DaVinciResolveConnectionError("Not connected to DaVinci Resolve")

    def _ensure_project(self) -> Any:
        """Ensure we have a current project."""
        self._ensure_connected()
        return "Mock Project"

    # System Information
    def get_version(self) -> str:
        """Get DaVinci Resolve version."""
        return "DaVinci Resolve Studio 18.6.4"

    def get_current_page(self) -> str:
        """Get the current page (Edit, Color, Fusion, etc.)."""
        return "edit"

    def switch_page(self, page: str) -> bool:
        """Switch to a specific page."""
        valid_pages = [
            "media",
            "cut",
            "edit",
            "fusion",
            "color",
            "fairlight",
            "deliver",
        ]
        if page.lower() not in valid_pages:
            raise ValueError(f"Invalid page. Must be one of: {', '.join(valid_pages)}")
        return True

    # Project Management
    def list_projects(self) -> List[str]:
        """List all projects in the current database."""
        return self._mock_projects

    def get_current_project_name(self) -> Optional[str]:
        """Get the name of the currently open project."""
        return "Test Project 1"

    def open_project(self, name: str) -> bool:
        """Open a project by name."""
        if name not in self._mock_projects:
            raise ValueError(
                f"Project '{name}' not found. Available: {', '.join(self._mock_projects)}"
            )
        return True

    def create_project(self, name: str) -> bool:
        """Create a new project."""
        if name in self._mock_projects:
            raise ValueError(f"Project '{name}' already exists")
        self._mock_projects.append(name)
        return True

    # Timeline Management
    def list_timelines(self) -> List[str]:
        """List all timelines in the current project."""
        return self._mock_timelines

    def get_current_timeline_name(self) -> Optional[str]:
        """Get the name of the current timeline."""
        return "Timeline 1"

    def create_timeline(self, name: str) -> bool:
        """Create a new timeline."""
        self._mock_timelines.append(name)
        return True

    def switch_timeline(self, name: str) -> bool:
        """Switch to a timeline by name."""
        if name not in self._mock_timelines:
            raise ValueError(f"Timeline '{name}' not found")
        return True

    # Media Pool Management
    def list_media_clips(self) -> List[Dict[str, Any]]:
        """List all clips in the media pool root folder."""
        return self._mock_media_clips

    def import_media(self, file_path: str) -> bool:
        """Import a media file into the media pool."""
        self._mock_media_clips.append({
            "name": file_path.split("/")[-1],
            "duration": 1000,
            "fps": "24"
        })
        return True