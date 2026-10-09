SUMMARY = "MediaPlayer3 - A modern audio player for Enigma2 receivers"
DESCRIPTION = "A feature-rich media player for Enigma2 receivers, supporting local audio files, internet radio, podcasts, playlists, and Finnish radio EPG."
AUTHOR = "onni-k"
LICENSE = "GPL-3.0-or-later"
LIC_FILES_CHKSUM = "file://LICENSE;md5=1ebbd3e34237af26da5dc08a4e440464"

HOMEPAGE = "https://github.com/onni-k/mediaplayer3"
BUGTRACKER = "https://github.com/onni-k/mediaplayer3/issues"

PV = "1.3.000"
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
#
# Round 201, upgraded from round 200's RRECOMMENDS: a real device log
# confirmed a receiver (OpenViX) whose Python build genuinely lacks
# sqlite3, and RRECOMMENDS turned out to be too weak in practice --
# the user's own installed build never got it pulled in at all. A real
# published installer for another Enigma2 plugin targeting this same
# "Opensource" image family (MultiStalker Pro, github.com/biko-73/
# Multi-Stalker, pro/installer.sh) was checked directly and confirmed
# "python3-sqlite3" is a real, resolvable opkg package name on these
# feeds -- so this is now a hard RDEPENDS. compatibility.py's own
# hasSqlite3() check, and InternetRadioManager's fallback to the
# slower (but self-contained) round-198 JSONL implementation, are kept
# regardless: they also cover a manually-copied install (bypassing
# opkg's own dependency resolution entirely) or any receiver feed that
# doesn't have this package for whatever reason. Round 201 also added
# an in-app "Install SQLite support" menu action (RadioBrowserScreen,
# InternetRadioManager.installSqliteSupport()) as a lower-friction path
# for anyone already running an older build from before this line
# existed, without needing to reinstall the whole plugin.
RDEPENDS_${PN} = "python3-core enigma2 python3-sqlite3"

# MediaPlayer3 uses only Python standard library, no additional Python packages needed
RPROVIDES_${PN} = "mediaplayer3"

# Changelog and documentation
FILES_${PN} += "/usr/lib/enigma2/python/Plugins/Extensions/MediaPlayer3/*"

# Round 188, per direct user report and a direct diff against the
# user's own kept copy of the 1.1.000 public release .ipk
# (mediaplayer3_1.1.000_all.ipk): removing the plugin via opkg had
# stopped deleting its install directory sometime after 1.0.000/
# 1.1.000. opkg only ever removes the individual files it itself
# tracked from a package -- files created at runtime (Python's own
# __pycache__/*.pyc, compiled the first time each module actually
# runs) are invisible to it, so the directory is never empty at
# removal time and gets left behind along with them. This was already
# solved once, in round 23 (see docs/Claude_notes_build0010.txt) --
# extracting the user's 1.1.000 .ipk directly (ar x, tar xzf
# control.tar.gz) confirms it shipped a postrm doing exactly this:
#     #!/bin/sh
#     rm -rf /usr/lib/enigma2/python/Plugins/Extensions/MediaPlayer3
#     exit 0
# But that postrm was only ever added to this project's own manual
# .ipk-packaging process for that one delivered build, never to THIS
# recipe -- so any build produced through the real bitbake/GitHub CI
# pipeline never had it in the first place, and the manual packaging
# process used for every test build since 1.1.000 lost it entirely
# (confirmed: the current session's own ipkbuild/control/ directory
# contains only a "control" file, no "postrm"). Restoring the same
# fix here, as pkg_postrm_${PN}, so a bitbake-built package gets it
# baked in automatically; the manual packaging process used for this
# project's own test builds needs the same file added by hand
# alongside "control" every time until/unless it goes through this
# recipe instead.
pkg_postrm_${PN} () {
    rm -rf /usr/lib/enigma2/python/Plugins/Extensions/MediaPlayer3
}
