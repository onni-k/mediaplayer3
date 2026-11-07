# -*- coding: utf-8 -*-
"""
Receiver region detection (1.5.000): the ISO country code of the receiver's time zone, read from
/etc/enigma2/settings (`config.timezone.val=Europe/Helsinki` or just `config.timezone.val=Helsinki`)
and /usr/share/zoneinfo/zone.tab. Used as the default Internet Radio region when none is set.
"""

import os
from typing import Optional

SETTINGS_FILE = "/etc/enigma2/settings"
ZONE_TABS = ("/usr/share/zoneinfo/zone.tab", "/usr/share/zoneinfo/zone1970.tab")


def readTimezone(settings_file: str = SETTINGS_FILE) -> str:
    """The configured time zone ("Europe/Helsinki" or "Helsinki"), '' when not found."""

    try:
        with open(settings_file, "r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                line = line.strip()
                if line.startswith("config.timezone.val="):
                    return line.split("=", 1)[1].strip()
    except OSError:
        pass

    return ""


def countryCodeForTimezone(timezone: str, zone_tabs=ZONE_TABS) -> Optional[str]:
    """ISO 3166 code of the country a time zone belongs to (accepts 'Helsinki' as well as 'Europe/Helsinki')."""

    timezone = (timezone or "").strip()

    if not timezone:
        return None

    short = timezone.rsplit("/", 1)[-1].lower()
    partial = None

    for path in zone_tabs:

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as handle:
                rows = [line.split("\t") for line in handle if line.strip() and not line.startswith("#")]
        except OSError:
            continue

        for row in rows:

            if len(row) < 3:
                continue

            zone = row[2].strip()

            if zone.lower() == timezone.lower():
                return row[0].strip().upper()

            if partial is None and zone.rsplit("/", 1)[-1].lower() == short:
                partial = row[0].strip().upper()

    return partial


def detectCountryCode(settings_file: str = SETTINGS_FILE) -> Optional[str]:

    return countryCodeForTimezone(readTimezone(settings_file))
