from distutils.core import setup
import shutil
shutil.rmtree("build", ignore_errors=True)
shutil.rmtree("dist", ignore_errors=True)
import py2exe
# import sys

# sys.setrecursionlimit(1000000)

includes = []
includes.append('sip')
# includes.append('win32.')
packages = []

setup(console=[{"script": "dld_main.py", "icon_resources": [(1, r"images\download.ico")]}],
    author="zh,zl,gyt,myl",
    version = "v1.2.0",
    description = "productline tool",
    name = "productline tool",
    zipfile = None,
    options = {"py2exe": {    "optimize": 0,
                              "packages": packages,
                              "includes": includes,
                              "dist_dir": 'dist',
                              "bundle_files": 3,
                              "xref": False,
                              "skip_archive": False,
                              "ascii": False,
                              "custom_boot_script": '',
                              "compressed": False,
                              'dll_excludes': ["mswsock.dll","w9xpopen.exe", "powrprof.dll", "CRYPT32.dll"]
                        }, },
    data_files=[
                ('productline_config.ui'),
                ('productline_config_en.ui'),
                ('setportdlg.ui'),
                ('setportdlg_en.ui'),
                ('setupdlg.ui'),
                ('programmer.bin'),
                ('productline_cfg.xml'),
                ('readme.txt'),
                ('transferdll.dll'),
                ("images", [r"images\\about.png"]),
                ("images", [r"images\\download.ico"]),
                ("images", [r"images\\download.png"]),
                ("images", [r"images\\error.png"]),
                ("images", [r"images\\fileset.png"]),
                ("images", [r"images\\help.png"]),
                ("images", [r"images\\quit.png"]),
                ("images", [r"images\\setup.png"]),
                ("images", [r"images\\start.png"]),
                ("images", [r"images\\stop.png"]),
                ]
    )
