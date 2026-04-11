---
id: 019d7d9c-c96e-77ab-bb1e-e9eaf89b5359
references: []
---

# Package `__init__.py` files (Python 3+)

## What they are

`__init__.py` is a regular file whose **name** is fixed: it must be called exactly `__init__.py` and live inside a directory that Python treats as importable (on `PYTHONPATH`, in an installed distribution, etc.).

That directory is then a **regular package**. Python loads `__init__.py` as the implementation of the **package module**—the object bound to the name you use in `import` (for example `mypkg` when you `import mypkg`).

This is separate from **namespace packages** (PEP 420): in modern Python 3, a directory *without* `__init__.py` can still participate in imports as part of a namespace package, where multiple directories on disk share one logical package name. If the directory **has** `__init__.py`, you get a regular package with explicit initializer code instead.

## What their role is

1. **Define the package module** — Whatever you put in `__init__.py` becomes the body of `mypkg`: attributes, docstring, and behavior on import.

2. **Run once per process** — The first time something causes that package to be loaded, `__init__.py` executes (subject to normal import caching). Later imports reuse the same module object.

3. **Optional API surface** — You can keep `__init__.py` nearly empty and expose only submodules (`import mypkg.utils`), or you can use it to define a **stable public API** (re-exports, version string, `__all__`) so callers need not know your internal module layout.

4. **Documentation** — A module docstring at the top of `__init__.py` is the natural place to describe the whole package; it shows up in `help(mypkg)` and many IDEs.

5. **Not for heavy startup work** — Best practice in modern codebases is to avoid expensive or surprising side effects at import time (network, lots of disk I/O, importing every submodule eagerly). Prefer lazy imports or explicit initialization functions when needed.

## How they can be used

**Minimal marker** — An empty `__init__.py` (or a short comment) is enough to make a clear regular package and keep behavior predictable.

**Docstring only** — Document the package; no re-exports.

**Version and exports** — Common patterns:

- `__version__ = "1.0.0"` so code can read `mypkg.__version__`.
- `__all__ = ["foo", "bar"]` to document and constrain `from mypkg import *` (discouraged in application code, still used in some libraries).

**Re-export a public API** — Import implementation details from submodules and expose names at the top level:

```python
"""Public surface for mypkg."""

from .core import useful_function
from .types import UsefulClass

__all__ = ["useful_function", "UsefulClass"]
```

Callers can then `from mypkg import useful_function` instead of reaching into `mypkg.core`.

**Subpackages** — Nested directories can each have their own `__init__.py`; each level is its own package with the same kinds of choices (minimal vs curated API).

**When you might omit them** — If you intentionally want a **namespace package** (splitting one logical name across multiple directories, or certain plugin layouts), you rely on PEP 420 rules and typically do **not** add `__init__.py` to those portions. For a normal library or app package with a single tree and a clear entry point, a regular package with `__init__.py` remains the usual choice.
