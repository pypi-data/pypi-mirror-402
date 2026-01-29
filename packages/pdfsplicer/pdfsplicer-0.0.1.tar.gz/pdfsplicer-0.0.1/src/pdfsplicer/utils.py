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


import sys
from typing import Literal


def test():
    def wrapper(f):
        f.__test__ = True
        return f

    return wrapper


def assert_throws(exec_type, call):
    try:
        call()
    except exec_type:
        return
    except:
        raise AssertionError("Function raised unexpected exception")
    else:
        raise AssertionError("Function did not throw")


def read_or_default(default):
    while (selection := input("> ").upper()) not in ["Y", "N", ""]:
        ...
    if selection == "":
        selection = default
    return selection


def confirm_or_exit(msg: str, default: Literal["Y", "N"] = "Y", on_reject=None):
    print(bold(msg + " " + list_options(default)))
    selection = read_or_default(default)

    if selection == "N":
        if on_reject is not None:
            print(on_reject)
        sys.exit(1)
    else:
        return


def list_options(default: Literal["Y", "N"]) -> str:
    if default == "Y":
        return f"({underline("Y")}/n)"
    else:
        return f"(y/{underline("N")})"


def bold(msg: str) -> str:
    return f"\x1b[1;39m{msg}\x1b[0;39m"


def underline(msg: str) -> str:
    return f"\x1b[4;39m{msg}\x1b[0;39m"
