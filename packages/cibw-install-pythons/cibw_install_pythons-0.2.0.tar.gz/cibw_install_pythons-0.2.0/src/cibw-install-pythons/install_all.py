import tempfile
import argparse
import inspect
import os
import shutil
import sys
import json
import subprocess
from pathlib import Path
from platform import machine
from filelock import FileLock
from contextlib import redirect_stdout, ExitStack
from unittest.mock import patch

from cibuildwheel.platforms import macos as platform
from cibuildwheel.util import resources
from cibuildwheel.util.cmd import call
from cibuildwheel.util.file import CIBW_CACHE_PATH, download
from cibuildwheel.ci import detect_ci_provider
from cibuildwheel import errors

def handle_arguments():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    macos_parser = subparsers.add_parser("macos")
    macos_parser.add_argument("--fake-lock", action="store_true")
    macos_parser.add_argument("--ensurepip", action="store_true")
    macos_parser.add_argument("--link", action="store_true")    
    return parser.parse_args()

def macos_install(fake_lock=False, ensurepip=False, link=False):
    configs = platform.all_python_configurations()
    with ExitStack() as stack:
        tmp_root = stack.enter_context(tempfile.TemporaryDirectory())
        if fake_lock:
            stack.enter_context(patch("cibuildwheel.platforms.macos.FileLock"))
        for config in configs:
            arch = "_".join(config.identifier.split("-")[-1].split("_")[1:])
            if arch == machine():
                print("Installing", config.identifier)
                tmp = Path(tmp_root) / config.identifier
                tmp.mkdir(exist_ok=True)
                implementation_id = config.identifier.split("-")[0]
                if implementation_id.startswith("cp"):
                    free_threading = "t-macos" in config.identifier
                    base_python = platform.install_cpython(
                        tmp,
                        config.version,
                        config.url,
                        free_threading
                    )
                elif implementation_id.startswith("pp"):
                    base_python = platform.install_pypy(tmp, config.url)
                elif implementation_id.startswith("gp"):
                    base_python = platform.install_graalpy(tmp, config.url)
                if link:
                    python_bin = base_python.parent / "python"
                    if not python_bin.exists():
                        python_bin.symlink_to(base_python.name)
                config = vars(config)
                config["python"] = str(base_python)                 
                if ensurepip:
                    subprocess.run(
                        [config["python"], "-m", "ensurepip"],
                        check=True,
                    )
                yield config

def main():
    args = handle_arguments()
    if args.command == "macos":
        with open(os.devnull, "w") as devnull:
            with redirect_stdout(devnull):
                pythons = list(
                    macos_install(
                        args.fake_lock,
                        args.ensurepip,
                        args.link,
                    )
                )
        for python in pythons:
            print(json.dumps(python))
 

if __name__ == "__main__":
    main()
