# -*- mode: python ; coding: utf-8 -*-
# Ricetta di PyInstaller per SiDD.exe (la usa build.bat).
# Rispetto a quella generata in automatico toglie le parti di Qt che SiDD non usa:
# l'exe viene più piccolo e si compila più in fretta.
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

HERE = SPECPATH  # noqa: F821  (definito da PyInstaller)

# moduli Qt mai importati da SiDD
EXCLUDES = ["PySide6.QtNetwork", "PySide6.QtQml", "PySide6.QtQuick", "PySide6.QtPdf", "PySide6.QtOpenGL",
            "PySide6.QtSvg", "PySide6.QtVirtualKeyboard", "tkinter"]

# file che i plugin di Qt si portano dietro ma che a SiDD non servono
DROP = (
    "opengl32sw.dll",                      # OpenGL software (20 MB): le finestre normali non lo usano
    "qt6quick", "qt6qml", "qt6pdf", "qt6opengl", "qt6network", "qt6virtualkeyboard", "qt6svg",
    "libcrypto-3-x64.dll", "libssl-3-x64.dll",   # SSL di Qt; requests usa quello di Python (libssl-3.dll)
    "plugins\\tls\\", "plugins\\networkinformation\\", "plugins\\platforminputcontexts\\", "plugins\\generic\\",
    "plugins\\iconengines\\", "plugins\\imageformats\\qpdf", "plugins\\imageformats\\qsvg",
    "plugins\\imageformats\\qtiff", "plugins\\imageformats\\qicns",
    "plugins\\platforms\\qdirect2d", "plugins\\platforms\\qoffscreen", "plugins\\platforms\\qminimal",
)


def keep(entry):
    name = entry[0].replace("/", "\\").lower()
    return not any(d in name for d in DROP)


a = Analysis(
    [os.path.join(HERE, "sidd.py")],
    pathex=[HERE],
    datas=collect_data_files("icalendar"),
    hiddenimports=collect_submodules("recurring_ical_events"),
    excludes=EXCLUDES,
    noarchive=False,
    optimize=0,
)
a.binaries = [b for b in a.binaries if keep(b)]
a.datas = [d for d in a.datas if keep(d)]
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="SiDD",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,        # UPX non è installato; meglio dirlo esplicitamente
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    icon=[os.path.join(HERE, "icon.ico")],
)
