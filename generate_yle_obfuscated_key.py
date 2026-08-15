#!/usr/bin/env python3
"""
generate_yle_obfuscated_key.py

Standalone helper -- NOT part of the shipped plugin (lives at the
project root, not under src/, so it never gets bundled into the
distributed zip).

Generates the obfuscated (XOR + base64) app_id/app_key pair that
src/epg_providers/Finland_radio_epg/yle_credentials.py bundles as the
default YLE Teksti-TV credentials, exactly mirroring how
src/podcast_providers/podcastindex/podcastindex_provider.py already
obfuscates its own bundled Podcast Index key/secret -- same
_OBFUSCATION_PAD scheme, same base64(XOR(...)) encoding, so
yle_credentials.py's own _deobfuscate() can read the result directly.

This is deliberately NOT real security -- see yle_credentials.py's own
header for why (this project is publicly distributed, so anyone who
reads the source has the deobfuscation logic too). It only avoids the
credentials being an immediately greppable plaintext string in the
repository.

Usage:

    python3 generate_yle_obfuscated_key.py <app_id> <app_key>

Paste the two printed lines into yle_credentials.py's own
_DEFAULT_YLE_APP_ID_OBFUSCATED / _DEFAULT_YLE_APP_KEY_OBFUSCATED
constants. Your real app_id/app_key are never written anywhere by
this script and are not needed again after this step.
"""

import base64
import sys

# Must match yle_credentials.py's own _OBFUSCATION_PAD exactly, or the
# generated strings won't deobfuscate back to the right value.
_OBFUSCATION_PAD = b"MediaPlayer3-YleTeletext-Build0010"


def obfuscate(value: str) -> str:

    data = value.encode("utf-8")

    xored = bytes(byte ^ _OBFUSCATION_PAD[i % len(_OBFUSCATION_PAD)] for i, byte in enumerate(data))

    return base64.b64encode(xored).decode("ascii")


def main() -> None:

    if len(sys.argv) != 3:

        print(f"Usage: {sys.argv[0]} <app_id> <app_key>", file=sys.stderr)

        sys.exit(1)

    app_id, app_key = sys.argv[1], sys.argv[2]

    print(f'_DEFAULT_YLE_APP_ID_OBFUSCATED = "{obfuscate(app_id)}"')

    print(f'_DEFAULT_YLE_APP_KEY_OBFUSCATED = "{obfuscate(app_key)}"')


if __name__ == "__main__":

    main()
