"""Wrapper for makeblastdb."""

from __future__ import annotations

import subprocess
import warnings
from pathlib import Path

from localblast._binaries import get_exe


def makeblastdb(
    input: str | Path,
    *,
    dbtype: str = "nucl",
    out: str | Path | None = None,
    title: str | None = None,
    parse_seqids: bool = True,
    **kwargs,
) -> str:
    """Create a BLAST database from input sequences.

    Args:
        input: Path to input FASTA file.
        dbtype: Database type ("nucl" or "prot").
        out: Output database name/prefix.
        title: Database title.
        parse_seqids: Parse sequence IDs.
        **kwargs: Additional makeblastdb arguments.

    Returns:
        Path to created database prefix.

    Raises:
        RuntimeError: If database creation fails.

    Example:
        >>> db_path = makeblastdb("sequences.fasta", dbtype="nucl", title="My DB")

    Note:
        On Windows, BLAST+ may return non-zero exit codes when paths contain spaces,
        but still create the database successfully. This function verifies database
        files were created rather than relying on exit codes.
    """
    exe = get_exe("makeblastdb")
    cmd = [
        exe,
        "-in",
        str(input),
        "-dbtype",
        dbtype,
    ]

    if out:
        cmd.extend(["-out", str(out)])

    if title:
        cmd.extend(["-title", title])

    if parse_seqids:
        cmd.append("-parse_seqids")

    for key, value in kwargs.items():
        key = key.replace("_", "-")
        cmd.extend([f"-{key}", str(value)])

    # Run command and capture output
    result = subprocess.run(cmd, capture_output=True)

    # Check for success by verifying database files exist
    # Exit code can be misleading on Windows with paths containing spaces
    db_prefix = str(out or Path(input).stem)
    expected_files = (
        [".nsq", ".nhr", ".nin"] if dbtype == "nucl" else [".psq", ".phr", ".pin"]
    )

    # Check if any expected database file was created
    db_created = any(Path(f"{db_prefix}{ext}").exists() for ext in expected_files)

    if not db_created:
        error_msg = result.stderr.decode()
        raise RuntimeError(f"makeblastdb failed: {error_msg}")

    # Warn if there were errors but database was created
    if result.returncode != 0 and db_created:
        warnings.warn(
            "makeblastdb returned non-zero exit code but database was created. "
            "This can happen with paths containing spaces on Windows.",
            stacklevel=2,
        )

    return str(out or Path(input).stem)
