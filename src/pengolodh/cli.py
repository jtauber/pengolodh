from pathlib import Path

import typer

from .epub import process_volume


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
