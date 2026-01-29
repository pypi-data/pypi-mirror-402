"""BLAST output parsers using BioPython."""

from io import StringIO

from Bio.Blast import NCBIXML

__all__ = ["parse_xml", "parse_xml_file"]


# Re-export BioPython's parser
def parse_xml(xml_text: str):
    """Parse BLAST XML output using BioPython.

    Args:
        xml_text: BLAST XML output string (outfmt=5).

    Returns:
        BioPython Blast record object with alignments and hsps.

    Example:
        >>> from localblast.parsers import parse_xml
        >>> record = parse_xml(xml_string)
        >>> for alignment in record.alignments:
        ...     for hsp in alignment.hsps:
        ...         print(f"E-value: {hsp.expect}")
    """
    return NCBIXML.read(StringIO(xml_text))


def parse_xml_file(file_path: str):
    """Parse BLAST XML file using BioPython.

    Args:
        file_path: Path to BLAST XML output file.

    Returns:
        BioPython Blast record object.

    Example:
        >>> from localblast.parsers import parse_xml_file
        >>> record = parse_xml_file("blast_output.xml")
        >>> for alignment in record.alignments:
        ...     print(f"Hit: {alignment.hit_id}, length: {alignment.length}")
    """
    with open(file_path) as handle:
        return NCBIXML.read(handle)
