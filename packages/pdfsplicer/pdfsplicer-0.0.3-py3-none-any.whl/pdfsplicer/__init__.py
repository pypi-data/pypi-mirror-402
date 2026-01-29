# pdfsplicer - a command line PDF editing tool
#
# Copyright (C) 2026 pdfsplicer Contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


import argparse

from pypdf import PdfWriter, PageRange

from pdfsplicer.ranges import parse_range
from pdfsplicer.utils import pretty_errors

HELP = """
Several files can be spliced together with repeated used of the `-f` or `--file`
arguments. Each file must be provided as a list of arguments starting with a
filename/path followed by one or more page ranges (described below). Page
ranges will be pulled from the specified PDF and written to a result PDF
specified by the `--out` option.

For example, the following takes the first and third pages from `foo.pdf` and
all except the first and last pages from `bar.pdf` and generates a new PDF
`baz.pdf`:

    pdfsplicer -f foo.pdf 1 3 -f bar.pdf 2:-1 -o baz.pdf
    
Rearranged for clarity:

    pdfsplicer \\
        -f foo.pdf 1 3 \\
        -f bar.pdf 2:-1 \\
        -o baz.pdf

Pages can be selected from PDFs using page numbers (1-indexed) or Python-style
slices (also 1-indexed). Negative indices can be used for indices and slices
with -1 indexing the last page, -2 the second to last page and so on.

Some examples of indices and ranges:
  - `1` the first page
  - `-2` the second to last page
  - `2:` everything but the first page
  - `:-1` everything but the last page
  - `2:5` pages 2, 3, and 4
  - `5:2:-1` pages 5, 4, and 3
  - `::2` every odd-numbered page
  - `:5 6:` everything except page 5
  
Note again: unlike Python slices, these are 1-indexed ranges
"""

parser = argparse.ArgumentParser(
    prog="pdfsplicer",
    epilog=HELP,
    formatter_class=argparse.RawDescriptionHelpFormatter
)
parser.add_argument(
    "-f", "--file", action="append", nargs="+",
    metavar=("FILENAME", "RANGES"),
    help="The PDF files to slice and concatenate",
)
parser.add_argument(
    "-o", "--out", type=str, required=True,
    help="The destination file"
)


@pretty_errors
def main():
    args = parser.parse_args()
    merger = PdfWriter()
    for file, *ranges in args.file:
        slices = [parse_range(r) for r in ranges]
        with open(file, "rb") as f:
            for page_range in slices:
                merger.append(f, pages=PageRange(page_range))

    with open(args.out, "wb") as f:
        merger.write(f)


if __name__ == "__main__":
    main()
