CHANGELOG
=========

PyPI pythonic-fp.containers project.

Semantic Versioning
-------------------

Strict 3 digit semantic versioning adopted 2025-05-19.

- **MAJOR** version incremented for incompatible API changes
- **MINOR** version incremented for backward compatible added functionality
- **PATCH** version incremented for backward compatible bug fixes

See `Semantic Versioning 2.0.0 <https://semver.org>`_.

Releases and Important Milestones
---------------------------------

PyPI 4.0.0 - 2025-09-09
~~~~~~~~~~~~~~~~~~~~~~~

Decided not to deprecated pythonic-fp.queues and moved queue development
back to there.

PyPI 3.0.1 - 2025-09-09
~~~~~~~~~~~~~~~~~~~~~~~

- added .pyi files
- updated Sphinx docs to new format

PyPI 3.0.0 - 2025-08-02
~~~~~~~~~~~~~~~~~~~~~~~

Coordinated entire project pythonic-fp PyPI deployment.

- moved maybe.py and xor.py to fptools, renamed xor.py -> either.py.
- duplicated pythonic_fp.queues -> pythonic_fp.containers.queues

  - deprecating pythonic-fp.queues

PyPI 2.0.0 - 2025-07-06
~~~~~~~~~~~~~~~~~~~~~~~

First PyPI release as pythonic-fp.containers

- switched from pdoc to Sphinx for docstring documentation generation.

PyPI 1.0.0 - 2025-05-22
~~~~~~~~~~~~~~~~~~~~~~~

First PyPI release as dtools.containers

- box.py -> stateful (mutable) container that can contain 0 ot 1 items
- functional_tuple.py -> easier starting point to inherit from tuple
- immutable_list.py -> immutable, guaranteed hashable "list"
- maybe.py -> implements the "maybe" monad from FP
- xor.py -> implements a left biased either monad from FP

PyPI 0.27.1 - 2025-04-22
~~~~~~~~~~~~~~~~~~~~~~~~

- replaced camelCaseNames method names with snake_case_names
- docstring changes
- pyproject.toml standardization

PyPI 0.27.0 - 2025-04-07
~~~~~~~~~~~~~~~~~~~~~~~~

- first PyPI release as dtools.tuples

  - split dtools.datastructures into

    - dtools.tuples
    - dtools.queues

- typing improvements

PyPI 0.25.1 - 2025-01-16
~~~~~~~~~~~~~~~~~~~~~~~~

- Fixed pdoc issues with new typing notation

  - updated docstrings
  - had to add TypeVars

PyPI 0.25.0 - 2025-01-17
~~~~~~~~~~~~~~~~~~~~~~~~

- First release under dtools.datastructures name

PyPI 0.24.0 - 2024-11-18
~~~~~~~~~~~~~~~~~~~~~~~~

- Changed flatMap to bind thru out project

PyPI 0.23.1 - 2024-11-18
~~~~~~~~~~~~~~~~~~~~~~~~

- Fixed bug with datastructures.tuple module

  - forgot to import std lib typing.cast into tuples.py

- renamed class FTuple -> ftuple

  - ftuple now takes 0 or 1 iterables, like list and tuple do

- created factory function for original constructor use case

  - ``FT[D](*ds: D) -> ftuple[D]``

PyPI 0.22.1 - 2024-10-20
~~~~~~~~~~~~~~~~~~~~~~~~

Removed docs from repo. Documentation for all grscheller namespace
projects is now maintained
here: https://grscheller.github.io/grscheller-pypi-namespace-docs/

PyPI 0.22.0 - 2024-10-18
~~~~~~~~~~~~~~~~~~~~~~~~

- made classes in nodes module less passive with better encapsulation
- compatible with:

  - grscheller.fp >= 1.0.0 < 1.0.1
  - grscheller.circular-array >= 3.6.1 < 3.7

PyPI 0.21.0 - 2024-08-20
~~~~~~~~~~~~~~~~~~~~~~~~

Got back to a state maintainer is happy with. Many dependencies needed
updating first.

- works with all the current versions of fp and circular-array
- preparing for PyPI 0.21.0 release

Version 0.20.5.0 - 2024-08-17
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Development environment only. Datastructures coming back together

- updated to use grscheller.fp.nada instead of grscheller.untyped.nothing

  - made debugging tons easier

- updated to use all latest PyPI versions of dependencies
- three failed tests involving class SplitEnd
- putting off PyPI v1.0.0 release indefinitely

  - all dependencies need to be at v1.0+
  - need to work out SplitEnd bugs
  - still need to finalize design (need to use it!)
  - need to find good SplitEnd use case
  - other Stack variants like SplintEnd??? (shared data/node variants?)

PyPI 0.20.2.0 - 2024-08-03
~~~~~~~~~~~~~~~~~~~~~~~~~~

Development environment only.
Still preparing for 1.0.0 datastructures release.

- Going down a typing rabbit hole

  - as I tighten up typing, I find I must do so for dependencies too
  - using `# type: ignore` is a band-aid, use `@overload` and `cast` instead
  - using `@overload` to "untype" optional parameters is the way to go
  - use `cast` only when you have knowledge beyond what the typechecker can know

PyPI 0.19.0 - 2024-07-15
~~~~~~~~~~~~~~~~~~~~~~~~

- continuing to prepare for PyPI release 1.0.0
- cleaned up docstrings for a 1.0.0 release
- changed accumulate1 to accumulate for FTuple
- considering requiring grscheller.fp as a dependency

Version 0.18.0.0 - Devel environment only
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Beginning to prepare for PyPI release 1.0.0

- first devel version requiring circular-array 3.1.0
- still some design work to be done
- TODO: Verify flatMap family yields results in "natural" order

Version 0.17.0.4 - Devel environment only
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Start of effort to relax None restrictions.

- have begun relaxing the requirement of not storing None as a value

  - completed for queues.py

- requires grscheller.circular-array >= 3.0.3.0
- perhaps next PyPI release will be v1.0.0 ???

Version 0.16.0.0 - Devel environment only
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Preparing to support PEP 695 generics.

- Requires Python >= 3.12
- preparing to support PEP 695 generics

  - will require Python 3.12
  - will not have to import typing for Python 3.12 and beyond
  - BUT... mypy does not support PEP 695 generics yet (Pyright does)

- bumped minimum Python version to >= 3.12 in pyproject.toml
- map methods mutating objects don't play nice with typing

  - map methods now return copies
  - THEREFORE: tests need to be completely overhauled

Version 0.14.1.1 - Devel environment only
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Preparing to add TypeVars.

- tests working with grscheller.circular-array >= 3.0.0, \<3.2

  - lots of mypy complaints
  - first version using TypeVars will be 0.15.0.0

PyPI 0.14.0 - 2024-03-09
~~~~~~~~~~~~~~~~~~~~~~~~

- updated dependency on CircularArray class

  - dependencies = ["grscheller.circular-array >= 0.2.0, < 2.1"]

- minor README.md wordsmithing
- keeping project an Alpha release for now

Version 0.13.3.1 - Devel environment only
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Preparing for another PyPI release soon.

- overhauled docstrings with Markdown markup
- updated pyproject.py to drop project back to an Alpha release

  - allows more renaming flexibility
  - intending to develop more graph based data structures

- renamed class core.nodes.Tree_Node to core.node.BT_Node

  - BT for Binary Tree (data in each node of tree)

- created class core.nodes.LT_Node

  - LT for Leaf Tree (data are the leaves of the tree)

- removed deprecated reduce method from various classes

  - use foldL instead

PyPI 0.13.2 - 2024-02-20
~~~~~~~~~~~~~~~~~~~~~~~~

Forgot to update pyproject.toml dependencies.

- ``dependencies = ["grscheller.circular-array >= 0.1.1, < 1.1"]``

PyPI 0.13.1 - 2024-01-31
~~~~~~~~~~~~~~~~~~~~~~~~

- FTuple now supports both slicing and indexing

- more tests for FTuple

  - slicing and indexing
  - ``map``, ``foldL``, ``accumulate`` methods
  - ``flatMap``, ``mergeMap``, ``exhaustMap`` methods

- forgot to update CHANGELOG for v0.13.0 release

PyPI 0.13.0 - 2024-01-30
~~~~~~~~~~~~~~~~~~~~~~~~

- BREAKING API CHANGE - CircularArray class removed
- CircularArray moved to its own PyPI & GitHub repos

  - https://pypi.org/project/grscheller.circular-array/
  - https://github.com/grscheller/circular-array

- Fix various out-of-date docstrings

PyPI 0.12.3 - 2024-01-20
~~~~~~~~~~~~~~~~~~~~~~~~

- cutting next PyPI release from development (main)

  - if experiment works, will drop release branch
  - will not include ``docs/``
  - will not include ``.gitignore`` and ``.github/``
  - will include ``tests/``
  - made pytest >= 7.4 an optional test dependency

PyPI 0.12.2 - 2024-01-17
~~~~~~~~~~~~~~~~~~~~~~~~

- fixed Stack reverse() method

  - should have caught this when I fixed FStack on last PyPI release
  - more Stack tests

PyPI 0.12.1 - 2024-01-15
~~~~~~~~~~~~~~~~~~~~~~~~

- BUG FIX: FStack reverse() method
- added more tests

PyPI 0.12.0 - 2024-01-14
~~~~~~~~~~~~~~~~~~~~~~~~

- Considerable future-proofing for first real Beta release

Version 0.11.3.4 - Devel environment only
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Finally decided to make next PyPI release Beta

- Package structure mature and not subject to change beyond additions
- Will endeavor to keep top level & core module names the same
- API changes will be deprecated before removed

PyPI 0.11.0 - 2023-12-20
~~~~~~~~~~~~~~~~~~~~~~~~

- A lot of work done on class CLArray

  - probably will change its name before the next PyPI Release
  - perhaps to "ProcessArray" or "PArray"

- Keeping this release an Alpha version

  - mostly for the freedom to rename and restructure the package

Version 0.10.17.0+ - 2023-12-17 (Devel environment only)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Second release candidate (0.11.0-RC2). Probably will
become next PyPI release.

- main now development branch, release will be release branch
- decided to drop it back to Alpha

  - making datastructures a Beta release was premature
  - classifier "Development Status :: 3 - Alpha"

- will cut next PyPI release with Flit from release branch
- will need to regenerate docs on release & move to main
- things to add in main before next release

  - will not make ``Maybe`` or ``Nothing`` a singleton
  - last touched ``CLArray`` refactor
  - improve ``CLArray`` test coverage

- Things for future PYPI releases

  - inherit ``FTuple`` from ``Tuple`` (use ``__new__``) for performance boost
  - hold off using ``__slots__`` until I understand them better

Version 0.10.14.2 - 2023-12-11 (Devel environment only)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

First release candidate (0.11.0-RC1). Unlikely this will be
the next PyPI release.

- will cut next PyPI release with Flit from main branch
- removed docs directory before merge (docs/ will be main only)
- things to add in main before next release

  - make Maybe Nothing a singleton (use ``__new__``)
  - derive FTuple from Tuple (use ``__new__``) for performance boost
  - simplify CLArray to use a Queue instead of CircularArray & iterator
  - start using ``__slots__`` for performance boost to data structures

    - efficiency trumps extensibility
    - prevents client code adding arbitrary attributes & methods
    - smaller size & quicker method/attribute lookups
    - big difference when dealing with huge number of data structures

Version 0.10.14.0 - 2023-12-09 (Devel environment only)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Finished massive renaming & repackaging effort

- to help with future growth in future
- name choices more self-documenting
- top level modules

  - array

    - ``CLArray``

  - queue

    - ``FIFOQueue`` (formerly ``SQueue``)
    - ``LIFOQueue`` (LIFO version of above)
    - ``DoubleQueue`` (formerly ``DQueue``)

  - stack

    - ``Stack`` (formerly ``PStack``)
    - ``FStack``

  - tuple-like

    - ``FTuple``

Version 0.10.11.0 - 2023-11-27 (Devel environment only)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Created new datastructures class ``CLArray``. Made package
overall more "atomic".

- more imperative version of ``FCLArray``

  - has an iterator to swap None values instead of a default value

    - when iterator is exhausted, will swap in ``()`` for ``None``

  - no ``flatMap`` type methods
  - ``map`` method mutates ``self``
  - can be resized
  - returns false when ``CLArray`` contains no non-``()`` elements

- TODO: does not yet handle StopIteration events properly

Version 0.10.10.0 - 2023-11-26 (Devel environment only)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

More or less finalized ``FCLArray`` API.

- finished overriding default ``flatMap``, ``mergeMap`` & ``exhaustMap`` from FP
- need ``mergeMap`` & ``exhaustMap`` versions of unit tests
- found this data structure very interesting

  - hopefully find a use for it

- considering a simpler ``CLArray`` version

Version 0.10.8.0 - 2023-11-18 (Devel environment only)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Bumping requires-python = ">=3.11" in pyproject.toml

  - Currently developing & testing on Python 3.11.5
  - 0.10.7.X will be used on the GitHub pypy3 branch

    - Pypy3 (7.3.13) using Python (3.10.13)
    - tests pass but are 4X slower
    - LSP almost useless due to more primitive typing module

Version 0.10.7.0 - 2023-11-18 (Devel environment only)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Overhauled ``__repr__`` & ``__str__`` methods for all classes

  - tests that ``ds == eval(repr(ds))`` for all data structures ``ds`` in package

- CLArray API is in a state of flux

  - no longer stores ``None`` as a value
  - ``__add__`` concatenates, no longer component adds
  - maybe allow zero length ``CLArrays``?

    - would make it a monoid and not just a semigroup
    - make an immutable version too?

- Updated markdown overview documentation

Version 0.10.1.0 - 2023-11-11 (Devel environment only)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Devel environment only.

- Removed ``flatMap`` methods from stateful objects

  - ``FLArray``, ``DQueue``, ``SQueue``, ``PStack``
  - kept the ``map`` method for each

- some restructuring so package will scale better in the future

PyPI 0.9.1 - 2023-11-09
~~~~~~~~~~~~~~~~~~~~~~~

- First Beta release of grscheller.datastructures on PyPI
- Infrastructure stable
- Existing datastructures only should need API additions
- Type annotations working extremely well
- Using Pdoc3 to generate documentation on GitHub

  - see https://grscheller.github.io/datastructures/

- All iterators conform to Python language "iterator protocol"
- Improved docstrings
- Future directions:

  - Develop some "typed" containers
  - Add sequence & transverse methods to functional subpackage classes
  - Monad transformers???
  - Need to use this package in other projects to gain insight

Version 0.8.4.0 - 2023-11-03 (Devel environment only)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Devel environment only.

- new data structure ``FTuple`` added

  - wrapped tuple with a FP interface
  - initial minimal viable product

Version 0.8.3.0 - 2023-11-02 (Devel environment only)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Devel environment only.

- major API breaking change

  - now two versions of ``Stack`` class

    - ``PStack`` (stateful) with ``push``, ``pop``, ``peak`` methods
    - ``FStack`` (immutable) with ``cons``, ``tail``, ``head`` methods

  - ``FLarray`` renamed ``FLArray``

- tests now work

Version 0.8.0.0 - 2023-10-28 (Devel environment only)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Devel environment only.

- API breaking changes

  - did not find everything returning self upon mutation

- Efforts for future directions

  - decided to use pdoc3 over sphinx to generate API documentation
  - need to resolve tension of package being Pythonic and Functional

PyPI 0.7.5.0 - 2023-10-26
~~~~~~~~~~~~~~~~~~~~~~~~~

- moved pytest test suite to root of the repo

  - src/grscheller/datastructures/tests -> tests/
  - seems to be the canonical location of a test suite

- instructions to run test suite in ``tests/__init__.py``

Version 0.7.4.0 - 2023-10-25 (Devel environment only)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Devel environment only.

- More mature
- More Pythonic
- Major API changes
- Still tagging it an Alpha release

Version 0.7.0.0 - 2023-10-16 (Devel environment only)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Updated README.md file.

- foreshadowing making a distinction between

  - objects "sharing" their data -> FP methods return copies
  - objects "contain" their data -> FP methods mutate object

Version 0.6.9.0 - 2023-10-09 (Devel environment only)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- renamed core module to iterlib module

  - library just contained functions for manipulating iterators
  - TODO: use ``mergeIters`` as a guide for an iterator "zip" function

- class Stack better in alignment with:

  - Python lists

    - more natural for ``Stack`` to iterate backwards starting from head
    - removed Stack's ``__getitem__`` method
    - both pop and push/append from end

PyPI 0.2.2.2 - 2023-09-04
~~~~~~~~~~~~~~~~~~~~~~~~~

- decided base package should have no dependencies other than

  - Python version (>=2.10 due to use of Python match statement)
  - Python standard libraries

- made pytest an optional [test] dependency
- added src/ as a top level directory as per

  - https://packaging.python.org/en/latest/tutorials/packaging-projects/
  - could not do the same for tests/ if end users are to have access

PyPI 0.2.1.0 - 2023-09-03
~~~~~~~~~~~~~~~~~~~~~~~~~

- first Version uploaded to PyPI
- https://pypi.org/project/grscheller.datastructures/
- Install from PyPI

  - ``$ pip install grscheller.datastructures==0.2.1.0``
  - ``$ pip install grscheller.datastructures # for top level version``

- Install from GitHub

  - ``$ pip install git+https://github.com/grscheller/datastructures@v0.2.1.0``

- pytest made a dependency

  - useful & less confusing to developers and end users

    - good for systems I have not tested on
    - prevents another pytest from being picked up from shell ``$PATH``

      - using a different python version
      - giving "package not found" errors

    - for CI/CD pipelines requiring unit testing

Version 0.2.0.2 - 2023-08-29 (GitHub only)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- First version able to be installed from GitHub with pip
- ``$ pip install git+https://github.com/grscheller/datastructures@v0.2.0.2``

Version 0.1.1.0 - 2023-08-27 (Devel environment only)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- grscheller.datastructures moved to its own GitHub repo
- https://github.com/grscheller/datastructures

  - GitHub and PyPI user names just a happy coincidence

Version 0.1.0.0 - 2023-08-27 (Devel environment only)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Initial version.

- Package implementing data structures which do not throw exceptions
- Did not push to PyPI until version 0.2.1.0
- Initial Python grscheller.datastructures for 0.1.0.0 commit:

  - ``dqueue`` implements a double sided queue ``class Dqueue``
  - ``stack`` implements a LIFO stack ``class Stack``
