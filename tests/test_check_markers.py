import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from check_markers import find_markers, scan_paths  # noqa: E402

# Built at runtime so this file never holds a literal the gate blocks (it is scanned on commit).
MARK = "acme" + "corp"
PUBLIC_IP = ".".join(["8"] * 4)
PRIVATE_IP = ".".join(["10", "1", "1", "1"])
REAL_MAC = ":".join(["aa", "bb", "cc", "dd", "ee", "ff"])


def kinds(findings):
    return [f["kind"] for f in findings]


def test_marker_case_insensitive():
    assert kinds(find_markers("Hello " + MARK.upper(), "x", [MARK])) == ["marker"]


def test_doc_ip_allowed():
    assert find_markers("ip 192.0.2.1 198.51.100.7 203.0.113.9", "x", []) == []


def test_real_ip_blocked():
    assert kinds(find_markers("ip " + PUBLIC_IP, "x", [])) == ["ip"]


def test_private_ip_blocked():
    assert kinds(find_markers("ip " + PRIVATE_IP, "x", [])) == ["ip"]


def test_mac_blocked():
    assert kinds(find_markers("mac " + REAL_MAC, "x", [])) == ["mac"]


def test_marker_in_path(tmp_path):
    f = tmp_path / (MARK + "-anchors.md")
    f.write_text("")
    assert "marker" in kinds(scan_paths([f], [MARK]))


def test_binary_file_skipped(tmp_path):
    f = tmp_path / "blob.bin"
    f.write_bytes(b"\xff\xfe\x00" + MARK.encode())
    assert scan_paths([f], ["nomatch"]) == []


def test_cli_exit_codes(tmp_path):
    (tmp_path / "clean.md").write_text("ip 192.0.2.1\n")
    (tmp_path / "dirty.md").write_text("ip " + PUBLIC_IP + "\n")
    cli = [sys.executable, str(ROOT / "scripts" / "check_markers.py")]
    # Relative names from inside tmp_path, as the hook passes them: the absolute tmp path holds the username.
    run = lambda name: subprocess.run(cli + [name], capture_output=True, cwd=tmp_path).returncode  # noqa: E731
    assert run("clean.md") == 0
    assert run("dirty.md") == 1


def test_missing_path_flagged(tmp_path):
    from check_markers import scan_paths as sp
    assert kinds(sp([tmp_path / "nope.md"], [])) == ["missing"]


def test_latin1_text_scanned(tmp_path):
    f = tmp_path / "old.cfg"
    f.write_bytes(b"ip " + PUBLIC_IP.encode() + b" caf\xe9\n")
    assert kinds(scan_paths([f], [])) == ["ip"]


def test_scan_blobs_name_with_space():
    from check_markers import scan_blobs
    assert kinds(scan_blobs([("lab notes.md", b"ip " + PUBLIC_IP.encode())], [])) == ["ip"]
