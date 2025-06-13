from pathlib import Path
from typing import TypedDict

from lxml import etree  # type: ignore[import-untyped]


type NodeTuple = tuple[str, int, int, list[NodeTuple]]


class NodeDict(TypedDict):
    label: str
    offset: int
    length: int
    child_count: int


def make_label(el: etree._Element) -> str:

    label = el.tag.split("}")[-1]
    if el.attrib.has_key("class"):
        label += "." + str(el.attrib["class"])
    if el.attrib.has_key("id"):
        label += "#" + str(el.attrib["id"])

    return label


def get_text(element: etree._Element) -> str:
    return etree.tostring(element, method="text", encoding="unicode", with_tail=False)


def element_and_offset(path: Path, address: str | None) -> tuple[etree._Element, int]:
    root = etree.fromstring(path.read_bytes())

    # start with the body
    element = root[1]

    offset = 0

    if address:
        for idx in [int(i) - 1 for i in address.split(".")]:
            offset += len(element.text or "")
            for j in range(idx):
                pre_element = element[j]
                pre_content = get_text(pre_element)
                offset += len(pre_content) + len(pre_element.tail or "")
            child = element[idx]
            element = child

    return element, offset


def extract_node(path: Path, address: str | None, recurse: bool, dictionary: bool) -> NodeTuple | NodeDict:

    element, offset = element_and_offset(path, address)

    if dictionary:
        # note: recurse is ignored for dictionary output
        return extract_dict(element, offset)[1]
    else:
        return extract_tuple(element, offset, recurse)[1]


def extract_tuple(element: etree._Element, offset: int, recurse: bool) -> tuple[str, NodeTuple]:
    element_text = get_text(element)

    children = []

    if recurse:
        child_offset = offset + len(element.text or "")
        for child in element:
            # skip comments
            if isinstance(child, etree._Comment):
                continue
            child_text, child_data = extract_tuple(child, child_offset, recurse)
            children.append(child_data)
            child_offset += len(child_text) + len(child.tail or "")

    node_tuple = (make_label(element), offset, len(element_text), children)

    return (element_text, node_tuple)


def extract_dict(element: etree._Element, offset: int) -> tuple[str, NodeDict]:
    element_text = get_text(element)

    node_dict = NodeDict({
        "label": make_label(element),
        "offset": offset,
        "length": len(element_text),
        "child_count": len(element),
    })

    return (element_text, node_dict)


def extract_text(filename: Path, address: str | None = None) -> str:

    element, _ = element_and_offset(filename, address)

    return get_text(element)
