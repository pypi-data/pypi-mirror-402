CHANGELOG
=========

PyPI pythonic-fp.iterables project.

Semantic Versioning
-------------------

Strict 3 digit semantic versioning adopted 2025-05-19.

- **MAJOR** version incremented for incompatible API changes
- **MINOR** version incremented for backward compatible added functionality
- **PATCH** version incremented for backward compatible bug fixes

See `Semantic Versioning 2.0.0 <https://semver.org>`_.

Releases and Important Milestones
---------------------------------

PyPI 5.1.1 - 2025-08-02
~~~~~~~~~~~~~~~~~~~~~~~

Only docstring changes.

PyPI 5.1.0 - 2025-08-02
~~~~~~~~~~~~~~~~~~~~~~~

- changed singletons -> sentinels
- Removed "from __future__ import annotations"
- Added .pyi files

PyPI 5.0.0 - 2025-08-02
~~~~~~~~~~~~~~~~~~~~~~~

General consistency tweaks and fixes across all pythonic-fp projects.

PyPI 4.0.0 - 2025-07-16
~~~~~~~~~~~~~~~~~~~~~~~

Primary purpose was to bring Sphinx documentation in alignment
with other pythonic-fp projects. Ended up making substantial
Sphinx documentation improvements. Will use this documentation
for the other pythonic-fp projects.

- API change

  - renamed pythonic_fp.iterables.foldl to pythonic_fp.iterables.fold_left

PyPI 3.0.0 - 2025-07-06
~~~~~~~~~~~~~~~~~~~~~~~

First PyPI release as ``pythonic-fp.iterables``

- dropping dtools namespace name because there is a repo by that name.

PyPI 2.0.0 - 2025-05-22
~~~~~~~~~~~~~~~~~~~~~~~

- Moved dtools.fp.iterables to its own PyPI project

  - dtools.iterables

- Moved dtools.fp.err_handling to the dtools.containers PyPI project

  - Moved class MayBe -> module dtools.containers.maybe
  - Moved class Xor -> module dtools.containers.xor
  - dropped lazy methods

    - will import dtools.fp.lazy directly for this functionality

PyPI 1.7.0 - 2025-04-22
~~~~~~~~~~~~~~~~~~~~~~~

Last PyPI release as dtools.fp

- API changes along the lines of dtools.ca 3.12
- typing improvements
- docstring changes
- pyproject.toml standardization

PyPI 1.6.0 - 2025-04-07
~~~~~~~~~~~~~~~~~~~~~~~

- typing improvements

PyPI 1.4.0 - 2025-03-16
~~~~~~~~~~~~~~~~~~~~~~~

- much work dtools.iterables

  - finally implemented scReduceL and scReduceR functions
  - tweaked API across iterables module

PyPI 1.3.0 - 2025-01-17
~~~~~~~~~~~~~~~~~~~~~~~

First release as dtools.fp

Repo name changes.

- GitHub: fp -> dtools-fp
- PyPI: grscheller.fp -> dtools.fp

PyPI 1.0.1 - 2024-10-20
~~~~~~~~~~~~~~~~~~~~~~~

- removed docs from repo
- docs for all grscheller namespace projects maintained here
 
  - https://grscheller.github.io/grscheller-pypi-namespace-docs/

PyPI 1.0.0 - 2024-10-18
~~~~~~~~~~~~~~~~~~~~~~~

Decided to make this release first stable release.

- renamed module fp.woException to fp.err_handling
- pytest improvements based on pytest documentation

PyPI 0.4.0 - 2024-10-03
~~~~~~~~~~~~~~~~~~~~~~~

Long overdue PyPI release.

Version 0.3.4.0 - 2024-09-30 (Devel environment only)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

API change for fp.iterables.

- function name changes

  - ``foldL``, ``foldR``, ``foldLsc``, ``foldRsc``
  - ``sc`` stands for "short circuit"

- all now return class woException.MB

Version 0.3.3.7 - 2024-09-22 (Devel environment only)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Added more functions to fp.iterables module.

- take(it: Iterable[D], n: int) -> Iterator[D]
- takeWhile(it: Iterable[D], pred: Callable\[[D], bool\]) -> Iterator[D]
- drop(it: Iterable[D], n: int) -> Iterator[D]
- dropWhile(it: Iterable[D], pred: Callable\[[D], bool\]) -> Iterator[D]

Version 0.3.3.4 - 2024-09-16 (Devel environment only)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Both ``foldL_sc`` and ``foldR_sc`` now have a common paradigm
and similar signatures.

Version 0.3.3.3 - 2024-09-15 (Devel environment only)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Added fp.iterables function ``foldR_sc``

- shortcut version of ``foldR``
- not fully tested
- docstring not updated

Version 0.3.3.2 - 2024-09-14 (Devel environment only)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Added ``foldL_sc``, shortcut version of foldL, 
to fp.iterables.


PyPI 0.3.1 - 2024-08-20
~~~~~~~~~~~~~~~~~~~~~~~

Now fp.iterables no longer exports ``CONCAT``, ``MERGE``, ``EXHAUST``.

- for grscheller.datastructures

  - grscheller.datastructures.ftuple
  - grscheller.datastructures.split_ends

PyPI 0.2.0 - 2024-07-26
~~~~~~~~~~~~~~~~~~~~~~~

- from last PyPI release

  - added accumulate function to fp.iterators

- overall much better docstrings

PyPI 0.1.0 - 2024-07-11
~~~~~~~~~~~~~~~~~~~~~~~

Initial PyPI release as grscheller.fp

Replicated functionality from grscheller.datastructures.

- ``grscheller.core.iterlib -> grscheller.fp.iterators``
