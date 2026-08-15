# ==============================================================================
#
# MediaPlayer3
#
# File        : yle_credentials.py
#
# Description :
#
#     Resolves the app_id/app_key YleTeletextScheduleProvider needs,
#     preferring the user's own Settings-provided pair (Settings ->
#     Yle EPG app_id/app_key, tunnus.yle.fi/api-avaimet) and falling
#     back to a bundled default otherwise -- so Yle Radio EPG works
#     out of the box without requiring signup first, exactly the same
#     shape as podcast_providers/podcastindex/podcastindex_provider.py's
#     own _resolveCredentials()/_deobfuscate(), including the same
#     obfuscation reasoning: this is deliberately NOT real security
#     (this project is publicly distributed, so anyone who reads this
#     source file has the deobfuscation logic too) -- it only avoids
#     the bundled credentials being an immediately greppable plaintext
#     string. A user's own key (Settings) is the only genuinely
#     private option, and using one also avoids every MediaPlayer3
#     installation sharing (and potentially exhausting) the same
#     bundled key's rate limit.
#
#     BUILD_0010_PLAN.md originally asked for the key to be read from
#     a local file (yle.txt) instead of manual Settings entry. Device
#     test round 16 changed this directly: bundle a default the same
#     way Podcast Index already is, rather than adding a second,
#     different "read a credential from a file" mechanism -- Settings
#     entry manual-override kept exactly as it already was, for anyone
#     who wants to use their own key.
#
#     _DEFAULT_YLE_APP_ID_OBFUSCATED / _DEFAULT_YLE_APP_KEY_OBFUSCATED
#     below are the maintainer's own real credentials (device test
#     round 17), generated via generate_yle_obfuscated_key.py (project
#     root, not shipped with the plugin) -- never received or stored
#     in plaintext by Claude at any point; the round 17 message
#     supplying them has since been generated straight into their
#     obfuscated form here. If resolveCredentials() ever needs to fall
#     back further (both constants empty, or deobfuscation fails), it
#     returns None -- EPG registration is skipped with a logged
#     reason, never a crash, same as before any bundled default
#     existed.
#
# Implements :
#
#     BUILD_0010_PLAN.md "YLE API Key" (as amended, device test round
#     16 -- see this file's own header above)
#
# Project :
#
#     MediaPlayer3
#
# License :
#
#     GPL-2.0-or-later
#
# ------------------------------------------------------------------------------
# Change history
#
# 2026-08-10  Build 0010 (round 16)
#   - Initial version. Bundled credential constants shipped as empty
#     placeholders -- no real Yle app_id/app_key available yet.
#
# 2026-08-10  Build 0010 (round 17)
#   - Maintainer supplied a real Yle app_id/app_key; obfuscated via
#     generate_yle_obfuscated_key.py and filled in below.
# ------------------------------------------------------------------------------

"""
yle_credentials -- resolves the Yle Teksti-TV app_id/app_key pair,
preferring the user's own Settings-provided credentials over a
bundled (obfuscated) default. See this file's own header for the
obfuscation/attribution details.
"""

from __future__ import annotations

import base64
from typing import Optional, Tuple

from ...config import cfg
from ...logger import logger

# Must match generate_yle_obfuscated_key.py's own _OBFUSCATION_PAD
# exactly -- see that script's own docstring.
_OBFUSCATION_PAD = b"MediaPlayer3-YleTeletext-Build0010"

# Bundled default credentials (obfuscated -- see _deobfuscate() and
# this file's own header). Generated via generate_yle_obfuscated_key.py
# from the maintainer's own Yle app_id/app_key (tunnus.yle.fi/api-
# avaimet), device test round 17. A user's own app_id/app_key in
# Settings always takes priority when provided; see
# resolveCredentials().
_DEFAULT_YLE_APP_ID_OBFUSCATED = "KVRXXgQxCAAYUkdWSTxcBGZXWlxAXUgRGCZEXFsAAQM="
_DEFAULT_YLE_APP_KEY_OBFUSCATED = "KFIBWlc2XAA="


def _deobfuscate(value: str) -> str:
    """
    Reverses the XOR+base64 obfuscation described in this file's own
    header -- identical scheme to podcastindex_provider.py's own
    _deobfuscate(), just a different pad. Not real encryption -- see
    that header for why this is only meant to avoid a plaintext
    credential string, not to provide genuine secrecy in a publicly
    distributed plugin.
    """

    xored = base64.b64decode(value)

    data = bytes(byte ^ _OBFUSCATION_PAD[i % len(_OBFUSCATION_PAD)] for i, byte in enumerate(xored))

    return data.decode("utf-8")


def resolveCredentials() -> Optional[Tuple[str, str]]:
    """
    Returns (app_id, app_key), preferring the user's own
    Settings-provided credentials (Settings -> Yle EPG app_id/app_key)
    over the bundled default. Returns None when neither a user-
    provided pair nor a usable bundled default is available -- the
    caller (finland_radio_epg_registry.py) treats that exactly like
    today's "not configured" case: EPG registration for this station
    is skipped, with a logged reason, never a crash.
    """

    user_app_id = cfg.epg.yle_app_id.value

    user_app_key = cfg.epg.yle_app_key.value

    if user_app_id and user_app_key:

        return user_app_id, user_app_key

    if not _DEFAULT_YLE_APP_ID_OBFUSCATED or not _DEFAULT_YLE_APP_KEY_OBFUSCATED:

        return None

    try:
        return (
            _deobfuscate(_DEFAULT_YLE_APP_ID_OBFUSCATED),
            _deobfuscate(_DEFAULT_YLE_APP_KEY_OBFUSCATED),
        )

    except Exception as error:

        # Build 0010 -- deliberately does not include `error` itself
        # here, in case a future change to the obfuscation format
        # made it include fragment data (same reasoning as
        # podcastindex_provider.py's own equivalent except clause).
        logger.warning("[YleCredentials] Bundled default credentials could not be read.")

        return None


# ==============================================================================
# End of file
# ==============================================================================
