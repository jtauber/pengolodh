from json import dumps
from pathlib import Path
import sys
from typing import Optional
import zipfile

from rich import print as rich_print  # type: ignore[import-not-found]
from rich.console import Console  # type: ignore[import-not-found]
from rich.table import Table  # type: ignore[import-not-found]

import typer  # type: ignore

from .config import books_configuration
from .epub import process_volume
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
def volume(book_id_or_path: str):
    path = get_path(book_id_or_path)
    volume_data = process_volume(path)
    print(volume_data["ncx"]["title"])


@app.command()
def spine(book_id_or_path: str):
    path = get_path(book_id_or_path)
    volume_data = process_volume(path)
    manifest = volume_data["manifest"]

    table = Table(title="Spine")
    table.add_column("Item Ref", style="cyan")
    table.add_column("Path", style="magenta")

    for itemref in volume_data["spine"]["itemrefs"]:
        table.add_row(itemref, str(manifest[itemref]["path"]))

    console = Console()
    console.print(table)


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

    print(extract_xml(file_path, address))
