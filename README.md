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

- `pengolodh extract-map <path-to-unzipped-epub> [--itemref <item-ref>] [--address <address>] [--recurse]`

will give information about HTML elements in the EPUB.

If there is an `--itemref` then only that item (i.e. file) will be considered otherwise all items will be traversed.

If there is an `--address` then only that element will be extracted otherwise the root will be extracted.

If there is a `--recurse` then information about the descendants will also be given.

The results are in tuple form if `--recurse` is used, otherwise they are in a dictionary.

Note that the name `extract-map` is historical and will likely change.

These three variants will soon be combined:

## Some Examples of `extract-map`

```
❯ pengolodh extract-map <path-to-unzipped-epub> --itemref chapter01
{'label': 'body.text#text', 'offset': 0, 'length': 170401, 'child_count': 1}

❯ pengolodh extract-map <path-to-unzipped-epub> --itemref chapter01 --address 1
{'label': 'div.chapter#chapter01', 'offset': 1, 'length': 170400, 'child_count': 4}

❯ pengolodh extract-map <path-to-unzipped-epub> --itemref chapter01 --address 1.3.2
{'label': 'h2.chapterTitle', 'offset': 7, 'length': 20, 'child_count': 1}

❯ pengolodh extract-map <path-to-unzipped-epub> --itemref chapter01 --address 1.3.2.1
{'label': 'span.bold', 'offset': 7, 'length': 20, 'child_count': 0}

❯ pengolodh extract-map <path-to-unzipped-epub> --itemref chapter01 --address 1.3.2 --recurse
('h2.chapterTitle', 7, 20, [('span.bold', 7, 20, [])])
```

## What is an `item-ref`?

An `item-ref` is an identifier for a particular HTML file in the EPUB given by the first column of the output of the `spine` command.

## What is an `address`?

An `address` is a dot-separated path to a particular element in an HTML file. `5.1.3` would mean the third child or the first child of the fifth child of the root.
