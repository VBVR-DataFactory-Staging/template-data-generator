#!/usr/bin/env python3
"""Install Blender 5.0.0 to the project directory (Linux only)."""

import platform
import subprocess
import sys
import tarfile
import urllib.request
from pathlib import Path

BLENDER_VERSION = "5.0.0"
BLENDER_BASE_URL = "https://download.blender.org/release/Blender5.0/"


def download_progress(block_num: int, block_size: int, total_size: int):
    """Simple download progress callback."""
    downloaded = block_num * block_size
    percent = min(100, downloaded * 100 / total_size) if total_size > 0 else 0
    sys.stdout.write(f"\rProgress: {percent:.1f}%")
    sys.stdout.flush()


def install_blender(project_root: Path) -> Path:
    """Install Blender 5.0.0 under the project root."""
    if platform.system().lower() != "linux":
        raise RuntimeError("This script only supports Linux. Please install Blender manually.")

    machine = platform.machine().lower()
    if "x86_64" not in machine and "amd64" not in machine:
        raise RuntimeError(f"Unsupported architecture: {machine}. Only x86_64 is supported.")

    blender_dir = project_root / "blender"
    blender_dir.mkdir(exist_ok=True)

    blender_exe_name = f"blender-{BLENDER_VERSION}-linux-x64"
    blender_exe = blender_dir / blender_exe_name / "blender"

    if blender_exe.exists():
        print(f"Blender {BLENDER_VERSION} already installed at {blender_exe}")
        return blender_exe

    filename = f"blender-{BLENDER_VERSION}-linux-x64.tar.xz"
    url = f"{BLENDER_BASE_URL}{filename}"
    archive_path = blender_dir / filename

    print(f"Downloading Blender {BLENDER_VERSION} from {url}")
    try:
        urllib.request.urlretrieve(url, archive_path, reporthook=download_progress)
        print("\nDownload complete")
    except Exception as exc:
        print(f"\nDownload failed: {exc}")
        if archive_path.exists():
            archive_path.unlink()
        raise

    print(f"Extracting {filename}...")
    try:
        with tarfile.open(archive_path, "r:xz") as tar:
            tar.extractall(blender_dir)
        print("Extraction complete")
    except Exception as exc:
        print(f"Extraction failed: {exc}")
        if archive_path.exists():
            archive_path.unlink()
        raise

    archive_path.unlink(missing_ok=True)

    if blender_exe.exists():
        try:
            result = subprocess.run(
                [str(blender_exe), "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                print("Blender installation verified")
                print(result.stdout.strip().splitlines()[0])
                return blender_exe
        except subprocess.TimeoutExpired:
            print("Blender test timed out; installation may still be OK")
            return blender_exe
        except Exception as exc:
            print(f"Blender test failed: {exc}")
            return blender_exe

    raise RuntimeError(f"Blender executable not found at {blender_exe}")


if __name__ == "__main__":
    project_root = Path(__file__).parent.parent

    print("=" * 60)
    print(f"Installing Blender {BLENDER_VERSION} (Linux x86_64)")
    print("=" * 60)

    try:
        blender_exe = install_blender(project_root)
        print()
        print("=" * 60)
        print("Installation complete.")
        print(f"Blender executable: {blender_exe}")
        print(f"Usage: {blender_exe} --version")
        print("=" * 60)
    except Exception as exc:
        print()
        print("=" * 60)
        print(f"Installation failed: {exc}")
        print("=" * 60)
        sys.exit(1)
