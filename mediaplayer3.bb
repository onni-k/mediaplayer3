SUMMARY = "MediaPlayer3 - A modern audio player for Enigma2 receivers"
DESCRIPTION = "A feature-rich media player for Enigma2 receivers, supporting local audio files, internet radio, podcasts, playlists, and Finnish radio EPG."
AUTHOR = "onni-k"
LICENSE = "GPL-3.0-or-later"
LIC_FILES_CHKSUM = "file://LICENSE;md5=1ebbd3e34237af26da5dc08a4e440464"

HOMEPAGE = "https://github.com/onni-k/mediaplayer3"
BUGTRACKER = "https://github.com/onni-k/mediaplayer3/issues"

PV = "1.1.000"
PR = "r0"

SRC_URI = "git://github.com/onni-k/mediaplayer3.git;branch=main;protocol=https"
SRCREV = "${AUTOREV}"

S = "${WORKDIR}/git"

# MediaPlayer3 is pure Python plus gettext translation compilation --
# both architecture-independent, so this still builds once for all
# architectures.
inherit allarch

# Round 135, per direct programmer feedback ("*.mo files should not be
# in the repo. These are added by the bitbake recipe. *.po files
# should not be shipped. They should be in 'po' folder in the root of
# the repo."): compiles each committed po/<lang>.po source into the
# .mo file Python's own gettext module actually loads at runtime
# (resources/locale/<lang>/LC_MESSAGES/MediaPlayer3.mo -- see
# localization.py's own LOCALE_PATH). Runs before do_install()'s own
# "cp -r ${S}/src/*" below, so the compiled .mo files are already in
# place inside ${S}/src by the time that copy happens; po/ itself,
# living outside src/, is never touched by that copy and so is never
# shipped in the installed package.
do_compile() {
    for lang in fi en sv de es; do
        install -d ${S}/src/resources/locale/${lang}/LC_MESSAGES
        msgfmt ${S}/po/${lang}.po -o ${S}/src/resources/locale/${lang}/LC_MESSAGES/MediaPlayer3.mo
    done
}

DEPENDS += "gettext-native"

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
