#!/usr/bin/env python3
"""Marker gate: block private strings and non-documentation IPs/MACs before they reach git history.

  check_markers.py [paths...]   scan path names + file contents (dirs recurse)
  check_markers.py --staged     scan staged content; NUL-separated names on stdin (the pre-commit hook)
  check_markers.py --stdin      scan text on stdin (e.g. `git log -p --all | check_markers.py --stdin`)

Markers come from private-markers.txt at the repo root (gitignored); without it only IPs/MACs are checked.
Exit 0 = clean, 1 = findings. Functions return lists of findings; only main() prints.
"""
from __future__ import annotations

import ipaddress
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Public repo: RFC 5737 doc ranges only, plus non-identifying loopback/multicast/mask space. RFC 1918 is blocked.
_ALLOWED_NETS = [ipaddress.ip_network(n) for n in (
    "192.0.2.0/24", "198.51.100.0/24", "203.0.113.0/24",
    "127.0.0.0/8", "224.0.0.0/4", "0.0.0.0/8", "255.0.0.0/8",
)]
_IPV4 = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?!\.?\d)")
_MAC = re.compile(r"(?<![0-9a-f:.-])(?:(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}|"
                  r"[0-9a-f]{4}\.[0-9a-f]{4}\.[0-9a-f]{4})(?![0-9a-f:.-])", re.IGNORECASE)
_ALLOWED_MAC_PREFIXES = ("00005e0053", "0180c20000", "01005e", "ffffffffffff", "000000000000")
_SKIP_DIRS = {".git", "__pycache__", ".claude"}


def load_markers(path: Path) -> list[str]:
    if not path.is_file():
        return []
    lines = (ln.strip() for ln in path.read_text(encoding="utf-8").splitlines())
    return [ln.lower() for ln in lines if ln and not ln.startswith("#")]


def _ip_ok(text: str) -> bool:
    try:
        addr = ipaddress.ip_address(text)
    except ValueError:
        return True  # octet > 255: not an address
    return any(addr in net for net in _ALLOWED_NETS)


def find_markers(text: str, where: str, markers: list[str]) -> list[dict]:
    out = []
    for n, line in enumerate(text.splitlines(), 1):
        low = line.lower()
        out += [{"where": where, "line": n, "kind": "marker", "match": m} for m in markers if m in low]
        out += [{"where": where, "line": n, "kind": "ip", "match": m.group()}
                for m in _IPV4.finditer(line) if not _ip_ok(m.group())]
        for m in _MAC.finditer(line):
            if not re.sub(r"[^0-9a-f]", "", m.group().lower()).startswith(_ALLOWED_MAC_PREFIXES):
                out.append({"where": where, "line": n, "kind": "mac", "match": m.group()})
    return out


def _decode(data: bytes) -> str | None:
    """None for true binaries (NUL byte); anything else is scanned, invalid UTF-8 replaced."""
    return None if b"\x00" in data else data.decode("utf-8", "replace")


def scan_blobs(items: list[tuple[str, bytes]], markers: list[str]) -> list[dict]:
    out = []
    for name, data in items:
        out += [{"where": name, "line": 0, "kind": "marker", "match": m} for m in markers if m in name.lower()]
        text = _decode(data)
        if text is not None:
            out += find_markers(text, name, markers)
    return out


def _files(paths: list[Path]) -> tuple[list[Path], list[Path]]:
    found, missing = [], []
    for p in paths:
        if p.is_dir():
            found += [f for f in sorted(p.rglob("*")) if f.is_file() and not _SKIP_DIRS & set(f.parts)]
        elif p.is_file():
            found.append(p)
        else:
            missing.append(p)
    return found, missing


def scan_paths(paths: list[Path], markers: list[str]) -> list[dict]:
    found, missing = _files(paths)
    out = [{"where": str(p), "line": 0, "kind": "missing", "match": "path not found"} for p in missing]
    return out + scan_blobs([(str(f), f.read_bytes()) for f in found], markers)


def staged_blobs(names: list[str]) -> list[tuple[str, bytes]]:
    """The staged (index) content of each path, not the working copy."""
    return [(n, subprocess.run(["git", "show", ":" + n], capture_output=True, check=True).stdout) for n in names]


def main(argv: list[str]) -> int:
    markers = load_markers(ROOT / "private-markers.txt")
    if argv[:1] == ["--stdin"]:
        findings = find_markers(sys.stdin.read(), "<stdin>", markers)
    elif argv[:1] == ["--staged"]:
        names = [n for n in sys.stdin.buffer.read().decode("utf-8", "replace").split("\0") if n]
        findings = scan_blobs(staged_blobs(names), markers)
    else:
        findings = scan_paths([Path(a) for a in argv], markers)
    for f in findings:
        print(f"{f['where']}:{f['line']}: {f['kind']} {f['match']}", file=sys.stderr)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
