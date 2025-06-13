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
def extract_map(volume_path: str, itemref: Optional[str] = None, address: Optional[str] = None, recurse: bool = False) -> None:

    volume_data = process_volume(Path(volume_path))
    manifest = volume_data["manifest"]

    if itemref is None:
        items = []
        volume_data = process_volume(Path(volume_path))
        manifest = volume_data["manifest"]
        for item_ref in volume_data["spine"]["itemrefs"]:
            file_path = manifest[item_ref]["path"]
            items.append([item_ref, extract_node(file_path, address=None, recurse=recurse, dictionary=not recurse)])
        print(dumps(items, indent=2))
    else:
        file_path = manifest[itemref]["path"]
        print(extract_node(file_path, address, recurse=recurse, dictionary=not recurse))
