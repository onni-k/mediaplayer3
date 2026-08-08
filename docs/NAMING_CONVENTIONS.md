# MediaPlayer3

# Naming Conventions

Version: 0.1

Status: Build 0007 CONFIRMED COMPLETE (device test round 13 -- OpenViX, OpenATV, openPLI, OpenBH)

---

# 1. Purpose

This document defines the naming conventions used throughout the
MediaPlayer3 project.

Consistent naming improves readability, maintainability and long-term
project stability.

All new code should follow these conventions.

---

# 2. General Principles

Names should be:

- Short
- Descriptive
- Consistent
- Predictable

Avoid abbreviations unless they are widely accepted.

Examples:

Good

PlaybackController

Compatibility

MainScreen

Logger

Avoid

PBController

CompatMgr

MainUI

Cfg

---

# 3. File Names

Python module names shall:

- Use lowercase letters.
- Use underscores where appropriate.
- Be concise.

Examples

config.py

logger.py

compatibility.py

systeminfo.py

project.py

version.py

constants.py

features.py

playback_controller.py

service_controller.py

mainscreen.py

browserscreen.py

settingsscreen.py

playbackinfo_screen.py

developer_screen.py

mainmenu.py

---

# 4. Class Names

Public classes shall use PascalCase.

Examples

ConfigurationManager

PlaybackController

ServiceController

MainScreen

BrowserScreen

SettingsScreen

PlaybackInfoScreen

DeveloperScreen

MainMenu

---

# 5. Method Names

Methods shall use snake_case.

Examples

load()

save()

play()

pause()

resume()

stop()

open_browser()

show_settings()

export_log()

---

# 6. Variables

Variable names shall use snake_case.

Names should clearly describe their purpose.

Examples

current_service

current_directory

selected_file

playback_state

logger_instance

Avoid:

tmp

var1

test

data

Unless their meaning is immediately obvious.

---

# 7. Constants

Constants shall use UPPER_CASE.

Examples

DEFAULT_TIMEOUT

DEFAULT_DIRECTORY

MAX_LOG_SIZE

SUPPORTED_EXTENSIONS

BUILD_NUMBER

VERSION_STRING

---

# 8. Documentation

Specification documents shall follow these naming conventions.

Examples

ARCHITECTURE.md

BUILD_0004_PLAN.md

SCREEN_NAVIGATION.md

LOGGER_SPEC.md

CONFIG_SPEC.md

PLAYBACK_CONTROLLER_SPEC.md

MAINSCREEN_SPEC.md

Naming shall remain consistent throughout the project.

---

# 9. Logging

Logger messages should:

- Be concise.
- Be descriptive.
- Be written in English.
- Describe completed or ongoing operations.

Examples

Playback started.

Playback paused.

Playback resumed.

Playback stopped.

BrowserScreen opened.

Configuration loaded.

Avoid vague messages such as:

Done.

Error.

OK.

---

# 10. Version Naming

Development versions shall follow:

Major.Minor.Patch-dev

Example

0.4.0-dev

Each version is associated with:

Build Number

Internal Revision (optional)

Example

Version

0.4.0-dev

Build

0004

Revision

1

---

# 11. Future Guidelines

New modules shall follow the naming conventions defined in this
document.

Exceptions should be documented in HISTORY.md together with the reason
for the deviation.

---

# 12. Acceptance Criteria

Naming conventions are considered satisfied when:

- Module names are consistent.
- Public classes use PascalCase.
- Methods use snake_case.
- Constants use UPPER_CASE.
- Documentation follows the defined naming scheme.
- Logger messages remain consistent.
- Version numbering follows the project standard.

---

# End of File
