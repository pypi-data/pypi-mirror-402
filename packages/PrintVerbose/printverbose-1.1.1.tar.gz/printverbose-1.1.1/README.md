# PrintVerbose

A small logging helper with colored output and traceback dumping.

Dependencies:
- colorama (BSD License)
```bash
pip install colorama
```

Install:
```bash
pip install printverbose
```

Usage:
```python
from PrintVerbose import get_logger, write_traceback_to_file

log = get_logger("app")
log.info("Hello")

try:
   oneplusone = 1 + 1
except:
   write_traceback_to_file() # works only inside a except block
   log.critical("Error doing math!")
```
# Changelog

## [1.1.1] - 1/20/2026
### Fixed
- Fixed minor spelling mistake in README.md

## [1.1.0] - 1/20/2026
### Added
- Error when using print_traceback_to_file() outside of an except block.
- Added changelog



Full changelog in CHANGELOG.md
