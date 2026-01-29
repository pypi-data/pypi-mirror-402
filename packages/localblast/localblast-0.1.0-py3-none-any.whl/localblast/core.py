"""Core wrapper functions for BLAST+ operations."""

from __future__ import annotations

import subprocess
from pathlib import Path

from localblast._binaries import get_exe


def blastn(
    query: str | Path,
    db: str | Path,
    *,
    out: str | Path | None = None,
    evalue: float = 10.0,
    max_target_seqs: int = 10,
    num_threads: int = 1,
    **kwargs,
):
    """Run nucleotide BLAST (blastn).

    Args:
        query: Path to query FASTA file.
        db: Path to BLAST database (prefix).
        out: Optional output file path.
        evalue: Expectation value threshold.
        max_target_seqs: Maximum number of aligned sequences to keep.
        num_threads: Number of threads to use.
        **kwargs: Additional BLAST arguments.

    Returns:
        list[BioPython Blast record]: List of BLAST results (one per query sequence).
        Access results via:
        - record.alignments: List of alignments
        - record.descriptions: List of hit descriptions
        - Each alignment.hsps: High-scoring pairs

    Example:
        >>> result = blastn("query.fasta", "nt_db", evalue=0.001)
        >>> for record in result:
        ...     for alignment in record.alignments:
        ...         for hsp in alignment.hsps:
        ...             print(f"{alignment.hit_id}: e-value={hsp.expect}")
    """
    exe = get_exe("blastn")
    cmd = [
        exe,
        "-query",
        str(query),
        "-db",
        str(db),
        "-evalue",
        str(evalue),
        "-max_target_seqs",
        str(max_target_seqs),
        "-num_threads",
        str(num_threads),
    ]

    # Add additional arguments
    for key, value in kwargs.items():
        key = key.replace("_", "-")
        cmd.extend([f"-{key}", str(value)])

    # Output handling
    if out:
        cmd.extend(["-out", str(out)])
        output_format = kwargs.get("outfmt", "5")  # XML by default
    else:
        output_format = kwargs.get("outfmt", "5")  # XML for parsing
        cmd.extend(["-outfmt", output_format])

    # Run BLAST
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=True,
    )

    # Parse output using BioPython
    from io import StringIO

    from Bio.Blast import NCBIXML

    xml_output = result.stdout if not out else Path(out).read_text()
    records = list(NCBIXML.parse(StringIO(xml_output)))
    return records


def blastp(
    query: str | Path,
    db: str | Path,
    *,
    out: str | Path | None = None,
    evalue: float = 10.0,
    max_target_seqs: int = 10,
    num_threads: int = 1,
    **kwargs,
):
    """Run protein BLAST (blastp).

    Args:
        query: Path to query protein FASTA file.
        db: Path to BLAST database (prefix).
        out: Optional output file path.
        evalue: Expectation value threshold.
        max_target_seqs: Maximum number of aligned sequences to keep.
        num_threads: Number of threads to use.
        **kwargs: Additional BLAST arguments.

    Returns:
        list[BioPython Blast record]: List of BLAST results (one per query sequence).
    """
    exe = get_exe("blastp")
    cmd = [
        exe,
        "-query",
        str(query),
        "-db",
        str(db),
        "-evalue",
        str(evalue),
        "-max_target_seqs",
        str(max_target_seqs),
        "-num_threads",
        str(num_threads),
    ]

    for key, value in kwargs.items():
        key = key.replace("_", "-")
        cmd.extend([f"-{key}", str(value)])

    if out:
        cmd.extend(["-out", str(out)])
    else:
        cmd.extend(["-outfmt", kwargs.get("outfmt", "5")])

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    from io import StringIO

    from Bio.Blast import NCBIXML

    xml_output = result.stdout if not out else Path(out).read_text()
    records = list(NCBIXML.parse(StringIO(xml_output)))
    return records


def blastx(
    query: str | Path,
    db: str | Path,
    *,
    out: str | Path | None = None,
    evalue: float = 10.0,
    max_target_seqs: int = 10,
    num_threads: int = 1,
    **kwargs,
):
    """Run translated query BLAST (blastx).

    Args:
        query: Path to query nucleotide FASTA file.
        db: Path to BLAST protein database (prefix).
        out: Optional output file path.
        evalue: Expectation value threshold.
        max_target_seqs: Maximum number of aligned sequences to keep.
        num_threads: Number of threads to use.
        **kwargs: Additional BLAST arguments.

    Returns:
        list[BioPython Blast record]: List of BLAST results (one per query sequence).
    """
    exe = get_exe("blastx")
    cmd = [
        exe,
        "-query",
        str(query),
        "-db",
        str(db),
        "-evalue",
        str(evalue),
        "-max_target_seqs",
        str(max_target_seqs),
        "-num_threads",
        str(num_threads),
    ]

    for key, value in kwargs.items():
        key = key.replace("_", "-")
        cmd.extend([f"-{key}", str(value)])

    if out:
        cmd.extend(["-out", str(out)])
    else:
        cmd.extend(["-outfmt", kwargs.get("outfmt", "5")])

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    from io import StringIO

    from Bio.Blast import NCBIXML

    xml_output = result.stdout if not out else Path(out).read_text()
    records = list(NCBIXML.parse(StringIO(xml_output)))
    return records


def tblastn(
    query: str | Path,
    db: str | Path,
    *,
    out: str | Path | None = None,
    evalue: float = 10.0,
    max_target_seqs: int = 10,
    num_threads: int = 1,
    **kwargs,
):
    """Run translated database BLAST (tblastn).

    Args:
        query: Path to query protein FASTA file.
        db: Path to BLAST nucleotide database (prefix).
        out: Optional output file path.
        evalue: Expectation value threshold.
        max_target_seqs: Maximum number of aligned sequences to keep.
        num_threads: Number of threads to use.
        **kwargs: Additional BLAST arguments.

    Returns:
        list[BioPython Blast record]: List of BLAST results (one per query sequence).
    """
    exe = get_exe("tblastn")
    cmd = [
        exe,
        "-query",
        str(query),
        "-db",
        str(db),
        "-evalue",
        str(evalue),
        "-max_target_seqs",
        str(max_target_seqs),
        "-num_threads",
        str(num_threads),
    ]

    for key, value in kwargs.items():
        key = key.replace("_", "-")
        cmd.extend([f"-{key}", str(value)])

    if out:
        cmd.extend(["-out", str(out)])
    else:
        cmd.extend(["-outfmt", kwargs.get("outfmt", "5")])

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    from io import StringIO

    from Bio.Blast import NCBIXML

    xml_output = result.stdout if not out else Path(out).read_text()
    records = list(NCBIXML.parse(StringIO(xml_output)))
    return records


def tblastx(
    query: str | Path,
    db: str | Path,
    *,
    out: str | Path | None = None,
    evalue: float = 10.0,
    max_target_seqs: int = 10,
    num_threads: int = 1,
    **kwargs,
):
    """Run translated query vs translated database BLAST (tblastx).

    Args:
        query: Path to query nucleotide FASTA file.
        db: Path to BLAST protein database (prefix).
        out: Optional output file path.
        evalue: Expectation value threshold.
        max_target_seqs: Maximum number of aligned sequences to keep.
        num_threads: Number of threads to use.
        **kwargs: Additional BLAST arguments.

    Returns:
        list[BioPython Blast record]: List of BLAST results (one per query sequence).
    """
    exe = get_exe("tblastx")
    cmd = [
        exe,
        "-query",
        str(query),
        "-db",
        str(db),
        "-evalue",
        str(evalue),
        "-max_target_seqs",
        str(max_target_seqs),
        "-num_threads",
        str(num_threads),
    ]

    for key, value in kwargs.items():
        key = key.replace("_", "-")
        cmd.extend([f"-{key}", str(value)])

    if out:
        cmd.extend(["-out", str(out)])
    else:
        cmd.extend(["-outfmt", kwargs.get("outfmt", "5")])

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    from io import StringIO

    from Bio.Blast import NCBIXML

    xml_output = result.stdout if not out else Path(out).read_text()
    records = list(NCBIXML.parse(StringIO(xml_output)))
    return records
