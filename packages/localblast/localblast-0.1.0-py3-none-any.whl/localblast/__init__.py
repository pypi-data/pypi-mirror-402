"""LocalBLAST: NCBI BLAST+ wrapper with automatic binary management."""

__version__ = "0.1.0"

# Core functions
# Utility functions
from localblast._binaries import (
    clear_bin_cache,
    get_bin_cache_dir,
    get_exe,
    get_version,
)
from localblast.core import blastn, blastp, blastx, tblastn, tblastx
from localblast.wrappers.makeblastdb import makeblastdb

__all__ = [
    "__version__",
    # Core BLAST functions
    "blastn",
    "blastp",
    "blastx",
    "tblastn",
    "tblastx",
    # Database creation
    "makeblastdb",
    # Utilities
    "get_exe",
    "get_version",
    "get_bin_cache_dir",
    "clear_bin_cache",
]
