# Changes

## 2.1.1 (2026-01-19)

- Build wheels for Python 3.14.
- Drop testing for Debian Bullseye, which has reached end-of-life.
- Don't install C sources in site-packages.

## 2.1.0 (2025-05-06)

- Remove the fallback code to import the Python implementation if importing the
  C implementation fails. It would be a bug and a performance regression if the
  import ever failed.
- Modernize the test suite and port most of the tests to pytest.
- Use ruff to automatically format all of the code.
- Build binary wheels for Linux aarch64.

## 2.0.0 (2024-12-19)

- This is the first release after forking from ligo-segments. It should be a
  drop-in replacement: just replace `from ligo import segments` with
  `import igwn_segemnts as segments`.
- Drop support for Python 2.
- Fix build on Python 3.12 and 3.13.
- Add builds for Windows.
