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


def extract_fragment(filename: Path, ref: str | None = None, debug=False) -> tuple[etree._Element, int, str]:

    root = etree.parse(filename).getroot()

    # start with the body
    element = root[1]

    # the full text of the body 
    full_content = etree.tostring(element, method="text", encoding="unicode")

    offset = 0

    if ref:
        for idx in [int(i) - 1 for i in ref.split(".")]:
            offset += len(element.text or "")
            for j in range(idx):
                pre_element = element[j]
                pre_content = etree.tostring(pre_element, method="text", encoding="unicode", with_tail=False)
                if debug:
                    print("  ", j + 1, pre_element.tag.split("}")[-1], len(pre_content), len(pre_element.tail or ""))
                offset += len(pre_content) + len(pre_element.tail or "")
            if debug:
                print("@", offset)
            child = element[idx]
            if debug:
                content = etree.tostring(child, method="text", encoding="unicode", with_tail=False)
                print(idx + 1, make_label(child), len(full_content), len(child.tail or ""), repr(content[:5]), repr((child.tail or "")[:5]))
            element = child

    return element, offset, full_content


def extract_fragment2(filename: Path, address: str | None = None) -> NodeDict:
    element, offset, _ = extract_fragment(filename, address)
    element_text = etree.tostring(element, method="text", encoding="unicode", with_tail=False)

    return {
        "label": make_label(element),
        "offset": offset,
        "length": len(element_text),
        "child_count": len(element),
    }


def extract_fragment3(filename: Path, address: str | None = None) -> NodeTuple:
    element, offset, _ = extract_fragment(filename, address)

    return recursive_extract(element, offset)[1]


def recursive_extract(element: etree._Element, offset: int) -> tuple[str, NodeTuple]:
    element_text = etree.tostring(element, method="text", encoding="unicode", with_tail=False)

    children = []

    child_offset = offset + len(element.text or "")
    for child in element:
        # skip comments
        if isinstance(child, etree._Comment):
            continue
        child_text, child_data = recursive_extract(child, child_offset)
        children.append(child_data)
        child_offset += len(child_text) + len(child.tail or "")

    return (
        element_text, (
            make_label(element),
            offset,
            len(element_text),
            children,
        )
    )
