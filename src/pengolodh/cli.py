from json import dumps
from pathlib import Path
from typing import Optional

import typer  # type: ignore

from .epub import process_volume
from .extract import extract_node


app = typer.Typer()


@app.command()
def volume(path_string: str):
    path = Path(path_string)
    volume_data = process_volume(path)
    print(volume_data["ncx"]["title"])


@app.command()
def spine(path_string: str):
    path = Path(path_string)
    volume_data = process_volume(path)
    manifest = volume_data["manifest"]
    for itemref in volume_data["spine"]["itemrefs"]:
        print(itemref, manifest[itemref]["path"])


@app.command()
def extract_map(volume_path: str, itemref: str, address: Optional[str] = None) -> None:

    volume_data = process_volume(Path(volume_path))
    manifest = volume_data["manifest"]
    file_path = manifest[itemref]["path"]

    print(extract_node(file_path, address, recurse=False, dictionary=True))


@app.command()
def extract_map2(volume_path: str, itemref: str, address: Optional[str] = None) -> None:

    volume_data = process_volume(Path(volume_path))
    manifest = volume_data["manifest"]
    file_path = manifest[itemref]["path"]

    print(dumps(extract_node(file_path, address, recurse=True, dictionary=False)))


@app.command()
def extract_map3(volume_path: str) -> None:

    items = []
    volume_data = process_volume(Path(volume_path))
    manifest = volume_data["manifest"]
    for itemref in volume_data["spine"]["itemrefs"]:
        file_path = manifest[itemref]["path"]
        items.append([itemref, extract_node(file_path, address=None, recurse=True, dictionary=False)])
    
    print(dumps(items, indent=2))
