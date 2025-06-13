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

- `pengolodh extract-map <path-to-unzipped-epub> <item-ref>`

(where `item-ref` comes from the first column of the output of `spine`) will give information about the root node of the given item.

- `pengolodh extract-map <path-to-unzipped-epub> <item-ref> --address <address>`

will do the above but for the node with the given `address` rather than the root node.

Note that the name `extract-map` is historical and will likely change.
