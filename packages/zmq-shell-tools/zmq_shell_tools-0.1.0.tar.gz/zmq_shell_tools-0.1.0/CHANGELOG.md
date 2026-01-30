# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and versions numbers follow the idea of Attention Versioning:
Basically, it looks like the well-known [Semantic Versioning (SemVer)](https://semver.org/) and works like the intuitive [Effort Versioning (EffVer)](https://jacobtomlinson.dev/effver/) but with attention instead of effort being the measure for bumping the `Macro.Meso.Micro` scheme.
Increasing the individual parts means something like this:

- `Macro`: you should pay attention and care to this patch, as there are big changes or exciting features coming with it,
- `Meso`: you should have a look as you might need to adapt minor things or be getting some new interesting features,
- `Micro`: no need to pay attention.



## 0.1.0 - 2026-01-22

### Added

- Add commands for PUSH and PULL sockets
- Add `ruff`, `ty`, `prek`, `coverage`, `pytest` and `git-cliff` as development dependencies alongside respective configuration
- Add tests with full coverage
- Add version option
- Add Python project setup with files `pyproject.toml`, `README.md`, `LICENSE` and `CHANGELOG.md`

