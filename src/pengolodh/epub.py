import zipfile
from pathlib import Path

from lxml import etree  # type: ignore[import-untyped]


def opendoc_container(element_name: str) -> str:
    return "{urn:oasis:names:tc:opendocument:xmlns:container}" + element_name


def opf(element_name: str) -> str:
    return "{http://www.idpf.org/2007/opf}" + element_name


def dc(element_name: str) -> str:
    return "{http://purl.org/dc/elements/1.1/}" + element_name


def ncx(element_name: str) -> str:
    return "{http://www.daisy.org/z3986/2005/ncx/}" + element_name


def xml(element_name: str) -> str:
    return "{http://www.w3.org/XML/1998/namespace}" + element_name


def process_volume(path: Path | zipfile.Path) -> dict:

    for child in path.iterdir():
        if child.name == "META-INF":
            assert child.is_dir()
            rootfile = process_container(child / "container.xml")
        elif child.name == "mimetype":
            assert child.is_file()
            assert child.read_text() == "application/epub+zip"
        elif child.name == "OEBPS":
            assert child.is_dir()
        else:
            pass  # skip unknown top-level files and directories

    return process_opf(path, rootfile)


def process_container(path: Path | zipfile.Path) -> str:
    assert path.is_file()
    container = etree.fromstring(path.read_bytes())
    assert container.tag == opendoc_container("container")
    assert container.attrib == {"version": "1.0"}
    assert len(container) == 1
    rootfiles = container[0]
    assert rootfiles.tag == opendoc_container("rootfiles")
    assert rootfiles.attrib == {}
    assert len(rootfiles) == 1
    rootfile = rootfiles[0]
    assert rootfile.tag == opendoc_container("rootfile")
    assert set(rootfile.keys()) == {"full-path", "media-type"}
    assert rootfile.attrib["full-path"]
    assert rootfile.attrib["media-type"] == "application/oebps-package+xml"
    assert len(rootfile) == 0

    return str(rootfile.attrib["full-path"])


def process_opf(epub_root: Path | zipfile.Path, rootfile: str) -> dict:
    path = epub_root / rootfile
    assert path.is_file()
    package = etree.fromstring(path.read_bytes())
    assert package.tag == opf("package")
    assert set(package.keys()) in [
        {"version", "unique-identifier"},
        {"version", "unique-identifier", "prefix"},
        {"version", "unique-identifier", xml("lang")},
        {"version", "unique-identifier", "prefix", xml("lang")},
    ], package.attrib
    version = package.attrib["version"]
    assert version in ["2.0", "3.0"]
    unique_identifier = package.attrib["unique-identifier"]
    # assert unique_identifier in ["PrimaryID", "bookid", "uuid_id"], unique_identifier
    assert len(package) == 4

    for child in package:
        if child.tag == opf("metadata"):
            metadata = process_metadata(child)
        elif child.tag == opf("manifest"):
            # @@@ not sure how to make this type check
            manifest = process_manifest(path.parent, child)  # type: ignore
        elif child.tag == opf("spine"):
            spine = process_spine(child)
        elif child.tag == opf("guide"):
            process_guide(child)
        else:
            raise ValueError(child.tag)

    ncx_path = path.parent / manifest[spine["toc_id"]]["href"]

    return {
        "version": version,
        "unique_identifier": unique_identifier,
        "prefix": package.attrib.get("prefix", ""),
        "xml_lang": package.attrib.get(xml("lang"), ""),
        "metadata": metadata,
        "manifest": manifest,
        "spine": spine,
        "ncx_path": ncx_path,
        "ncx": process_ncx(ncx_path),
    }


def process_metadata(metadata_element: etree._Element) -> dict:

    assert metadata_element.tag == opf("metadata")
    assert metadata_element.attrib == {}

    metadata = {}

    for child in metadata_element:
        if child.tag == dc("title"):
            assert set(child.keys()) in [
                set(),
                {"id", xml("lang")},
            ], child.attrib
            assert len(child) == 0
            metadata["title"] = child.text
        elif child.tag == dc("creator"):
            assert set(child.keys()) in [
                {"id"},
                {opf("role"), opf("file-as")},
                set(),
            ], child.attrib
            assert len(child) == 0
            # print(child.text)  # @@@
        elif child.tag == dc("contributor"):
            assert set(child.keys()) in [
                {opf("role")},
                set(),
            ], child.attrib
            assert len(child) == 0
            # print(child.text)  # @@@
        elif child.tag == dc("publisher"):
            assert child.attrib == {}
            assert len(child) == 0
            # print(child.text)  # @@@
        elif child.tag == dc("rights"):
            assert child.attrib == {}
            assert len(child) == 0
            # print(child.text)  # @@@
        elif child.tag == dc("format"):
            assert child.attrib == {}
            assert len(child) == 0
            # print(child.text)  # @@@
        elif child.tag == dc("date"):
            assert set(child.keys()) in [set(), {opf("event")}]
            assert len(child) == 0
            # print(child.attrib.get(opf("event"), ""), child.text)  # @@@
        elif child.tag == dc("subject"):
            assert child.attrib == {}
            assert len(child) == 0
            # print(child.text)  # @@@
        elif child.tag == dc("description"):
            assert child.attrib == {}
            assert len(child) == 0
            # print(child.text)  # @@@
        elif child.tag == dc("language"):
            assert child.attrib == {}
            assert len(child) == 0
            assert child.text in ["en", "en-US"]
        elif child.tag == dc("identifier"):
            assert set(child.keys()) in [
                {"id"},
                {opf("scheme")},
                {"id", opf("scheme")},
            ], child.attrib
            # print(child.text)
        elif child.tag == dc("type"):
            assert child.attrib == {}
            assert len(child) == 0
            # print(child.text)  # @@@
        elif child.tag == dc("source"):
            assert set(child.keys()) in [
                set(),
                {"id"},
            ], child.attrib
            assert len(child) == 0
            # print(child.text)  # @@@
        elif child.tag == opf("meta"):
            if "property" in child.attrib:
                assert child.attrib["property"] in [
                    "dcterms:modified",
                    "role",
                    "title-type",
                    "file-as",
                    "source-of",
                    "schema:accessMode",
                    "schema:accessModeSufficient",
                    "schema:accessibilityFeature",
                    "schema:accessibilityHazard",
                    "schema:accessibilitySummary",
                    "a11y:certifiedBy",
                ], child.attrib["property"]
                assert len(child) == 0
                #  print(child.text)  # @@@
            else:
                assert set(child.keys()) == {"name", "content"}
                assert len(child) == 0
                assert child.text is None
        elif child.tag == opf("link"):
            pass  # @@@
        else:
            raise ValueError(child.tag)

    return metadata


def process_manifest(parent_path: Path | zipfile.Path, manifest_element: etree._Element) -> dict:

    assert manifest_element.tag == opf("manifest")
    assert manifest_element.attrib == {}

    manifest = {}

    for child in manifest_element:
        assert child.tag == opf("item")
        assert set(child.keys()) in [
            {"id", "href", "media-type"},
            {"id", "href", "media-type", "properties"},
        ], child.keys()
        if "properties" in child.attrib:
            assert child.attrib["properties"] in [
                "nav", "cover-image", "svg"
            ], child.attrib["properties"]
        assert child.attrib["media-type"] in [
            "application/vnd.adobe-page-template+xml",  # @@@
            "application/xhtml+xml",
            "image/jpeg",
            "image/gif",
            "application/x-dtbncx+xml",
            "application/javascript",
            "text/css",
            "application/x-font-ttf",  # @@@
            "application/x-font-truetype",  # @@@
            "application/vnd.ms-opentype",  # @@@
            "font/otf",  # @@@
        ], child.attrib["media-type"]
        assert len(child) == 0
        assert child.text is None
        manifest[child.attrib["id"]] = {
            "href": child.attrib["href"],
            "path": parent_path / str(child.attrib["href"]),
            "media-type": child.attrib["media-type"],
            "properties": child.attrib.get("properties"),
        }

    return manifest


def process_spine(spine: etree._Element) -> dict:

    assert spine.tag == opf("spine")
    assert set(spine.keys()) == {"toc"}

    toc_id = spine.attrib["toc"]

    itemrefs = []
    for child in spine:
        assert child.tag == opf("itemref")
        # could also have 'linear' attribute
        # assert set(child.keys()) == {"idref"}
        assert child.attrib["idref"]
        assert len(child) == 0
        assert child.text is None
        itemrefs.append(child.attrib["idref"])

    return {
        "toc_id": toc_id,
        "itemrefs": itemrefs,
    }


def process_guide(guide: etree._Element) -> None:

    assert guide.tag == opf("guide")
    assert guide.attrib == {}

    for child in guide:
        assert child.tag == opf("reference")
        assert set(child.keys()) == {"type", "title", "href"}
        assert child.attrib["type"] in ["cover", "toc", "text", "start", "copyright-page", "title-page"]
        assert child.attrib["title"]
        assert child.attrib["href"]
        assert len(child) == 0
        assert child.text is None


def process_ncx(path: Path) -> dict:

    assert path.is_file()

    ncx_root = etree.fromstring(path.read_bytes())

    assert ncx_root.tag == ncx("ncx")
    # could also have an xml:lang
    # assert set(ncx_root.keys()) == {"version"}
    assert ncx_root.attrib["version"] == "2005-1"

    navMap = []
    head = {}

    for child in ncx_root:
        if child.tag == ncx("head"):
            assert child.attrib == {}
            for head_child in child:
                assert head_child.tag == ncx("meta")
                assert set(head_child.keys()) == {"name", "content"}, head_child.attrib
                assert len(head_child) == 0
                assert head_child.attrib["name"] in [
                    "dtb:uid",
                    "dtb:depth",
                    "dtb:totalPageCount",
                    "dtb:maxPageNumber",
                    "dtb:generator",
                ], head_child.attrib["name"]
                if head_child.attrib["name"] == "dtb:uid":
                    uid = head_child.attrib["content"]
                head[head_child.attrib["name"]] = head_child.attrib["content"]
        elif child.tag == ncx("docTitle"):
            assert child.attrib == {}
            assert len(child) == 1
            text_element = child[0]
            assert text_element.tag == ncx("text")
            assert text_element.attrib == {}
            assert len(text_element) == 0
            docTitle = text_element.text
        elif child.tag == ncx("docAuthor"):
            assert child.attrib == {}
            assert len(child) == 1
            text_element = child[0]
            assert text_element.tag == ncx("text")
            assert text_element.attrib == {}
            assert len(text_element) == 0
            # author = text_element.text
        elif child.tag == ncx("navMap"):
            assert child.attrib == {}
            assert len(child) > 0
            for navPoint in child:
                navMap.append(process_nav_point(path.parent, navPoint))
        elif child.tag == ncx("pageList"):
            pass  # @@@
        else:
            raise ValueError(child.tag)

    return {
        "uid": uid,
        "head": head,
        "title": docTitle,
        "path": path.parent,
        "navMap": navMap,
    }


def process_nav_point(root_path: Path, navPoint: etree._Element, level: int = 0):

    assert navPoint.tag == ncx("navPoint")
    # could also have a 'class' or 'nav0' attribute
    # assert set(navPoint.keys()) == {"id", "playOrder"}, navPoint.attrib
    assert len(navPoint) > 0

    playOrder = navPoint.attrib.get("playOrder")
    klass = navPoint.attrib.get("class")
    nav0 = navPoint.attrib.get("nav0")
    pointId = navPoint.attrib.get("id")

    children = []

    for navPoint_child in navPoint:
        if navPoint_child.tag == ncx("navLabel"):
            assert navPoint_child.attrib == {}
            assert len(navPoint_child) == 1
            navLabel_child = navPoint_child[0]
            assert navLabel_child.tag == ncx("text")
            assert navLabel_child.attrib == {}
            assert len(navLabel_child) == 0
            label = navLabel_child.text
        elif navPoint_child.tag == ncx("content"):
            assert set(navPoint_child.attrib) == {"src"}
            assert len(navPoint_child) == 0
            assert navPoint_child.text is None
            src = navPoint_child.attrib["src"]
        elif navPoint_child.tag == ncx("navPoint"):
            children.append(process_nav_point(root_path, navPoint_child, level + 1))
        else:
            raise ValueError(navPoint_child.tag)

    return {
        "id": pointId,
        "playOrder": playOrder,
        "class": klass,
        "nav0": nav0,
        "level": level,
        "label": label,
        "src": src,
        "volume_name": root_path.parent.name,
        "path": root_path / str(src),
        "children": children,
    }
