# pengolodh

A text preparation pipeline

Initially focused on extracting text from EPUBs for citation and stand-off annotation.

## To Run

- `uv sync`
- activate venv
- `pengolodh volume <path-to-unzipped-epub>`

Will either print the title of the volume or, if the assertions are too strict, throw an exception.
