from json import dumps
from pathlib import Path
import sys
from typing import Optional
from typing_extensions import Annotated
import zipfile

from rich.console import Console  # type: ignore[import-not-found]
from rich.table import Table  # type: ignore[import-not-found]
from rich.tree import Tree  # type: ignore[import-not-found]

from typer import Typer, Argument  # type: ignore

from .config import books_configuration
from .epub import process_volume, process_container, process_opf
from .extract import extract_node, extract_text, extract_xml


app = Typer()
console = Console()
stderr_console = Console(stderr=True)


def print_info(message: str) -> None:
    stderr_console.print(f"[blue]{message}[/blue]")


def print_error(message: str) -> None:
    stderr_console.print(f"[red]{message}[/red]")


def get_path(book_id_or_path: str) -> Path | zipfile.Path | None:

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
            print_error(f"Path {path} is not a directory or a valid EPUB file.")
            return None
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

        console.print(table)


@app.command()
def title(book_id_or_path: str):
    path = get_path(book_id_or_path)
    if path:
        volume_data = process_volume(path)
        console.print("Metadata:", volume_data["metadata"]["title"])
        console.print("NCX:", volume_data["ncx"]["title"])


@app.command()
def container(book_id_or_path: str):
    epub_root = get_path(book_id_or_path)
    if epub_root:
        opf_path = epub_root / process_container(epub_root / "META-INF/container.xml") 
        console.print(opf_path)


@app.command()
def opf(book_id_or_path: str):
    epub_root = get_path(book_id_or_path)
    if epub_root:
        opf_path = process_container(epub_root / "META-INF/container.xml")
        opf_data = process_opf(epub_root, opf_path)
        console.print("OPF Version:      ", opf_data["version"])
        console.print("Unique Identifier:", opf_data["unique_identifier"])
        console.print("Prefix:           ", opf_data["prefix"])
        console.print("XML Language:     ", opf_data["xml_lang"])
        console.print()
        console.print(opf_data["metadata"])
        console.print()

        table = Table(title="Manifest")
        table.add_column("id", style="cyan")
        table.add_column("href", style="magenta")
        table.add_column("media-type", style="green")
        table.add_column("properties", style="yellow")

        for item_id, item_data in opf_data["manifest"].items():
            table.add_row(item_id, item_data["href"], item_data.get("media-type", ""), item_data.get("properties", ""))

        console.print(table)


@app.command()
def spine(book_id_or_path: str):
    path = get_path(book_id_or_path)
    if path:
        volume_data = process_volume(path)
        manifest = volume_data["manifest"]

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
    if path:
        volume_data = process_volume(path)
        console.print(volume_data["ncx"]["title"])
        console.print(volume_data["ncx"]["head"])

        tree = Tree("[bold]NCX[/bold]")
        for nav_point in volume_data["ncx"]["navMap"]:
            build_nav_tree(tree, nav_point)

        console.print(tree)


@app.command()
def extract_map(
    book_id_or_path: str,
    itemref: Annotated[Optional[str], Argument()] = None,
    address: Annotated[Optional[str], Argument()] = None,
    recurse: bool = False
) -> None:
    path = get_path(book_id_or_path)
    if path:
        volume_data = process_volume(path)
        manifest = volume_data["manifest"]

        if itemref is None:
            items = []
            for item_ref in volume_data["spine"]["itemrefs"]:
                file_path = manifest[item_ref]["path"]
                items.append([item_ref, extract_node(file_path, address=None, recurse=recurse, dictionary=not recurse)])
            console.print(dumps(items, indent=2))
        else:
            if itemref not in manifest:
                print_error(f"Item reference '{itemref}' not found in the manifest.")
                return

            file_path = manifest[itemref]["path"]
            node = extract_node(file_path, address, recurse=recurse, dictionary=not recurse)
            if node:
                console.print(node)
            else:
                print_error(f"Address '{address}' not found in item reference '{itemref}'.")


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


def get_file_path(book_id_or_path: str, itemref: str) -> Path | None:

    path = get_path(book_id_or_path)
    if path:
        volume_data = process_volume(path)
        manifest = volume_data["manifest"]

        if itemref not in manifest:
            print_error(f"Item reference '{itemref}' not found in the manifest.")
            return None

        return manifest[itemref]["path"]
    else:
        return None


@app.command()
def tree(
    book_id_or_path: str,
    itemref: str,
    address: Annotated[Optional[str], Argument()] = None,
    depth: Optional[int] = None
) -> None:

    file_path = get_file_path(book_id_or_path, itemref)

    if file_path:
        tree = Tree(itemref, style="bold")
        node = extract_node(file_path, address, recurse=True, dictionary=False)
        if node:
            build_tree(tree, node, depth)

            console.print(tree)
        else:
            print_error(f"Address '{address}' not found in item reference '{itemref}'.")


@app.command()
def text(
    book_id_or_path: str,
    itemref: str,
    address: Annotated[Optional[str], Argument()] = None,
) -> None:

    file_path = get_file_path(book_id_or_path, itemref)

    if file_path:
        text = extract_text(file_path, address)
        if text:
            console.print(text)
        else:
            print_error(f"Address '{address}' not found in item reference '{itemref}'.")



@app.command()
def xml(
    book_id_or_path: str,
    itemref: str,
    address: Annotated[Optional[str], Argument()] = None,
) -> None:
    file_path = get_file_path(book_id_or_path, itemref)

    if file_path:
        xml = extract_xml(file_path, address)
        if xml:
            console.print(xml)
        else:
            print_error(f"Address '{address}' not found in item reference '{itemref}'.")
