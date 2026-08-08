# MediaPlayer3

# Configuration Specification

Version: 0.3

Status: Build 0007 CONFIRMED COMPLETE (device test round 13 -- OpenViX, OpenATV, openPLI, OpenBH)

---

# 1. Purpose

The Configuration module provides centralized configuration management
for MediaPlayer3.

It is responsible for loading, validating, storing and saving all
application settings.

Configuration management is implemented in config.py.

---

# 2. Responsibilities

ConfigurationManager is responsible for:

- Loading configuration
- Saving configuration
- Providing default values
- Validating configuration values
- Managing configuration version
- Providing public configuration access

ConfigurationManager is NOT responsible for:

- Playback
- User interface
- Platform detection
- Logging implementation
- Service control

---

# 3. Architecture

Configuration is implemented as a Core module.

Screen Layer

↓

Controller Layer

↓

ConfigurationManager

ConfigurationManager never depends on Screen classes.

Controllers and Screens access configuration only through the public
ConfigurationManager interface.

---

# 4. Public Interface

ConfigurationManager provides the following public operations.

load()

save()

get()

set()

validate()

reset_defaults()

get_version()

Future public operations should remain backward compatible whenever
practical.

---

# 5. Configuration Categories

Configuration is divided into logical categories.

General

Playback

User Interface (Build 0005 -- progress bar/elapsed/remaining time/
playback state display toggles)

Appearance (Build 0006 -- skin, theme)

Radio (Build 0007 -- default country/language, navigation mode,
history size)

Logging

Developer

Future categories may be added without changing the public interface.

---

# 6. Configuration Storage

Configuration shall be stored independently of the application code.

The storage implementation may change in future versions without
changing the public ConfigurationManager interface.

ConfigurationManager is responsible for:

- Reading configuration
- Writing configuration
- Detecting missing values
- Applying default values

Configuration storage details shall remain internal to the module.

---

# 7. Validation

Every configuration value shall be validated before being accepted.

Invalid values shall:

- Be rejected, or
- Be replaced with the default value

Validation shall never terminate the application.

Validation errors should be written to the application log.

---

# 8. Configuration Version

Configuration contains an internal version number.

Example

Configuration Version

1

Future versions may automatically migrate older configurations.

Migration shall preserve user settings whenever practical.

---

# 9. Default Values

Every configuration entry shall have a documented default value.

ConfigurationManager is responsible for restoring defaults when
requested.

Factory defaults shall remain independent of platform-specific
behaviour.

---

# 10. Logging

ConfigurationManager follows LOGGER_SPEC.md.

Typical lifecycle logging:

```
ConfigurationManager initializing.

Loading configuration.

Validating configuration.

Configuration loaded.

Saving configuration.

Configuration saved.
```

Typical warning logging:

```
Invalid configuration value.

Missing configuration entry.

Using default value.
```

Developer Mode VERBOSE

Additionally:

- Configuration version
- Individual value changes
- Validation details
- Migration operations (future)

---

# 11. Future Extensions

ConfigurationManager is designed for future expansion.

Possible future additions:

- Configuration import
- Configuration export
- Automatic backup
- Multiple user profiles
- Profile switching
- Configuration migration
- Configuration checksum
- Reset selected category

Future extensions should not require changes to the public interface.

---

# 12. Acceptance Criteria

ConfigurationManager is considered complete when:

- Configuration loads successfully.
- Configuration saves successfully.
- Invalid values are handled safely.
- Default values are available for every setting.
- Configuration version is maintained.
- Logging follows LOGGER_SPEC.md.
- ConfigurationManager contains no user interface code.
- ConfigurationManager contains no platform-specific code.

---

# End of File
