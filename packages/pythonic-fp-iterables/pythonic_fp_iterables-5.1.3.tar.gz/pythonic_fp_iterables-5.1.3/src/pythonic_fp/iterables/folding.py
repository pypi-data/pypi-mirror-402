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
Folding
-------

.. admonition:: module pythonic_fp.iterables.folding

    Functions to reduce and accumulate values from iterables.

"""

from collections.abc import Callable, Iterable, Iterator
from typing import cast, Never
from pythonic_fp.fptools.function import negate, swap
from pythonic_fp.fptools.maybe import MayBe
from pythonic_fp.gadgets.sentinels.novalue import NoValue
from .drop_take import drop_while, take_while_split

__all__ = [
    'accumulate',
    'reduce_left',
    'fold_left',
    'maybe_fold_left',
    'sc_reduce_left',
    'sc_reduce_right',
]


def accumulate[D, L](
    iterable: Iterable[D], f: Callable[[L, D], L], initial: L | NoValue = NoValue()
) -> Iterator[L]:
    """Returns an iterator of partial fold values.

    A pure Python version of standard library's ``itertools.accumulate``

    - function ``f`` does not default to addition (for typing flexibility)
    - begins accumulation with an "optional" ``initial`` value

    :param iterable: iterable to be folded
    :param f: two parameter function, first parameter for accumulated value
    :param initial: "optional" initial value to start fold
    :return: an iterator of the intermediate fold values

    """
    it = iter(iterable)
    try:
        it0 = next(it)
    except StopIteration:
        if initial is NoValue():
            return
        yield cast(L, initial)
    else:
        if initial is not NoValue():
            init = cast(L, initial)
            yield init
            acc = f(init, it0)
            for ii in it:
                yield acc
                acc = f(acc, ii)
            yield acc
        else:
            acc = cast(L, it0)  # in this case L = D
            for ii in it:
                yield acc
                acc = f(acc, ii)
            yield acc


def reduce_left[D](iterable: Iterable[D], f: Callable[[D, D], D]) -> D | Never:
    """Fold an iterable left with a function.

    .. Warning::

       This function never return if given an infinite iterable.

    .. Warning::

       This function does not catch or re-raises exceptions from ``f``.

    :param iterable: iterable to be reduced (folded)
    :param f: two parameter function, first parameter for accumulated value
    :return: reduced value from the iterable
    :raises StopIteration: when called on an empty iterable
    :raises Exception: does not catch any exceptions from ``f``

    """
    it = iter(iterable)
    try:
        acc = next(it)
    except StopIteration as exc:
        msg = 'Attempt to reduce an empty iterable?'
        raise StopIteration(msg) from exc

    for v in it:
        acc = f(acc, v)

    return acc


def fold_left[D, L](
    iterable: Iterable[D], f: Callable[[L, D], L], initial: L
) -> L | Never:
    """Fold an iterable left with a function and initial value.

    - not restricted to ``__add__`` for the folding function
    - initial value required, does not default to ``0`` for initial value
    - handles non-numeric data just find

    .. Warning::

       This function never return if given an infinite iterable.

    .. Warning::

       This function does not catch any exceptions ``f`` may raise.

    :param iterable: iterable to be folded
    :param f: two parameter function, first parameter for accumulated value
    :param initial: mandatory initial value to start fold
    :return: the folded value

    """
    acc = initial
    for v in iterable:
        acc = f(acc, v)
    return acc


def maybe_fold_left[D, L](
    iterable: Iterable[D], f: Callable[[L, D], L], initial: L | NoValue = NoValue()
) -> MayBe[L] | Never:
    """Folds an iterable left with an "optional" initial value..

    - when an initial value is not given then ``L = D``
    - if iterable empty and no ``initial`` value given, return ``MayBe()``

    .. Warning::

       This function never return if given an infinite iterable.

    .. Warning::

        This function returns a ``MayBe()`` when ``f`` raises any
        exception what-so-ever. The exception is thrown away.

    :param iterable: The iterable to be folded.
    :param f: First argument is for the accumulated value.
    :param initial: Mandatory initial value to start fold.
    :return: MayBe of a successfully folded value, otherwise MayBe()

    """
    acc: L
    it = iter(iterable)
    if initial is NoValue():
        try:
            acc = cast(L, next(it))  # in this case L = D
        except StopIteration:
            return MayBe()
    else:
        acc = cast(L, initial)

    for v in it:
        try:
            acc = f(acc, v)
        except Exception:
            return MayBe()

    return MayBe(acc)


def sc_reduce_left[D](
    iterable: Iterable[D],
    f: Callable[[D, D], D],
    start: Callable[[D], bool] = (lambda d: True),
    stop: Callable[[D], bool] = (lambda d: False),
    include_start: bool = True,
    include_stop: bool = True,
) -> tuple[MayBe[D], Iterator[D]]:
    """Short circuit version of a left reduce.

    Useful for infinite iterables.

    Behavior for default arguments will

    - left reduce finite iterable
    - start folding immediately
    - continue folding until end (of a possibly infinite iterable)

    :param iterable: iterable to be reduced from the left
    :param f: two parameter function, first parameter for accumulated value
    :param start: delay starting the fold until it returns true
    :param stop: prematurely stop the fold when it returns true
    :param include_start: if true, include fold starting value in fold
    :param include_stop: if true, include stopping value in fold
    :return: tuple of a MayBe of the folded value and iterator of remaining iterables

    """
    it_start = drop_while(iterable, negate(start))
    if not include_start:
        try:
            next(it_start)
        except StopIteration:
            pass
    it_reduce, it_rest = take_while_split(it_start, negate(stop))
    mb_reduced = maybe_fold_left(it_reduce, f)
    if include_stop:
        if mb_reduced:
            try:
                last = next(it_rest)
                mb_reduced = MayBe(f(mb_reduced.get(), last))
            except StopIteration:
                pass
        else:
            try:
                last = next(it_rest)
                mb_reduced = MayBe(last)
            except StopIteration:
                pass

    return (mb_reduced, it_rest)


def sc_reduce_right[D](
    iterable: Iterable[D],
    f: Callable[[D, D], D],
    start: Callable[[D], bool] = (lambda d: False),
    stop: Callable[[D], bool] = (lambda d: False),
    include_start: bool = True,
    include_stop: bool = True,
) -> tuple[MayBe[D], Iterator[D]]:
    """Short circuit version of a right reduce.

    Useful for infinite and non-reversible iterables.

    Behavior for default arguments will

    - right reduce finite iterable
    - start folding at end (of a possibly infinite iterable)
    - continue reducing right until beginning

    :param iterable: iterable to be reduced from the right
    :param f: two parameter function, second parameter for accumulated value
    :param start: delay starting the fold until it returns true
    :param stop: prematurely stop the fold when it returns true
    :param include_start: if true, include fold starting value in fold
    :param include_stop: if true, include stopping value in fold
    :return: tuple of a MayBe of the folded value and iterator of remaining iterables

    """
    it_start, it_rest = take_while_split(iterable, negate(start))
    list1 = list(it_start)
    if include_start:
        try:
            begin = next(it_rest)
        except StopIteration:
            pass
        else:
            list1.append(begin)

    list1.reverse()
    it_reduce, it_stop = take_while_split(list1, negate(stop))

    mb_reduced = maybe_fold_left(it_reduce, swap(f))
    if include_stop:
        try:
            end = next(it_stop)
        except StopIteration:
            pass
        else:
            if mb_reduced:
                mb_reduced = MayBe(f(end, mb_reduced.get()))
            else:
                mb_reduced = MayBe(end)

    return (mb_reduced, it_rest)
