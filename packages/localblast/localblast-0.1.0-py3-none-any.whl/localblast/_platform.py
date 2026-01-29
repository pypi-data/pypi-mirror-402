"""Platform detection for NCBI BLAST+ binaries."""

import platform as _platform
import sys


def get_platform() -> str:
    """Get platform identifier for BLAST+ binary selection.

    Returns:
        Platform string in format: "{os}-{arch}"
        Examples: "windows-x86_64", "linux-x86_64", "macos-aarch64"
    """
    return _get_os_string() + "-" + _get_arch()


def _get_os_string() -> str:
    """Detect operating system."""
    if sys.platform.startswith("win"):
        return "windows"
    elif sys.platform.startswith("darwin"):
        return "macos"
    elif sys.platform.startswith("linux"):
        return "linux"
    else:
        return sys.platform


def _get_arch() -> str:
    """Detect system architecture."""
    is_64_bit = sys.maxsize > 2**32
    machine = _platform.machine()

    if is_64_bit and machine.startswith(("arm", "aarch64")):
        return "aarch64"
    elif is_64_bit:
        return "x86_64"
    else:
        return "i686"


# BLAST+ 2.17.0+ binary archive names
BLAST_ARCHIVE_PER_PLATFORM = {
    "windows-x86_64": "ncbi-blast-2.17.0+-x64-win64.tar.gz",
    "linux-x86_64": "ncbi-blast-2.17.0+-x64-linux.tar.gz",
    "macos-x86_64": "ncbi-blast-2.17.0+-x64-macosx.tar.gz",
    "macos-aarch64": "ncbi-blast-2.17.0+-aarch64-macosx.tar.gz",
    "linux-aarch64": "ncbi-blast-2.17.0+-aarch64-linux.tar.gz",
}

# Core BLAST+ executables to distribute
CORE_EXECUTABLES = [
    "blastn",
    "blastp",
    "blastx",
    "tblastn",
    "tblastx",
    "makeblastdb",
]
