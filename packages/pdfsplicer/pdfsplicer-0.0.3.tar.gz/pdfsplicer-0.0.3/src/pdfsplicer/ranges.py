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

import re

from pdfsplicer.utils import test, assert_throws

__all__ = ("parse_range",)

INT_PATTERN = re.compile(r"^[+-]?[1-9]\d*$")
SLICE_PATTERN = re.compile(r"^(?:[+-]?[1-9]\d*:|:){1,2}(?:[+-]?[1-9]\d*)?$")


def parse_range(arg: str) -> slice:
    if INT_PATTERN.match(arg):
        value = int(arg)
        if value == -1:
            return slice(-1, None, None)
        elif value > 0:
            return slice(value - 1, value)
        else:
            return slice(value, value + 1)

    if not SLICE_PATTERN.match(arg):
        raise ValueError(f"Invalid page range format: {arg}")

    parts = arg.split(":")
    start = int(parts[0]) if parts[0] != "" else None
    stop = int(parts[1]) if parts[1] != "" else None
    step = int(parts[2]) if len(parts) == 3 and parts[2] != "" else None

    if start is not None and start > 0:
        start -= 1
    if stop is not None and stop > 0:
        stop -= 1

    return slice(start, stop, step)


@test()
def parse_range_can_parse_single_pages():
    assert parse_range("1") == slice(0, 1, None)
    assert parse_range("-1") == slice(-1, None, None)
    assert parse_range("5") == slice(4, 5, None)
    assert parse_range("-5") == slice(-5, -4, None)


@test()
def ranges_with_start_only_are_parsed():
    assert parse_range("1:") == slice(0, None, None)
    assert parse_range("-1:") == slice(-1, None, None)
    assert parse_range("5:") == slice(4, None, None)
    assert parse_range("-5:") == slice(-5, None, None)


@test()
def ranges_with_stop_only_are_parsed():
    assert parse_range(":1") == slice(None, 0, None)
    assert parse_range(":-1") == slice(None, -1, None)
    assert parse_range(":5") == slice(None, 4, None)
    assert parse_range(":-5") == slice(None, -5, None)


@test()
def ranges_with_step_only_are_parsed():
    assert parse_range("::1") == slice(None, None, 1)
    assert parse_range("::-1") == slice(None, None, -1)
    assert parse_range("::3") == slice(None, None, 3)
    assert parse_range("::-3") == slice(None, None, -3)


@test()
def ranges_with_start_and_stop_values_are_parsed():
    assert parse_range("1:2") == slice(0, 1, None)
    assert parse_range("-1:-2") == slice(-1, -2, None)
    assert parse_range("5:10") == slice(4, 9, None)
    assert parse_range("-5:-10") == slice(-5, -10, None)
    assert parse_range("5:-10") == slice(4, -10, None)
    assert parse_range("-5:10") == slice(-5, 9, None)


@test()
def ranges_with_start_and_step_values_are_parsed():
    assert parse_range("1::2") == slice(0, None, 2)
    assert parse_range("1::-2") == slice(0, None, -2)
    assert parse_range("-1::2") == slice(-1, None, 2)
    assert parse_range("-1::-2") == slice(-1, None, -2)


@test()
def ranges_with_stop_and_step_values_are_parsed():
    assert parse_range(":1:2") == slice(None, 0, 2)
    assert parse_range(":1:-2") == slice(None, 0, -2)
    assert parse_range(":-1:2") == slice(None, -1, 2)
    assert parse_range(":-1:-2") == slice(None, -1, -2)


@test()
def ranges_with_start_stop_and_step_values_are_parsed():
    assert parse_range("1:1:2") == slice(0, 0, 2)
    assert parse_range("-1:1:-2") == slice(-1, 0, -2)
    assert parse_range("1:-1:2") == slice(0, -1, 2)
    assert parse_range("-1:-1:-2") == slice(-1, -1, -2)
    assert parse_range("5:1:2") == slice(4, 0, 2)
    assert parse_range("-5:1:-2") == slice(-5, 0, -2)
    assert parse_range("5:5:2") == slice(4, 4, 2)
    assert parse_range("-5:-5:-2") == slice(-5, -5, -2)


@test()
def invalid_ranges_throw():
    assert_throws(ValueError, lambda: parse_range(""))
    assert_throws(ValueError, lambda: parse_range("0"))
    assert_throws(ValueError, lambda: parse_range("0:1"))
    assert_throws(ValueError, lambda: parse_range("1:0:-1"))
    assert_throws(ValueError, lambda: parse_range("1:1:1:1"))
