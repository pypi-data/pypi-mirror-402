# PDFSplicer

[![Repository](https://img.shields.io/badge/jamesansley%2Fpdfsplicer-102335?logo=codeberg&labelColor=07121A)](https://codeberg.org/jamesansley/pdfsplicer)
[![License](https://img.shields.io/badge/GPL--3.0-002d00?label=license)](https://codeberg.org/jamesansley/pdfsplicer/src/branch/main/LICENCE)
[![PyPi](https://img.shields.io/pypi/v/pdfsplicer?label=PyPi&labelColor=%23ffd343&color=%230073b7)](https://pypi.org/project/pdfsplicer/)

A CLI to splice and dice your PDFs

## Install

Some variation of

```bash
pip install pdfsplicer
```

or

```bash
pipx install pdfsplicer
```

## Usage

The `pdfsplicer` command line application takes several input file PDFs, each
with a list of page indices or ranges to slice, and concatenates the result,
writing to an output PDF.

For example, the following will take pages one and three from foo.pdf, all
except the first and last pages of bar.pdf, and will write the result to
baz.pdf:

    pdfsplicer -f foo.pdf 1 3 -f bar.pdf 2:-1 -o baz.pdf

Rearranged for clarity:

    pdfsplicer \
        -f foo.pdf 1 3 \
        -f bar.pdf 2:-1 \
        -o baz.pdf

Pages can be sliced from PDFs with 1-based indices. See `--help` for more
information.
