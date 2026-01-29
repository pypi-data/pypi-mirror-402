# Copyright 2023-2025 Geoffrey R. Scheller
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
Merging Iterables
-----------------

.. admonition:: module pythonic_fp.iterables.merging

    Functions to merge multiple iterables together into one.

"""

from collections.abc import Iterable, Iterator
from enum import auto, Enum

__all__ = [
    'MergeEnum',
    'concat',
    'merge',
    'exhaust',
    'blend',
]


class MergeEnum(Enum):
    """Iterable Blending Enums.

    - **MergeEnum.Concat:** Concatenate first to last
    - **MergeEnum.Merge:** Merge until one is exhausted
    - **MergeEnum.Exhaust:** Merge until all are exhausted

    """

    Concat = auto()
    Merge = auto()
    Exhaust = auto()


def concat[D](*iterables: Iterable[D]) -> Iterator[D]:
    """Sequentially concatenate multiple iterables together.

    .. warning::
        An infinite iterable will prevent subsequent iterables from
        yielding any values.

    .. note::

        Performant to the standard library's ``itertools.chain``.

    :param iterables: Iterables to concatenate.
    :returns: Iterator of concatenated values from the iterables.

    """
    for iterator in map(lambda x: iter(x), iterables):
        while True:
            try:
                value = next(iterator)
                yield value
            except StopIteration:
                break


def merge[D](*iterables: Iterable[D], yield_partials: bool = False) -> Iterator[D]:
    """Merge together ``iterables`` until one is exhausted.

    .. note::

        When ``yield_partials`` is true, then any unmatched values from other iterables
        already yielded when the first iterable is exhausted are yielded. This prevents
        data lose if any of the iterables are iterators with external references.

    :param iterables: Iterables to merge until one gets exhausted.
    :param yield_partials: Yield any unpaired yielded values from other iterables.
    :returns: Iterator of merged values from the iterables until one is exhausted.

    """
    iter_list = list(map(lambda x: iter(x), iterables))
    values = []
    if (num_iters := len(iter_list)) > 0:
        while True:
            try:
                for ii in range(num_iters):
                    values.append(next(iter_list[ii]))
                yield from values
                values.clear()
            except StopIteration:
                break
        if yield_partials:
            yield from values


def exhaust[D](*iterables: Iterable[D]) -> Iterator[D]:
    """Merge together multiple iterables until all are exhausted.

    :param iterables: Iterables to exhaustively merge.
    :returns: Iterator of merged values from the iterables until all are exhausted.

    """
    iter_list = list(map(lambda x: iter(x), iterables))
    if (num_iters := len(iter_list)) > 0:
        ii = 0
        values = []
        while True:
            try:
                while ii < num_iters:
                    values.append(next(iter_list[ii]))
                    ii += 1
                yield from values
                ii = 0
                values.clear()
            except StopIteration:
                num_iters -= 1
                if num_iters < 1:
                    break
                del iter_list[ii]

        yield from values


def blend[D](
    *iterables: Iterable[D],
    merge_enum: MergeEnum = MergeEnum.Concat,
    yield_partials: bool = False,
) -> Iterator[D]:
    """Merge behavior based on value of merge_enum parameter.

    :param iterables: Iterables to blend together.
    :param merge_enum: ``MergeEnum`` to determine merging behavior.
    :param yield_partials: Yield unpaired values from other iterables.
    :returns: An iterator of type ``D``.
    :raises ValueError: When an unknown ``MergeEnum`` is given.

    """
    match merge_enum:
        case MergeEnum.Concat:
            return concat(*iterables)
        case MergeEnum.Merge:
            return merge(*iterables, yield_partials=yield_partials)
        case MergeEnum.Exhaust:
            return exhaust(*iterables)

    raise ValueError('Unknown MergeEnum given')
