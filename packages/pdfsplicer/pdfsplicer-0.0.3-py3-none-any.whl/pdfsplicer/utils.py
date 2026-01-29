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


def pretty_errors(f):
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            print(e, file=sys.stderr)
            sys.exit(1)

    return wrapper
