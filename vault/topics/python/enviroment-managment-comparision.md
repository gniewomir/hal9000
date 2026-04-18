
# Python environment tooling — comparison

This note compares common ways to **isolate dependencies** and **pin versions** for Python projects. Tools fall into overlapping categories: *only virtualenvs*, *lockfiles + workflows*, *full installers* (Python + libs), and *version managers* (which Python binary you use).

## Quick orientation

| Tool | Primary job | Lockfile / pins | Installs Python? |
|------|-------------|-----------------|------------------|
| **venv** | Virtual environment (isolated `site-packages`) | No — you pair with `pip` + pins elsewhere | No |
| **virtualenv** | Same as venv, older/backport + extras | No | No |
| **pip-tools** | Compile pinned `requirements.txt` from `.in` files | Yes (`requirements.txt`) | No |
| **Poetry** | Project metadata, env, lock, publish | Yes (`poetry.lock`) | Optional (via `python` on PATH or plugin) |
| **Pipenv** | `Pipfile` workflow + env | Yes (`Pipfile.lock`) | No |
| **uv** | Fast resolver/installer, envs, can replace several tools | Yes (`uv.lock`) | Yes (optional `uv python install`) |
| **Hatch** | Env matrices, builds, tests, publishing | Via PEP 621 / lock strategies | Optional |
| **PDM** | PEP 621 project, env, lock | Yes (`pdm.lock`) | Optional |
| **Conda** / **Mamba** / **Micromamba** | Cross-language envs + binary packages | Yes (conda env export / explicit specs) | Yes (bundled or via installer) |
| **pyenv** / **asdf** | Switch Python versions per directory | No (not a project dep tool by itself) | Yes (sources/builds) |
| **pipx** | Install *CLI apps* in isolation | N/A for libraries | No |

---

## venv (stdlib)

**What it is:** Creates a directory with its own `python` and `pip`, so project packages do not touch the system site-packages.

**Pros**

- Built into Python 3 — no extra install for the venv *mechanism*.
- Simple mental model: activate → `pip install` → run.
- Universal; works everywhere Python runs.
- Fine-grained control when combined with hand-written or generated `requirements.txt`.

**Cons**

- No lockfile or dependency resolution — you manage pins (e.g. `pip-tools`, manual pins, or CI checks).
- Does not install Python versions; pair with **pyenv**, **asdf**, OS packages, or **uv python**.
- “Requirements drift” is common without discipline (unpinned or loosely pinned deps).

---

## Conda (and Mamba / Micromamba)

**What it is:** A package and environment manager oriented around **channels**; can install Python itself and **pre-built binaries** (including non-Python deps like MKL, CUDA stacks in some channels).

**Pros**

- Strong for **scientific / data** stacks where compiled libs matter.
- One tool can provide reproducible envs across platforms (with care for channel pins).
- **Mamba** / **Micromamba** are much faster solvers and lighter installs than classic `conda` alone.

**Cons**

- Heavier than venv + pip for pure-Python workflows.
- Channel and license policies need attention (defaults vs conda-forge, etc.).
- Not always aligned with “pure” PyPI + `pyproject.toml` workflows unless you bridge carefully.

---

## Poetry

**What it is:** Project-centric: `pyproject.toml` for metadata and dependencies, **`poetry.lock`** for reproducible installs, plus build and publish commands.

**Pros**

- Coherent story: metadata, lock, virtualenv, and packaging in one tool.
- Widely adopted in application and library projects.
- Good UX for many teams once conventions are set.

**Cons**

- Historical quirks vs strict PEP standards (improving over time; still worth reading current docs).
- Another abstraction to learn; CI must invoke `poetry install` (or export) consistently.
- Speed was a common complaint vs newer tools (less of an issue vs **uv** today if you combine tools).

---

## Pipenv

**What it is:** `Pipfile` / `Pipfile.lock`, integrates **pip** and **virtualenv** with a single CLI.

**Pros**

- Lockfile-first workflow predates wide `pyproject.toml` adoption.
- Familiar to teams already standardized on it.

**Cons**

- Slower maintenance and less momentum than Poetry, **uv**, or **pip-tools** in many communities.
- Duplicative with modern `pyproject.toml` + dedicated lockers for new projects.

---

## uv (Astral)

**What it is:** A very fast Rust-based **installer and resolver**; can manage virtualenvs, lock projects, and optionally install Python versions. Often discussed as a **pip** / **pip-tools** / parts of **Poetry**-style workflows accelerator.

**Pros**

- Extremely fast installs and resolution.
- Strong fit for teams wanting **lockfiles** and modern UX without conda’s weight.
- Can align with `pyproject.toml` workflows and interoperate with existing ecosystems.

**Cons**

- Newer than pip/venv — organizational policies may still standardize on older tools first.
- Rapid evolution: check current docs for exact feature parity with your prior tool.

---

## Hatch

**What it is:** Focus on **project automation**: multiple environments, test matrices, builds, and publishing — PEP 621 native.

**Pros**

- Excellent for **libraries** needing clean multi-version testing and standardized build hooks.
- Plays well with standard packaging metadata.

**Cons**

- More “framework” than “just an env”; steeper if you only wanted `venv` + `pip`.
- Overkill for a tiny script repo.

---

## Other widely used options

### pip-tools (`pip-compile` / `pip-sync`)

**Pros:** Minimal change from `requirements.in` → pinned `requirements.txt`; works with plain **venv**; battle-tested in ops-heavy setups.

**Cons:** Less project metadata than full Poetry/PDM; another moving part in CI.

### PDM

**Pros:** PEP 621-first, lockfile, fast, active development; good middle ground between minimalism and full IDE-style tooling.

**Cons:** Smaller share than Poetry in some enterprises; team has to agree on one standard.

### pyenv (and **asdf** with Python plugin)

**Pros:** Per-project **Python version** switching; pairs naturally with **venv** or **uv**.

**Cons:** Does not replace dependency locking; another layer to install and keep updated.

### pipx

**Pros:** Installs **CLI tools** (black, ruff, poetry) in isolated envs — avoids polluting project deps.

**Cons:** Not for declaring a library project’s runtime dependencies.

---

## Practical “how to choose”

- **Library author, multi-Python CI:** Consider **Hatch** or **tox**/**nox** + **venv**, with **uv** or **pip-tools** for speed/pins.
- **Application team, single stack, want one tool:** **Poetry**, **PDM**, or **uv** (depending on team taste and PEP alignment needs).
- **Data / science / compiled stack:** **conda-forge** + **mamba**/**micromamba** often wins.
- **Minimal / ops / Docker-first:** **venv** + **pip-tools** (or **uv**) keeps images simple.
- **Global CLI utilities:** **pipx**, not your project venv.

No single tool is “best” — overlap is large; **consistency inside a repo and in CI** matters more than picking the trendiest name.
