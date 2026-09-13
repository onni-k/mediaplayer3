# ==============================================================================
# MediaPlayer3
#
# File        : __init__.py
# Description : Package initialisation.
#
# Author      : MediaPlayer3 Project
# Copyright   : (C) 2026 MediaPlayer3 Project
# License     : GNU General Public License v2 (GPL-2.0)
#
# Compatible  : OpenViX, OpenATV (planned)
# Python      : 3.13+
#
# ------------------------------------------------------------------------------
# Change history
#
# 2026-07-04  Build 0001
#   - Initial version.
# ------------------------------------------------------------------------------

"""
MediaPlayer3 package.

The package intentionally performs no initialisation on import.
All runtime initialisation is handled by plugin.py.
"""

# Round 158, per direct request (a GitHub Actions autotag workflow --
# .github/workflows/autotag.yml -- needs a plain, literal version
# string it can find by regex, since it runs as a shell grep, not
# Python, and can't resolve an import): this is now the single source
# of truth for the project's own version number. project.py's own
# VERSION constant imports this value rather than defining its own
# copy, so there is only one place to update when releasing a new
# version, not two that could drift out of sync.
__version__ = "1.1.000"

__all__ = ["__version__"]

#end_of_file
