# Copyright 2023-2026 Geoffrey R. Scheller
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Tools for iterables
-------------------

.. admonition:: Library of functions for iterating iterables

    +-----------+-------------------------------------------+
    | Module    | Description                               |
    +===========+===========================================+
    | merging   | Concatenating and merging iterables       |
    +-----------+-------------------------------------------+
    | drop_take | Dropping and taking values from iterables |
    +-----------+-------------------------------------------+
    | folding   | Reducing and accumulating iterables       |
    +-----------+-------------------------------------------+

.. important::

    **Assumptions:**

    - iterables are not necessarily iterators
    - at all times iterator protocol is assumed to be followed

    - all iterators are assumed to be iterable
    - for all iterators ``foobar`` we assume ``iter(foobar) is foobar``

"""

__author__ = 'Geoffrey R. Scheller'
__copyright__ = 'Copyright (c) 2023-2026 Geoffrey R. Scheller'
__license__ = 'Apache License 2.0'
