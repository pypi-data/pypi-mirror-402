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
import textwrap

from pypdf import PdfWriter, PageRange

from pdfsplicer.ranges import parse_range
from pdfsplicer.utils import confirm_or_exit

def snip(args):
    slices = [parse_range(r) for r in args.range]
    merger = PdfWriter()
    with open(args.file, "rb") as f:
        for page_range in slices:
            merger.append(f, pages=PageRange(page_range))
            f.seek(0)
    if args.out is None:
        if not args.yes:
            confirm_or_exit(
                f"This operation will rewrite `{args.file}`. This may be a "
                f"destructive action.\nAre you sure you want to continue?",
                on_reject="If you do not want to modify the PDF in-place, "
                          "provide the `--out` option.\nSee --help for details."
            )
        args.out = args.file

    with open(args.out, "wb") as f:
        merger.write(f)


def main():
    parser = argparse.ArgumentParser(prog="pdfsplicer")
    subparsers = parser.add_subparsers(required=True)

    snip_parser = subparsers.add_parser(
        "snip",
        help="Slices pages from the given PDF",
        epilog=textwrap.dedent("""
            Ranges are 1-indexed page numbers or Python-style slices.
            Negative indices can be used with -1 being the last page.
            
            For example:
              - `1` the first page
              - `-2` the second to last page
              - `2:` everything but the first page
              - `:-1` everything but the last page
              - `2:5` pages 2, 3, and 4
              - `5:2:-1` pages 5, 4, and 3
              - `::2` every odd-numbered page
              - `:5 6:` everything except page 5
            Note: unlike Python slices, these are 1-indexed, inclusive ranges
            
            Example usage:
            - Pages 2, 3, 4, 6, ..., -2 (second to last page):
                pdfsplicer snip foo.pdf 2:4 6:-1 --out bar.pdf
            - Reverse all pages:
                pdfsplicer snip foo.pdf ::-1 --out bar.pdf
        """),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    snip_parser.add_argument(
        "file", type=str,
        help="The source file to process"
    )
    snip_parser.add_argument(
        "range", type=str, nargs="+",
        help=("1-indexed, inclusive Python-style page slices: start:stop:step. "
              + "Multiple ranges can be provided, in which case the ranges are "
              + "concatenated in the resulting PDF."),
    )
    snip_parser.add_argument(
        "-o", "--out", type=str,
        help="The destination file. If not provided, the PDF is modified "
             "in-place after asking confirmation."
    )
    snip_parser.add_argument(
        "-y", "--yes", action="store_true",
        help="Whether to accept the default choice when asked for confirmation"
    )
    snip_parser.set_defaults(func=snip)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
