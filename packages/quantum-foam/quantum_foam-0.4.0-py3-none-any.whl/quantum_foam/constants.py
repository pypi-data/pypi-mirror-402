# The MIT License (MIT)
# Copyright (c) 2025, 2026 The Galactipy Contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
# OR OTHER DEALINGS IN THE SOFTWARE.


"""Constants for Quantum Foam."""

import re

SOLOVER_ANY_REGEX = re.compile(
    r"""
        ^v?
        (?P<solover>[1-9]\d*)
        (?P<prerelease_segment>-
            (?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)
            (?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*
        )?
        (?P<build_segment>\+
            [0-9a-zA-Z-]+
            (?:\.[0-9a-zA-Z-]+)*
        )?
        $
    """,
    re.VERBOSE,
)

CALVER_ANY_REGEX = re.compile(
    r"""
        ^v?
        (?P<base>
        (?P<year>\d{2}|\d{4,5})
        \.
        (?P<minor>\d{1,2})
        (?:\.(?P<micro>\d{1,2}))?)
        (?P<prerelease_segment>-
            (?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)
            (?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*
        )?
        (?P<build_segment>\+
            [0-9a-zA-Z-]+
            (?:\.[0-9a-zA-Z-]+)*
        )?
        $
    """,
    re.VERBOSE,
)
