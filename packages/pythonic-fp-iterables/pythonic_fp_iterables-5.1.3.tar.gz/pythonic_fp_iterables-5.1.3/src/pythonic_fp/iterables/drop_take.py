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
Drop and Take
-------------

.. admonition:: module pythonic_fp.iterables.drop_take

    Functions to drop or take values from an iterable.

"""

from collections.abc import Callable, Iterable, Iterator
from pythonic_fp.gadgets.box import Box
from .merging import concat

__all__ = [
    'drop',
    'drop_while',
    'take',
    'take_while',
    'take_split',
    'take_while_split',
]


def drop[D](iterable: Iterable[D], n: int) -> Iterator[D]:
    """Drop the next n values from iterable.

    :param iterable: Iterable whose values are to be dropped.
    :param n: Number of values to be dropped.
    :returns: An iterator of the remaining values.

    """
    iterator = iter(iterable)
    for _ in range(n):
        try:
            next(iterator)
        except StopIteration:
            break
    return iterator


def drop_while[D](iterable: Iterable[D], pred: Callable[[D], bool]) -> Iterator[D]:
    """Drop initial values from iterable while predicate is true.

    :param iterable: Iterable whose values are to be dropped.
    :param pred: Single argument Boolean valued function, the "predicate".
    :returns: An iterator beginning where pred returned false.

    """
    iterator = iter(iterable)
    while True:
        try:
            value = next(iterator)
            if not pred(value):
                iterator = concat((value,), iterator)
                break
        except StopIteration:
            break
    return iterator


def take[D](iterable: Iterable[D], n: int) -> Iterator[D]:
    """Return an iterator of up to n initial values of an iterable.

    :param Iterable: iterable providing the values to be taken.
    :param n: Number of values to be dropped.
    :returns: An iterator of up to n initial values from iterable.

    """
    iterator = iter(iterable)
    for _ in range(n):
        try:
            value = next(iterator)
            yield value
        except StopIteration:
            break


def take_while[D](iterable: Iterable[D], pred: Callable[[D], bool]) -> Iterator[D]:
    """Yield values from iterable while predicate is true.

    .. warning::

        Risk of value loss if iterable is multiple referenced iterator.

    :param iterable: Iterable providing the values to be taken.
    :param pred: Single argument Boolean valued function, the "predicate".
    :returns: An Iterator of of values from iterable until predicate false.

    """
    iterator = iter(iterable)
    while True:
        try:
            value = next(iterator)
            if pred(value):
                yield value
            else:
                break
        except StopIteration:
            break


def take_split[D](iterable: Iterable[D], n: int) -> tuple[Iterator[D], Iterator[D]]:
    """Same as take except also return iterator of remaining values.

    .. Warning::

        **CONTRACT:** Do not access the second returned iterator until the
        first one is exhausted.

    :param iterable: Iterable providing the values to be taken.
    :param n: maximum Number of values to be taken.
    :returns: An iterator of values taken and an iterator of remaining values.

    """
    iterator = iter(iterable)
    itn = take(iterator, n)

    return itn, iterator


def take_while_split[D](
    iterable: Iterable[D], pred: Callable[[D], bool]
) -> tuple[Iterator[D], Iterator[D]]:
    """Yield values from iterable while predicate is true.

    .. Warning::

        **CONTRACT:** Do not access the second returned iterator until
        the first one is exhausted.

    :param iterable: Iterable providing the values to be taken.
    :param pred: Single argument Boolean valued function.
    :returns: Tuple of iterator of values taken and an iterator of remaining values.

    """

    def _take_while(
        iterator: Iterator[D], pred: Callable[[D], bool], val: Box[D]
    ) -> Iterator[D]:
        while True:
            try:
                val.put(next(iterator))
                if pred(val.get()):
                    yield val.pop()
                else:
                    break
            except StopIteration:
                break

    iterator = iter(iterable)
    value: Box[D] = Box()
    it_pred = _take_while(iterator, pred, value)

    return it_pred, concat(value, iterator)
