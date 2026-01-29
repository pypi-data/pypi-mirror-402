===================================
Change log for risclog.cryptography
===================================


1.2 (2026-01-19)
================

- Fixed type annotations for ``encrypt()`` and ``decrypt()`` methods to accurately reflect dual-mode behavior: return ```Coroutine``` when called from within a running event loop, or direct result when called outside an event loop
- Added comprehensive docstrings to ``encrypt()`` and ``decrypt()`` public methods explaining the dual-mode behavior and coroutine requirements
- Removed unnecessary ``# type: ignore`` comments from ``encrypt()`` and ``decrypt()`` methods


1.1 (2024-09-13)
================

- added default salt. Can be used with a single instance


1.0 (2024-09-11)
================

* initial release
