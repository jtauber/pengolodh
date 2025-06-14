from json import dumps
from pathlib import Path
import sys
from typing import Optional
import zipfile

from rich import print as rich_print  # type: ignore[import-not-found]
from rich.console import Console  # type: ignore[import-not-found]
from rich.table import Table  # type: ignore[import-not-found]
from rich.tree import Tree  # type: ignore[import-not-found]

import typer  # type: ignore

from .config import books_configuration
from .epub import process_volume, process_container, process_opf
from .extract import extract_node, extract_text, extract_xml


app = typer.Typer()


def print_info(message: str) -> None:
    rich_print(f"[blue]{message}[/blue]", file=sys.stderr)


def print_error(message: str) -> None:
    rich_print(f"[red]{message}[/red]", file=sys.stderr)


def get_path(book_id_or_path: str) -> Path | zipfile.Path:

    books = books_configuration()

    if book_id_or_path in books:
        path_string = books[book_id_or_path]
        print_info(f"using {path_string}")
    else:
        path_string = book_id_or_path

    path = Path(path_string)
    book_path: Path | zipfile.Path
    if not path.is_dir():
        if not zipfile.is_zipfile(path):
            raise ValueError(f"Path {path} is not a directory or a valid EPUB file.")
        book_path = zipfile.Path(zipfile.ZipFile(path))
    else:
        book_path = path
    
    return book_path


@app.command()
def list_books() -> None:
    books = books_configuration()
    if not books:
        print_error("No books found.")
    else:
        table = Table(title="Books")
        table.add_column("Book ID", style="cyan")
        table.add_column("Path", style="magenta")

        for book_id, path in books.items():
            table.add_row(book_id, str(Path(path).resolve()))

        console = Console()
        console.print(table)


@app.command()
def title(book_id_or_path: str):
    path = get_path(book_id_or_path)
    volume_data = process_volume(path)
    print("Metadata:", volume_data["metadata"]["title"])
    print("NCX:", volume_data["ncx"]["title"])


@app.command()
def container(book_id_or_path: str):
    epub_root = get_path(book_id_or_path)
    opf_path = epub_root / process_container(epub_root / "META-INF/container.xml") 
    print(opf_path)


@app.command()
def opf(book_id_or_path: str):
    epub_root = get_path(book_id_or_path)
    opf_path = process_container(epub_root / "META-INF/container.xml")
    opf_data = process_opf(epub_root, opf_path)
    rich_print("OPF Version:      ", opf_data["version"])
    rich_print("Unique Identifier:", opf_data["unique_identifier"])
    rich_print("Prefix:           ", opf_data["prefix"])
    rich_print("XML Language:     ", opf_data["xml_lang"])
    print()
    print(opf_data["metadata"])
    print()

    table = Table(title="Manifest")
    table.add_column("id", style="cyan")
    table.add_column("href", style="magenta")
    table.add_column("media-type", style="green")
    table.add_column("properties", style="yellow")

    for item_id, item_data in opf_data["manifest"].items():
        table.add_row(item_id, item_data["href"], item_data.get("media-type", ""), item_data.get("properties", ""))

    console = Console()
    console.print(table)


@app.command()
def spine(book_id_or_path: str):
    path = get_path(book_id_or_path)
    volume_data = process_volume(path)
    manifest = volume_data["manifest"]

    console = Console()

    table = Table(title="Spine")
    table.add_column("Item Ref", style="cyan")
    table.add_column("Path", style="magenta")

    for itemref in volume_data["spine"]["itemrefs"]:
        table.add_row(itemref, str(manifest[itemref]["href"]))

    console.print(table)
    console.print(
        f"[bold]TOC ID[/bold]:",
        f"[cyan]{volume_data['spine']['toc_id']}[/cyan]", 
        f"[magenta]{manifest[volume_data['spine']['toc_id']]['href']}[/magenta]",)


def build_nav_tree(node, nav_point) -> None:
    styled_label = ""
    if nav_point.get("playOrder"):
        styled_label += f"[dim][{nav_point['playOrder']}][/dim] "
    styled_label += f"[cyan]{nav_point['id']}[/cyan] "
    styled_label += f"[bold]{nav_point['label']}[/bold] "
    styled_label += f"[magenta]{nav_point['src']}[/magenta] "

    child_node = node.add(styled_label)

    for child in nav_point["children"]:
        build_nav_tree(child_node, child)


@app.command()
def ncx(book_id_or_path: str):
    path = get_path(book_id_or_path)
    volume_data = process_volume(path)
    print(volume_data["ncx"]["title"])
    print(volume_data["ncx"]["head"])

    tree = Tree("[bold]NCX[/bold]")
    for nav_point in volume_data["ncx"]["navMap"]:
        build_nav_tree(tree, nav_point)

    console = Console()
    console.print(tree)


@app.command()
def extract_map(book_id_or_path: str, itemref: Optional[str] = None, address: Optional[str] = None, recurse: bool = False) -> None:
    path = get_path(book_id_or_path)
    volume_data = process_volume(path)
    manifest = volume_data["manifest"]

    if itemref is None:
        items = []
        for item_ref in volume_data["spine"]["itemrefs"]:
            file_path = manifest[item_ref]["path"]
            items.append([item_ref, extract_node(file_path, address=None, recurse=recurse, dictionary=not recurse)])
        print(dumps(items, indent=2))
    else:
        file_path = manifest[itemref]["path"]
        print(extract_node(file_path, address, recurse=recurse, dictionary=not recurse))


def build_tree(node, data, depth: Optional[int] = None):
    address, label, offset, total_length, text, children, tail = data

    if "#" in label:
        a, d = label.split("#")
    else:
        a, d = label, ""
    if "." in a:
        b, c = a.split(".")
    else:
        b, c = a, ""
    styled_label = f"[bold]{address}[/bold] " if address else ""
    styled_label += f"[green]{b}[/green]"
    if c:
        styled_label += f".[cyan]{c}[/cyan]"
    if d:
        styled_label += f"[dim]#{d}[/dim]"

    styled_label += f" [magenta][{offset}:{offset+total_length}][/magenta]"

    child_node = node.add(styled_label, style="not bold")

    if text:
        child_node.add(f"[yellow]{repr(text)}[/yellow]")

    if depth is None or depth > 0:
        for child in children:
            build_tree(child_node, child, None if depth is None else depth - 1)

    if tail:
        node.add(f"[yellow]{repr(tail)}[/yellow]")


@app.command()
def tree(book_id_or_path: str, itemref: str, address: Optional[str] = None, depth: Optional[int] = None) -> None:
    path = get_path(book_id_or_path)
    volume_data = process_volume(path)
    manifest = volume_data["manifest"]

    file_path = manifest[itemref]["path"]
    tree = Tree(itemref, style="bold")
    node = extract_node(file_path, address, recurse=True, dictionary=False)
    build_tree(tree, node, depth)

    console = Console()
    console.print(tree)


@app.command()
def text(book_id_or_path: str, itemref: str, address: Optional[str] = None) -> None:
    path = get_path(book_id_or_path)
    volume_data = process_volume(path)
    manifest = volume_data["manifest"]
    file_path = manifest[itemref]["path"]

    print(extract_text(file_path, address))


@app.command()
def xml(book_id_or_path: str, itemref: str, address: Optional[str] = None) -> None:
    path = get_path(book_id_or_path)
    volume_data = process_volume(path)
    manifest = volume_data["manifest"]
    file_path = manifest[itemref]["path"]

    console = Console()
    console.print(extract_xml(file_path, address))
