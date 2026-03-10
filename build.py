"""Build a standalone .exe with PyInstaller.

Usage:
    uv run python build.py
"""

import os
import re
import sysconfig
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _find_mypyc_binaries():
    """Find top-level mypyc .pyd/.so files in site-packages and return as
    (source_path, module_name) pairs for --add-binary."""
    results = []
    sp_dir = sysconfig.get_path("platlib")
    if not sp_dir or not os.path.isdir(sp_dir):
        return results
    for fname in os.listdir(sp_dir):
        if "__mypyc" in fname and (fname.endswith(".pyd") or ".so" in fname):
            full_path = os.path.join(sp_dir, fname)
            module_name = re.split(r"\.cp\d|\.cpython|\.so|\.pyd", fname)[0]
            results.append((full_path, module_name))
    return results


def main():
    spec_file = os.path.join(SCRIPT_DIR, "RunPodPodManager.spec")
    if os.path.exists(spec_file):
        os.remove(spec_file)
        print("[build] Removed stale .spec file")

    args = [
        sys.executable,
        "-m",
        "PyInstaller",
        "main.py",
        "--onefile",
        "--windowed",
        "--name",
        "RunPodPodManager",
        "--noconfirm",
    ]

    mypyc_bins = _find_mypyc_binaries()

    for src_path, mod_name in mypyc_bins:
        args.extend(["--add-binary", f"{src_path}{os.pathsep}."])
        args.extend(["--hidden-import", mod_name])

    print(f"[build] Adding {len(mypyc_bins)} mypyc binaries:")
    for src_path, mod_name in mypyc_bins:
        print(f"  {mod_name} -> {src_path}")

    return subprocess.call(args)


if __name__ == "__main__":
    raise SystemExit(main())
