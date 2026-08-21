SUMMARY = "MediaPlayer3 - A modern audio player for Enigma2 receivers"
DESCRIPTION = "A feature-rich media player for Enigma2 receivers, supporting local audio files, internet radio, podcasts, playlists, and Finnish radio EPG."
AUTHOR = "onni-k"
LICENSE = "GPL-3.0-or-later"
LIC_FILES_CHKSUM = "file://LICENSE;md5=0fca51bc5e55e5b8ac32567bbd288c13"

HOMEPAGE = "https://github.com/onni-k/mediaplayer3"
BUGTRACKER = "https://github.com/onni-k/mediaplayer3/issues"

PV = "1.0.0"
PR = "r0"

SRC_URI = "git://github.com/onni-k/mediaplayer3.git;branch=main;protocol=https"
SRCREV = "${AUTOREV}"

S = "${WORKDIR}/git"

# MediaPlayer3 is a pure Python package, no compilation needed
inherit allarch

# Install Python files to Enigma2 plugin directory
do_install() {
    install -d ${D}/usr/lib/enigma2/python/Plugins/Extensions/MediaPlayer3
    cp -r ${S}/src/* ${D}/usr/lib/enigma2/python/Plugins/Extensions/MediaPlayer3/
}

# Package dependencies
RDEPENDS_${PN} = "python3-core enigma2"

# MediaPlayer3 uses only Python standard library, no additional Python packages needed
RPROVIDES_${PN} = "mediaplayer3"

# Changelog and documentation
FILES_${PN} += "/usr/lib/enigma2/python/Plugins/Extensions/MediaPlayer3/*"
