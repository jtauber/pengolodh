from pathlib import Path
from typing import TypedDict

from lxml import etree  # type: ignore[import-untyped]


# (address, label, offset, total_length, text_length, children, tail_length)
type NodeTuple = tuple[str, str, int, int, int, list[NodeTuple], int]


class NodeDict(TypedDict):
    label: str
    offset: int
    total_length: int
    text_length: int
    child_count: int
    tail_length: int


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
        return extract_tuple(element, offset, recurse, address)[1]


def extract_tuple(element: etree._Element, offset: int, recurse: bool, address: str | None) -> tuple[str, NodeTuple]:
    element_text = get_text(element)

    children = []

    if recurse:
        child_offset = offset + len(element.text or "")
        for child in element:
            # skip comments
            if isinstance(child, etree._Comment):
                continue
            child_text, child_data = extract_tuple(child, child_offset, recurse, (address + "." if address else "") + str(len(children) + 1))
            children.append(child_data)
            child_offset += len(child_text) + len(child.tail or "")

    node_tuple = (
        address or "",
        make_label(element),
        offset,
        len(element_text),
        0 if element.text is None else len(element.text),
        children,
        0 if element.tail is None else len(element.tail)
    )

    return (element_text, node_tuple)


def extract_dict(element: etree._Element, offset: int) -> tuple[str, NodeDict]:
    element_text = get_text(element)

    node_dict = NodeDict({
        "label": make_label(element),
        "offset": offset,
        "total_length": len(element_text),
        "text_length": 0 if element.text is None else len(element.text),
        "child_count": len(element),
        "tail_length": 0 if element.tail is None else len(element.tail),
    })

    return (element_text, node_dict)


def extract_text(filename: Path, address: str | None = None) -> str:

    element, _ = element_and_offset(filename, address)

    return get_text(element)


def extract_xml(filename: Path, address: str | None = None) -> str:

    element, _ = element_and_offset(filename, address)

    return etree.tostring(element, method="xml", encoding="unicode", with_tail=False)
