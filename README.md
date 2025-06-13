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

will give information about the root node of the given item.

- `pengolodh extract-map <path-to-unzipped-epub> <item-ref> --address <address>`

will do the above but for the node with the given `address` rather than the root node.

Note that the name `extract-map` is historical and will likely change.

## What is an `item-ref`?

An `item-ref` is an identifier for a particular HTML file in the EPUB given by the first column of the output of the `spine` command.

## What is an `address`?

An `address` is a dot-separated path to a particular element in an HTML file. `5.1.3` would mean the third child or the first child of the fifth child of the root.
