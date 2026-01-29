"""Binary download, caching, and path resolution."""

import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from urllib.request import urlretrieve

from localblast._platform import (
    BLAST_ARCHIVE_PER_PLATFORM,
    CORE_EXECUTABLES,
    get_platform,
)

# Constants
NCBI_FTP_BASE = "https://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/LATEST/"
BIN_CACHE_DIR = Path.cwd() / ".localblast"
BIN_CACHE_VERSION = "1"  # Increment to force re-download


def get_bin_cache_dir() -> Path:
    """Get the binary cache directory for BLAST+ executables.

    Returns:
        Path to binary cache directory.
    """
    # Check for environment variable override
    override = os.getenv("LOCALBLAST_CACHE_DIR")
    if override:
        return Path(override)
    return BIN_CACHE_DIR


def get_bin_dir() -> Path:
    """Get the directory containing BLAST+ binaries.

    Downloads binaries if not already cached.

    Returns:
        Path to binaries directory.
    """
    bin_dir = get_bin_cache_dir() / "bin"
    version_file = bin_dir / ".version"

    # Check if we need to download
    if bin_dir.exists() and version_file.exists():
        current_version = version_file.read_text().strip()
        if current_version == BIN_CACHE_VERSION:
            # Verify at least one executable exists
            exe = "blastn.exe" if sys.platform.startswith("win") else "blastn"
            if (bin_dir / exe).exists():
                return bin_dir

    # Download binaries
    _download_binaries(bin_dir)
    version_file.write_text(BIN_CACHE_VERSION)

    return bin_dir


def _download_binaries(bin_dir: Path) -> None:
    """Download and extract BLAST+ binaries for current platform.

    Args:
        bin_dir: Directory to extract binaries to.
    """
    platform = get_platform()
    archive_name = BLAST_ARCHIVE_PER_PLATFORM.get(platform)

    if not archive_name:
        raise ValueError(
            f"No BLAST+ archive available for platform: {platform}. "
            f"Supported platforms: {list(BLAST_ARCHIVE_PER_PLATFORM.keys())}"
        )

    # Create cache directory
    bin_dir.mkdir(parents=True, exist_ok=True)

    # Download archive
    url = NCBI_FTP_BASE + archive_name
    print(f"Downloading {archive_name} from NCBI FTP...")

    with tempfile.TemporaryDirectory() as tmpdir:
        archive_path = Path(tmpdir) / archive_name
        urlretrieve(url, archive_path)

        # Extract archive
        print(f"Extracting {archive_name}...")
        with tarfile.open(archive_path, "r:gz") as tar:
            tar.extractall(tmpdir)

        # Find the extracted bin directory
        extracted_dirs = list(Path(tmpdir).glob("ncbi-blast-*/bin"))
        if not extracted_dirs:
            raise RuntimeError("Could not find bin directory in extracted archive")

        extracted_bin = extracted_dirs[0]

        # Copy entire bin directory (all executables and dependencies)
        for item in extracted_bin.iterdir():
            if item.is_file():
                dest = bin_dir / item.name
                shutil.copy2(item, dest)
                # Make executable on Unix
                if not sys.platform.startswith("win"):
                    os.chmod(dest, 0o755)

    print(f"BLAST+ binaries cached to: {bin_dir}")


def get_exe(name: str) -> str:
    """Get path to a BLAST+ executable, downloading if needed.

    Args:
        name: Executable name (e.g., "blastn", "makeblastdb")

    Returns:
        Full path to the executable.

    Raises:
        ValueError: If executable name is unknown.
        RuntimeError: If executable cannot be found.
    """
    if name not in CORE_EXECUTABLES:
        raise ValueError(f"Unknown executable: {name}. Available: {CORE_EXECUTABLES}")

    # 1. Check environment variable (override)
    env_path = os.getenv(f"LOCALBLAST_{name.upper()}")
    if env_path and os.path.isfile(env_path):
        return env_path

    # 2. Check cached binary (will download if needed)
    bin_dir = get_bin_dir()
    exe_name = f"{name}.exe" if sys.platform.startswith("win") else name
    exe_path = bin_dir / exe_name

    if exe_path.exists() and _is_valid_exe(str(exe_path)):
        return str(exe_path)

    # 3. Check system PATH
    system_exe = shutil.which(name)
    if system_exe and _is_valid_exe(system_exe):
        return system_exe

    raise RuntimeError(
        f"Cannot find {name} executable. "
        f"Set LOCALBLAST_{name.upper()} environment variable or ensure BLAST+ is installed."
    )


def _is_valid_exe(exe: str) -> bool:
    """Verify executable is valid by running it with version flag.

    Args:
        exe: Path to executable.

    Returns:
        True if executable runs successfully, False otherwise.
    """
    try:
        with open(os.devnull, "w") as null:
            subprocess.check_call(
                [exe, "-version"],
                stdout=null,
                stderr=subprocess.STDOUT,
                timeout=5,
            )
        return True
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False


def get_version() -> str:
    """Get BLAST+ version from cached/system binary.

    Returns:
        Version string.

    Raises:
        RuntimeError: If version cannot be determined.
    """
    exe = get_exe("blastn")
    try:
        result = subprocess.run(
            [exe, "-version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        # Parse version from output: "blastn: 2.17.0+ ..."
        # Output may be in stdout or stderr depending on platform
        output = result.stdout or result.stderr
        for line in output.splitlines():
            if "blastn:" in line:
                return line.split(":")[1].strip().split()[0]
        raise RuntimeError("Version not found in output")
    except Exception as e:
        raise RuntimeError(f"Failed to get BLAST+ version: {e}") from e


def clear_bin_cache() -> None:
    """Clear the cached BLAST+ binaries.

    This will force re-download on next use.
    """
    bin_dir = get_bin_cache_dir() / "bin"
    if bin_dir.exists():
        shutil.rmtree(bin_dir)
        print(f"Cleared cache: {bin_dir}")
    else:
        print("No cache to clear")
