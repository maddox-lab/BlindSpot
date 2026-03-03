import os
import csv
from pathlib import Path

from .functions.BlindSpot_unblindingapp import run_unblinder


def make_blinding_key(csv_path, rows):
    # rows are tuples: (blind_name, original_name, original_full_path)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Old file name", "New file name", "Old path"])
        for blind_name, original_name, original_path in rows:
            # Keep your existing header names, but write values consistently:
            # Old file name = original name, New file name = blind name, Old path = original full path
            w.writerow([original_name, blind_name, original_path])


def test_unblinder(tmp_path, monkeypatch):
    monkeypatch.setattr(os, "fsync", lambda x: None)

    blind_file_name = "a1b2c3d4.nd2"
    original_file_name = "experiment1.nd2"
    content = "This is a test file for unblinding."

    (tmp_path / blind_file_name).write_text(content, encoding="utf-8")

    key_path = tmp_path / "unblinding_key.csv"
    make_blinding_key(
        key_path,
        [(blind_file_name, original_file_name, str(tmp_path / original_file_name))],
    )

    result = run_unblinder(
        base_path=tmp_path,
        key_csv_path=key_path,
        restore_folder=tmp_path,
        overwrite=False,
        progress=None,
        total=None,
    )

    restored = tmp_path / original_file_name

    assert isinstance(result, dict)
    assert result["restored"] == 1
    assert result["skipped"] == 0
    assert result["errors"] == 0
    assert result["total"] == 1

    assert restored.exists()
    assert restored.read_text(encoding="utf-8") == content
    assert not (tmp_path / blind_file_name).exists()


def test_unblind_multi(tmp_path, monkeypatch):
    monkeypatch.setattr(os, "fsync", lambda x: None)

    num_files = 1000
    rows = []

    for i in range(num_files):
        blind_name = f"blind_{i}.nd2"
        original_name = f"original_{i}.nd2"
        content = f"This is the data of file {i}."
        (tmp_path / blind_name).write_text(content, encoding="utf-8")
        rows.append((blind_name, original_name, str(tmp_path / original_name)))

    key_csv = tmp_path / "Blinding_key.csv"
    make_blinding_key(key_csv, rows)

    result = run_unblinder(
        base_path=tmp_path,
        key_csv_path=key_csv,
        restore_folder=tmp_path,
        overwrite=False,
        progress=None,
        total=None,
    )

    assert result["restored"] == num_files
    assert result["skipped"] == 0
    assert result["errors"] == 0
    assert result["total"] == num_files

    for i in range(num_files):
        restored_file = tmp_path / f"original_{i}.nd2"
        assert restored_file.exists()
        assert restored_file.read_text(encoding="utf-8") == f"This is the data of file {i}."
        assert not (tmp_path / f"blind_{i}.nd2").exists()


def test_unblind_overwrite(tmp_path, monkeypatch):
    monkeypatch.setattr(os, "fsync", lambda x: None)

    blind_name = "blind_file.nd2"
    original_name = "original_file.nd2"
    content_blind = "This is the blinded file."
    content_original = "This is the original file."

    (tmp_path / blind_name).write_text(content_blind, encoding="utf-8")
    (tmp_path / original_name).write_text(content_original, encoding="utf-8")

    key_csv = tmp_path / "Blinding_key.csv"
    make_blinding_key(key_csv, [(blind_name, original_name, str(tmp_path / original_name))])

    result = run_unblinder(
        base_path=tmp_path,
        key_csv_path=key_csv,
        restore_folder=tmp_path,
        overwrite=True,
        progress=None,
        total=None,
    )

    assert result["restored"] == 1
    assert result["skipped"] == 0
    assert result["errors"] == 0
    assert result["total"] == 1

    # overwrite=True should replace original content with blinded content
    assert (tmp_path / original_name).exists()
    assert (tmp_path / original_name).read_text(encoding="utf-8") == content_blind
    # blinded file should be gone because we moved it into place
    assert not (tmp_path / blind_name).exists()


def test_unblind_skip_existing(tmp_path, monkeypatch):
    monkeypatch.setattr(os, "fsync", lambda x: None)

    blind_name = "blind_file.nd2"
    original_name = "original_file.nd2"
    content_blind = "This is the blinded file."
    content_original = "This is the original file."

    (tmp_path / blind_name).write_text(content_blind, encoding="utf-8")
    (tmp_path / original_name).write_text(content_original, encoding="utf-8")

    key_csv = tmp_path / "Blinding_key.csv"
    make_blinding_key(key_csv, [(blind_name, original_name, str(tmp_path / original_name))])

    result = run_unblinder(
        base_path=tmp_path,
        key_csv_path=key_csv,
        restore_folder=tmp_path,
        overwrite=False,
        progress=None,
        total=None,
    )

    assert result["restored"] == 0
    assert result["skipped"] == 1
    assert result["errors"] == 0
    assert result["total"] == 1

    # original remains unchanged; blinded remains because we skipped
    assert (tmp_path / original_name).exists()
    assert (tmp_path / original_name).read_text(encoding="utf-8") == content_original
    assert (tmp_path / blind_name).exists()
    assert (tmp_path / blind_name).read_text(encoding="utf-8") == content_blind


def test_unblind_no_overwrite(tmp_path, monkeypatch):
    """
    Same behavior as skip_existing, but with different original content.
    """
    monkeypatch.setattr(os, "fsync", lambda x: None)

    blind_name = "blind_file.nd2"
    original_name = "original_file.nd2"
    content_blind = "This is the blinded file."
    content_original = "existing original file."

    (tmp_path / blind_name).write_text(content_blind, encoding="utf-8")
    (tmp_path / original_name).write_text(content_original, encoding="utf-8")

    key_csv = tmp_path / "Blinding_key.csv"
    make_blinding_key(key_csv, [(blind_name, original_name, str(tmp_path / original_name))])

    result = run_unblinder(
        base_path=tmp_path,
        key_csv_path=key_csv,
        restore_folder=tmp_path,
        overwrite=False,
        progress=None,
        total=None,
    )

    assert result["restored"] == 0
    assert result["skipped"] == 1
    assert result["errors"] == 0
    assert result["total"] == 1

    # unchanged original; blinded still present
    assert (tmp_path / original_name).exists()
    assert (tmp_path / original_name).read_text(encoding="utf-8") == content_original
    assert (tmp_path / blind_name).exists()
    assert (tmp_path / blind_name).read_text(encoding="utf-8") == content_blind


def test_unblind_logging(tmp_path, monkeypatch):
    monkeypatch.setattr(os, "fsync", lambda x: None)

    blind_name = "blind_file.nd2"
    original_name = "original_file.nd2"
    content_blind = "This is the blinded file."

    (tmp_path / blind_name).write_text(content_blind, encoding="utf-8")

    key_csv = tmp_path / "Blinding_key.csv"
    make_blinding_key(key_csv, [(blind_name, original_name, str(tmp_path / original_name))])

    _ = run_unblinder(
        base_path=tmp_path,
        key_csv_path=key_csv,
        restore_folder=tmp_path,
        overwrite=False,
        progress=None,
        total=None,
    )

    assert (tmp_path / "_unblinding_log.csv").exists()