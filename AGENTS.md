# AI Agent Playbook

Audience: AI coding agents working in this repo.

## Ground rules

- Markdown: wrap near ~120 chars.
- Keep [README.md](README.md) user-only.
- KISS: default to minimal changes; avoid optional parameters/configs or extra result objects unless explicitly requested.
- Visibility first: new modules default to private (`_`); keep constants private unless used outside the module.
- Do not invent new public APIs or config fields unless explicitly requested.
- For all Python commands, use a virtualenv:
  `python -m venv .venv && source .venv/bin/activate && pip install -r requirements-dev.txt`.
- Respect [doc/python-test-structure-guidelines.md](doc/python-test-structure-guidelines.md).
- Respect [doc/visibility.md](doc/visibility.md).
- Disabling linters via comments is a last resort; fix first and only suppress with explicit approval.

## Python guidelines

- Prefer explicit datatypes and clear module boundaries.
- Default to private visibility and only widen visibility when there is actual outside usage.
- Test packages must mirror `src` packages and module names.
- Test method names must mirror source method names per the test structure guidelines.

## Linting and tests

- Lint: `source .venv/bin/activate && ./scripts/lint.sh`
- Tests: `source .venv/bin/activate && pytest --cov=src --cov-report=term-missing`
