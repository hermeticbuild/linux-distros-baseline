# Linux Distributions Baseline

Small dataset for Linux distro compatibility baselines.

Each CSV row describes one distro release or runtime with:

- libc family and baseline version (`glibc`/GNU libc or `musl`)
- C++ standard library family and baseline version (`libstdc++` or `libc++`)
- Linux UAPI/kernel headers baseline, reduced to a release-level floor
- optional alternate kernel/header track
- notes and source URL used to justify the row

`cxx_stdlib_baseline` records the upstream package version, not the distro
package release suffix. For example, `12.2.0-14+deb12u1` is recorded as
`12.2.0`. Snapshot-style upstream versions, such as Ubuntu `10-20200411` or
SUSE `13.2.1+git8285`, are kept. Use `not packaged` when the distro release
does not provide that C++ standard library package.

Generated C++ standard library constraints use the same coarse version style as
libc constraints. Versions with a major/minor pair become
`@llvm//constraints/cxxstdlib:<flavor>.<major>.<minor>`. GCC snapshot versions
without a minor component use the leading major, for example `12-20220319`
becomes `@llvm//constraints/cxxstdlib:libstdcxx.12`.

The goal is to help choose or generate build constraints for Linux sysroots,
without encoding distro-specific target names in the data.

## Generate constraints

Run:

```sh
./generate_constraints.py > constraints.bzl
```

The generator reads all `*.csv` files and emits Bazel-style constants:

```python
# notes: Too new for RHEL 8 or Ubuntu 20.04 if GLIBC_2.32+ symbols leak.
# source_url: https://documentation.ubuntu.com/release-notes/22.04/
# cxx_stdlib: libstdc++ 12-20220319
# cxx_stdlib_source_url: https://archive.ubuntu.com/ubuntu/dists/jammy/main/binary-amd64/Packages.gz
UBUNTU_2204_CONSTRAINTS = [
    "@llvm//constraints/libc:gnu.2.35",
    "@llvm//constraints/cxxstdlib:libstdcxx.12",
    "@llvm//constraints/kernel/linux:5.15",
]
```

Rows with snapshot-specific or non-versioned baselines are skipped with a
comment.
