# ==============================================================================
#
# MediaPlayer3
#
# File        : systeminfo.py
#
# Description :
#
#     Collects system information for logging, diagnostics and
#     Developer Mode.
#
# Implements :
#
#     SYSTEMINFO_SPEC.md v0.1
#
# Architecture :
#
#     ARCHITECTURE.md v0.2
#
# Project :
#
#     MediaPlayer3
#
# License :
#
#     GPL-2.0-or-later
#
# ==============================================================================

from __future__ import annotations

import platform
from typing import Any, Dict

from .compatibility import compatibility
from .logger import logger


class SystemInfo:
    """
    Collect diagnostic information about the current runtime environment.
    """

    SPECIFICATION_VERSION = "0.1"
    ARCHITECTURE_VERSION = "0.3"

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def __init__(self) -> None:

        self._initialized = False

        self._log("Created")

        self._initialize()

    # ------------------------------------------------------------------

    def _initialize(self) -> None:

        self._log("Initializing")

        self._initialized = True

        self._log("Ready")

    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:

        logger.info("[SystemInfo] %s", message)

# End of Part 1
    # ------------------------------------------------------------------
    # System Information
    # ------------------------------------------------------------------

    def getPlatformInformation(self) -> Dict[str, Any]:
        """
        Return general platform information.
        """

        return {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        }

    # ------------------------------------------------------------------

    def getPythonInformation(self) -> Dict[str, Any]:
        """
        Return Python runtime information.
        """

        return {
            "version": compatibility.getPythonVersion(),
            "implementation": platform.python_implementation(),
            "compiler": platform.python_compiler(),
        }

    # ------------------------------------------------------------------

    def getCompatibilityInformation(self) -> Dict[str, Any]:
        """
        Return compatibility layer information.
        """

        return compatibility.getCompatibilityReport()

    # ------------------------------------------------------------------

    def getApplicationInformation(self) -> Dict[str, Any]:
        """
        Return MediaPlayer3 application information.

        Additional build information may be added in future builds.
        """

        return {
            "application": "MediaPlayer3",
            "architecture": self.ARCHITECTURE_VERSION,
            "specification": self.SPECIFICATION_VERSION,
        }

    # ------------------------------------------------------------------

    def getSummary(self) -> Dict[str, Any]:
        """
        Return a summarized system overview.
        """

        return {
            "application": self.getApplicationInformation(),
            "platform": self.getPlatformInformation(),
            "python": self.getPythonInformation(),
            "compatibility": self.getCompatibilityInformation(),
        }

# End of Part 2
    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def dump(self) -> Dict[str, Any]:
        """
        Return complete diagnostic information.

        This method is intended for Developer Mode,
        logging and troubleshooting.
        """

        return self.getSummary()

    # ------------------------------------------------------------------

    def logSystemInformation(self) -> None:
        """
        Write system information to the application log.
        """

        info = self.dump()

        self._log("========== System Information ==========")

        for section, values in info.items():

            self._log(section)

            if isinstance(values, dict):

                for key, value in values.items():
                    self._log(f"    {key}: {value}")

            else:
                self._log(f"    {values}")

        self._log("========================================")

    # ------------------------------------------------------------------

    def isInitialized(self) -> bool:
        """
        Return initialization status.
        """

        return self._initialized

    # ------------------------------------------------------------------

    def getCompatibility(self) -> Dict[str, Any]:
        """
        Return compatibility report.

        Convenience wrapper around Compatibility.
        """

        return compatibility.getCompatibilityReport()

    # ------------------------------------------------------------------

    def getPlatformName(self) -> str:
        """
        Return detected platform name.
        """

        report = compatibility.getCompatibilityReport()

        return report.get("platform", "Unknown")

# End of Part 3
    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def cleanup(self) -> None:
        """
        Release SystemInfo resources.

        Build 0003 currently has no external resources to release,
        but the method is provided for API consistency.
        """

        self._log("Closing")

        self._initialized = False

        self._log("Closed")

    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        """
        Return readable object representation.
        """

        return (
            "SystemInfo("
            f"initialized={self._initialized})"
        )


# ----------------------------------------------------------------------
# Global instance
# ----------------------------------------------------------------------

systeminfo = SystemInfo()


# ==============================================================================
#
# Build Notes
#
# Build 0003 introduces the first diagnostic layer for MediaPlayer3.
#
# Responsibilities:
#
#   - Collect runtime information
#   - Collect platform information
#   - Collect compatibility information
#   - Provide diagnostic reports
#   - Write startup diagnostics to the application log
#
# Future builds may extend this module with:
#
#   - Memory statistics
#   - CPU information
#   - Storage information
#   - Active service information
#   - Decoder information
#   - Network information
#   - Plugin information
#   - Performance statistics
#
# The public API should remain stable whenever possible.
#
# ==============================================================================


# ==============================================================================
# End of file
# ==============================================================================
