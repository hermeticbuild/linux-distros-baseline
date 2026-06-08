#!/usr/bin/env python3
"""Generate Bazel constraint lists from the distro CSV files."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


FIELDS = (
    "distro",
    "release",
    "libc",
    "libc_baseline",
    "cxx_stdlib",
    "cxx_stdlib_baseline",
    "cxx_stdlib_source_url",
    "linux_uapi_headers_baseline",
    "notes",
    "source_url",
)


def name_part(value: str) -> str:
    value = value.replace("/", " ")
    value = value.replace("&", " and ")
    value = re.sub(r"\bLTS\b", "", value, flags=re.IGNORECASE)
    value = re.sub(r"(?<=\d)\.(?=\d)", "", value)
    value = re.sub(r"[^A-Za-z0-9]+", "_", value)
    return re.sub(r"_+", "_", value).strip("_")


def constant_name(distro: str, release: str) -> str:
    raw = "_".join(part for part in (name_part(distro), name_part(release)) if part)
    return f"{raw.upper()}_CONSTRAINTS"


def major_minor(version: str) -> str | None:
    match = re.search(r"\d+\.\d+", version)
    if not match:
        return None
    return match.group(0)


def major_minor_or_major(version: str) -> str | None:
    return major_minor(version) or leading_major(version)


def leading_major(version: str) -> str | None:
    match = re.search(r"\d+", version)
    if not match:
        return None
    return match.group(0)


def libc_constraint(libc: str, baseline: str) -> str | None:
    libc_lower = libc.lower()
    if libc_lower == "musl":
        return "@llvm//constraints/libc:musl"
    if "glibc" in libc_lower or "eglibc" in libc_lower:
        version = major_minor(baseline)
        if version:
            return f"@llvm//constraints/libc:gnu.{version}"
    return None


def cxx_stdlib_constraint(cxx_stdlib: str, baseline: str) -> str | None:
    cxx_stdlib_lower = cxx_stdlib.lower()
    if cxx_stdlib_lower == "libc++":
        flavor = "libcxx"
    elif cxx_stdlib_lower == "libstdc++":
        flavor = "libstdcxx"
    else:
        return None

    version = major_minor_or_major(baseline)
    if version:
        return f"@llvm//constraints/cxxstdlib:{flavor}.{version}"
    return None


def kernel_constraint(version: str) -> str | None:
    version = major_minor(version)
    if not version:
        return None
    return f"@llvm//constraints/kernel/linux:{version}"


def comment(label: str, value: str) -> str:
    return f"# {label}: {value}"


def read_rows(csv_dir: Path) -> list[tuple[Path, dict[str, str]]]:
    rows: list[tuple[Path, dict[str, str]]] = []
    for path in sorted(csv_dir.glob("*.csv")):
        with path.open(newline="") as file:
            reader = csv.DictReader(file)
            missing = [field for field in FIELDS if field not in (reader.fieldnames or [])]
            if missing:
                raise SystemExit(f"{path}: missing columns: {', '.join(missing)}")
            for row in reader:
                rows.append((path, row))
    return rows


def generate(csv_dir: Path) -> str:
    lines = [
        "# Generated from linux sysroot CSV data.",
        "# Run: ./generate_constraints.py > constraints.bzl",
        "",
    ]
    seen: set[str] = set()

    for path, row in read_rows(csv_dir):
        name = constant_name(row["distro"], row["release"])
        if name in seen:
            raise SystemExit(f"{path}: duplicate generated constant name: {name}")
        seen.add(name)

        libc = libc_constraint(row["libc"], row["libc_baseline"])
        cxx_stdlib = cxx_stdlib_constraint(
            row["cxx_stdlib"],
            row["cxx_stdlib_baseline"],
        )
        kernel = kernel_constraint(row["linux_uapi_headers_baseline"])
        if not libc or not cxx_stdlib or not kernel:
            lines.append(
                f"# Skipped {name}: non-versioned libc/cxxstdlib/kernel baseline "
                f"({row['libc_baseline']!r}, {row['cxx_stdlib_baseline']!r}, "
                f"{row['linux_uapi_headers_baseline']!r})"
            )
            continue

        lines.extend(
            [
                comment("notes", row["notes"]),
                comment("source_url", row["source_url"]),
                comment(
                    "cxx_stdlib",
                    f"{row['cxx_stdlib']} {row['cxx_stdlib_baseline']}",
                ),
                comment("cxx_stdlib_source_url", row["cxx_stdlib_source_url"]),
                f"{name} = [",
                f'    "{libc}",',
                f'    "{cxx_stdlib}",',
                f'    "{kernel}",',
                "]",
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate Bazel constraint lists from distro CSV files."
    )
    parser.add_argument(
        "csv_dir",
        nargs="?",
        default=".",
        type=Path,
        help="Directory containing the CSV files. Defaults to current directory.",
    )
    args = parser.parse_args()
    print(generate(args.csv_dir), end="")


if __name__ == "__main__":
    main()
