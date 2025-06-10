# pengolodh

A text preparation pipeline

Initially focused on extracting text from EPUBs for citation and stand-off annotation.

## To Set Up

- `uv sync`
- activate venv

## To Run

- `pengolodh volume <path-to-unzipped-epub>`

will either print the title of the volume or, if the assertions are too strict, throw an exception.

- `pengolodh spine <path-to-unzipped-epub>`

will either print the "spine" of the volume, or, if the assertions are too strict, throw an exception.
