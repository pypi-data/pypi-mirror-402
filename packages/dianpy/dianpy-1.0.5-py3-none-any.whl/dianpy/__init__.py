from __future__ import annotations
from lxml import etree

from pathlib import Path
from typing import Tuple, Union
from .meet import Meet
from .event import Event
from .athlete import Athlete

__all__: Tuple[str, ...] = ("fromfile", "tofile", "Meet", "Event", "Athlete")

PathLike = Union[str, Path]


def fromfile(path: PathLike) -> Meet:
    """
    Read XML from file and parse it into Meet.
    Important: pass BYTES to from_xml() to support XML declaration with encoding.
    """
    p = Path(path)
    xml_bytes: bytes = p.read_bytes()
    return Meet.from_xml(xml_bytes)


def tofile(
    meet: Meet,
    path: PathLike,
    *,
    encoding: str = "utf-8",
    pretty: bool = True,
    indent: int = 4,
    skip_empty: bool = True,
    exclude_none: bool = True,
    exclude_unset: bool = False,
) -> None:
    """
    Serialize Meet to XML and write it to file.
    NOTE: meet.to_xml() delegates to lxml.etree.tostring(), so do NOT pass pretty_print/indent there.
    """
    p = Path(path)

    # 1) дерево
    root = meet.to_xml_tree(
        skip_empty=skip_empty,
        exclude_none=exclude_none,
        exclude_unset=exclude_unset,
    )

    if pretty:
        try:
            etree.indent(root, space=" " * indent)
        except TypeError:
            etree.indent(root)

    xml_bytes: bytes = etree.tostring(
        root,
        encoding=encoding,
        xml_declaration=True,
        method="xml",
    )

    p.write_bytes(xml_bytes)
