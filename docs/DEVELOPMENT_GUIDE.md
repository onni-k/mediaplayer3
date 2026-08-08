# MediaPlayer3

# Development Guide

Version: 0.1

Status: Build 0007 CONFIRMED COMPLETE (device test round 13 -- OpenViX, OpenATV, openPLI, OpenBH)

---

# 1. Purpose

This document describes the recommended development workflow for
MediaPlayer3.

Its purpose is to ensure that all future development follows the same
architecture, coding style and documentation practices.

It complements ARCHITECTURE.md and the individual specification
documents.

---

# 2. Development Principles

Every new feature should follow these principles:

- Keep modules small.
- One responsibility per module.
- Reuse existing interfaces whenever practical.
- Avoid platform-specific code outside Compatibility.
- Document architectural changes.

Development should prioritise maintainability over short-term
convenience.

---

# 3. Recommended Workflow

The recommended development sequence is:

Idea

↓

Architecture review

↓

Specification update

↓

Implementation

↓

Testing

↓

Documentation update

↓

Release checklist

↓

Build freeze

Implementation should begin only after responsibilities are clearly
defined.

---

# 4. Adding a New Screen

Before implementing a new Screen:

- Update SCREEN_NAVIGATION.md.
- Create or update the corresponding *_SPEC.md.
- Verify Screen responsibilities.
- Verify Controller dependencies.

A Screen shall:

- Contain user interface logic only.
- Never implement business logic.
- Never access platform-specific functionality directly.

---

# 5. Adding a New Controller

Before implementing a new Controller:

- Define its responsibility.
- Verify it does not duplicate existing functionality.
- Update ARCHITECTURE.md if necessary.

Controllers shall:

- Contain business logic.
- Use Core modules through public interfaces.
- Never display user interface elements.

---

# 6. Adding a New Core Module

Before implementing a new Core module:

- Verify that similar functionality does not already exist.
- Define a clear public interface.
- Document the module in a corresponding *_SPEC.md file.

Core modules shall:

- Provide reusable services.
- Remain independent of the Screen Layer.
- Avoid platform-specific implementations whenever practical.

---

# 7. Logging

Every new module shall follow LOGGER_SPEC.md.

Typical lifecycle:

Initialize

↓

Running

↓

Cleanup

↓

Closed

Developer logging should support troubleshooting without affecting
normal application behaviour.

---

# 8. Testing

Before freezing a Build:

- Review documentation.
- Verify architecture.
- Test primary workflows.
- Review logging.
- Execute RELEASE_CHECKLIST.md.

Testing should include both functional behaviour and architectural
compliance.

---

# 9. Documentation

Documentation is part of the implementation.

Whenever architecture changes:

- Update ARCHITECTURE.md.
- Update PROJECT_STRUCTURE.md if required.
- Update SCREEN_NAVIGATION.md if navigation changes.
- Update the relevant *_SPEC.md files.
- Update CHANGELOG.md.
- Update HISTORY.md if architectural decisions change.

Documentation should remain synchronized with the implementation.

---

# 10. Build Workflow

Each Build should follow this lifecycle:

Planning

↓

Documentation

↓

Implementation

↓

Testing

↓

Bug Fixing

↓

Build Freeze

↓

Release

↓

Next Build Planning

Every completed Build provides the foundation for the next Build.

---

# 11. Long-Term Goals

MediaPlayer3 aims to be:

- Modular
- Maintainable
- Portable
- Well documented
- Easy to extend
- Easy to debug

Development decisions should support these goals whenever practical.

---

# 12. Acceptance Criteria

Development practices are considered compliant when:

- Architecture is respected.
- Module responsibilities remain clear.
- Documentation is up to date.
- Logging follows LOGGER_SPEC.md.
- Platform-specific code remains isolated.
- New functionality integrates cleanly with the existing architecture.
- RELEASE_CHECKLIST.md has been completed before Build Freeze.

---

# End of File
