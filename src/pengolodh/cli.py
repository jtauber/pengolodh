from pathlib import Path
from typing import Optional

import typer

from .epub import process_volume
from .extract import extract_fragment2


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

    print(extract_fragment2(file_path, address))


