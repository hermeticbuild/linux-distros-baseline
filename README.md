# Linux Distributions Baseline

Small dataset for Linux distro compatibility baselines.

Each CSV row describes one distro release or runtime with:

- libc family and baseline version (`glibc`/GNU libc or `musl`)
- Linux UAPI/kernel headers baseline, reduced to a release-level floor
- optional alternate kernel/header track
- notes and source URL used to justify the row

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
UBUNTU_2204_CONSTRAINTS = [
    "@llvm//constraints/libc:gnu.2.35",
    "@llvm//constraints/kernel/linux:5.15",
]
```

Rows with snapshot-specific or non-versioned baselines are skipped with a
comment.
