# Experimental CPython 3.15t Linux wheels

A normal `pip install` from this repository selects the verified release wheel
for the recorded source snapshot on Linux x86_64, CPython 3.15t and glibc 2.39+.
pip performs downloading, dependency resolution and SHA256 validation.
No consumer SDK setup or extra build flag is required for this binary path.

The original PEP 517 backend and its build requirements are preserved. Changed
native/build sources, another ABI/platform, explicit configuration settings or
compiler overrides use that original source build. The JSON manifest records
the source commit, artifact hash and the checked delivery metadata. Source
builds retain their ordinary development-library prerequisites.

These are engineering dependency artifacts, not a StableKite release.

Embedded HIDAPI C source filenames are relative to the source root. This
avoids duplicating pip's absolute checkout path in the MSVC object directory
for named VCS requirements on Windows. Include directories, compiler/linker
settings, native HIDAPI sources and the Cython runtime remain unchanged.
The manifest records this build-path correction while retaining the original
Linux binary and its exact runtime source snapshot.
