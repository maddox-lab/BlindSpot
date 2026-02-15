import os
import sys
from pathlib import Path
from unittest import result
from BlindSpot3_2 import run_blinder
import shutil


def test_blinder_moveBlind(tmp_path, monkeypatch):

    """
    Test the blinder function to ensure it correctly moves files to the blind directory and updates the log 


    """
    monkeypatch.setattr(os, "fsync", lambda fd: None)

    num_files = 1000

    for files in range(num_files):
        (tmp_path / f"file{files}.jpg").write_text("x", encoding="utf-8")

    progress_state = {"last_done": 0, "total": None}

    def progress_cb(last_done, total, msg):

        progress_state["last_done"] = last_done
        progress_state["total"] = total

    results = {}

    def finished(summary, mapping):

        results["summary"] = summary
        results["mapping"] = mapping

    run_blinder(
        base_path=tmp_path,
        extension=".jpg",
        move_to_blind=True,
        clone_og=False,
        include_subdirs=False,
        progress=progress_cb,
        finished= finished
    )

    assert "mapping" in results and isinstance(results["mapping"], dict) and len(results["mapping"]) == num_files

    blind_dir = tmp_path / "Blind Files"
    assert blind_dir.exists() and blind_dir.is_dir()
    assert len(list(blind_dir.glob("*.jpg"))) == num_files

    for old_name, new_name in results["mapping"].items():
        assert not (tmp_path / old_name).exists()
        assert (blind_dir / new_name).exists()

    assert progress_state["total"] == num_files
    assert len(list(tmp_path.glob("*.jpg"))) == 0
    assert progress_state["total"] == num_files and progress_state["last_done"] == num_files


def test_blinder_copyog(tmp_path, monkeypatch):

    """
    Test the blinder function to ensure it correctly copies files to the blind directory and retains the original files


    """

    monkeypatch.setattr(os, "fsync", lambda fd: None)

    num_files = 1000

    for files in range(num_files):
        (tmp_path / f"file{files}.png").write_text("x", encoding="utf-8")

    progress_state = {"last_done": 0, "total": None}

    def progress_cb(last_done, total, msg):

        progress_state["last_done"] = last_done
        progress_state["total"] = total

    results = {}

    def finished(summary, mapping):

        results["summary"] = summary
        results["mapping"] = mapping

    run_blinder(
        base_path=tmp_path,
        extension=".png",
        move_to_blind=False,
        clone_og=True,
        include_subdirs=False,
        progress=progress_cb,
        finished=finished
    )

    assert "mapping" in results and isinstance(results["mapping"], dict) and len(results["mapping"]) == num_files

    for old_name, new_name in results["mapping"].items():
        assert (tmp_path / new_name).exists()
        assert (tmp_path / old_name).exists()

    assert progress_state["total"] == num_files and progress_state["last_done"] == num_files
    assert len(list(tmp_path.glob("*.png"))) == 2000


def test_blinder_sub_off(tmp_path, monkeypatch):

    """
    Test the blinder function to ensure it correctly processes files without including subfolders

    """
    monkeypatch.setattr(os, "fsync", lambda fd: None)

    num_files = 500

    blind_dir = tmp_path / "Blind Files"
    blind_dir.mkdir(parents=True, exist_ok=True)

    for files in range(num_files):
        (blind_dir / f"blinded_file{files}.tif").write_text("x", encoding="utf-8")

    progress_state = {"last_done": 0, "total": None}

    def progress(last_done, total, msg):
        progress_state["last_done"] = last_done
        progress_state["total"] = total

    results = {}

    def finished(summary, mapping):


        results["summary"] = summary
        results["mapping"] = mapping

    run_blinder(
        base_path=tmp_path,
        extension=".tif",
        move_to_blind=False,
        clone_og=False,
        include_subdirs=False,
        progress=progress,
        finished=finished
    )

    assert "mapping" in results and isinstance(results["mapping"], dict) and len(results["mapping"]) == 0
    assert progress_state["total"] is None and progress_state["last_done"] == 0
    assert len(list(blind_dir.glob("*.tif"))) == num_files


def test_blinder_sub_on(tmp_path, monkeypatch):

    """
    Test the blinder function to ensure it correctly processes files in subfolders the option is selected

    """
    monkeypatch.setattr(os, "fsync", lambda fd: None)

    num_files = 500

    blind_dir = tmp_path / "Blind Files"
    blind_dir.mkdir(parents=True, exist_ok=True)

    sub_dir = tmp_path / "Subdir1"
    sub_dir.mkdir(parents=True, exist_ok=True)

    for files in range(num_files):
        (sub_dir / f"blinded_file{files}.tif").write_text("x", encoding="utf-8")

    progress_state = {"last_done": 0, "total": None}

    def progress(last_done, total, msg):

        progress_state["last_done"] = last_done
        progress_state["total"] = total

    results = {}

    def finished(summary, mapping):
        results["summary"] = summary
        results["mapping"] = mapping

    run_blinder(
        base_path=tmp_path,
        extension=".tif",
        move_to_blind=False,
        clone_og=False,
        include_subdirs=True,
        progress=progress,
        finished=finished
    )

    assert "mapping" in results and isinstance(results["mapping"], dict) and len(results["mapping"]) == num_files
    assert progress_state["total"] == num_files and progress_state["last_done"] == num_files
    assert len(list(blind_dir.glob("*.tif"))) == 0


def test_accuracy(tmp_path, monkeypatch):

    """
    Test the blinder function to ensure it correctly processes files and maintains data integrity 
    """
    monkeypatch.setattr(os, "fsync", lambda fd: None)

    num_files = 1000

    for files in range(num_files):
        (tmp_path / f"file{files}.jpg").write_text(f"this is file number {files}", encoding="utf-8")

    progress_state = {"last_done": 0, "total": None}

    def progress(last_done, total, msg):

        progress_state["last_done"] = last_done
        progress_state["total"] = total

    results = {}

    def finished(summary, mapping):


        results["summary"] = summary
        results["mapping"] = mapping

    run_blinder(
        base_path=tmp_path,
        extension=".jpg",
        move_to_blind=True,
        clone_og=False,
        include_subdirs=False,
        progress=progress,
        finished=finished
    )

    assert len(results["mapping"]) == num_files
    assert progress_state["total"] == num_files and progress_state["last_done"] == num_files

    for old_name, new_name in results["mapping"].items():
        with open(tmp_path / "Blind Files" / new_name, "r", encoding="utf-8") as f:
            content = f.read()

        idx = int(Path(old_name).stem.replace("file", ""))
        assert content == f"this is file number {idx}"
        assert len(results["mapping"]) == num_files
        assert new_name != old_name
        assert not (tmp_path / old_name).exists()
        assert (tmp_path / "Blind Files" / new_name).exists()
        assert old_name in results["mapping"] and results["mapping"][old_name] == new_name

    for old_name, new_name in results["mapping"].items():
        idx = int(Path(old_name).stem.replace("file", ""))
        content = (tmp_path / "Blind Files" / new_name).read_text()
        assert content == f"this is file number {idx}"
        assert len(content) > 0


def test_uniqueness(tmp_path, monkeypatch):

    """
    Test the blinder function to ensure it generates unique blinded filenames for each original file


    """

    monkeypatch.setattr(os, "fsync", lambda fd: None)

    num_files = 1000

    for files in range(num_files):
        (tmp_path / f"file{files}.jpg").write_text("x", encoding="utf-8")

    progress_state = {"last_done": 0, "total": None}

    def progress(last_done, total, msg):


        progress_state["last_done"] = last_done
        progress_state["total"] = total

    results = {}

    def finished(summary, mapping):
        results["summary"] = summary
        results["mapping"] = mapping

    run_blinder(
        base_path=tmp_path,
        extension=".jpg",
        move_to_blind=True,
        clone_og=False,
        include_subdirs=False,
        progress=progress,
        finished=finished
    )

    assert "mapping" in results and isinstance(results["mapping"], dict) and len(results["mapping"]) == num_files
    assert progress_state["total"] == num_files and progress_state["last_done"] == num_files
    assert len(set(results["mapping"].values())) == len(results["mapping"])


def test_mixed_files(tmp_path, monkeypatch):

    """
    Test the blinder function to ensure it correctly processes only the specified file extension and ignores others
    
    """
    monkeypatch.setattr(os, "fsync", lambda fd: None)

    num_files = 1000

    for files in range(num_files):
        (tmp_path / f"file{files}.jpg").write_text("x", encoding="utf-8")
        (tmp_path / f"file{files}.txt").write_text("x", encoding="utf-8")

    progress_state = {"last_done": 0, "total": None}

    def progress(last_done, total, msg):
        progress_state["last_done"] = last_done
        progress_state["total"] = total

    results = {}

    def finished(summary, mapping):


        results["summary"] = summary
        results["mapping"] = mapping

    run_blinder(
        base_path=tmp_path,
        extension=".jpg",
        move_to_blind=True,
        clone_og=False,
        include_subdirs=False,
        progress=progress,
        finished=finished
    )

    assert "mapping" in results and isinstance(results["mapping"], dict) and len(results["mapping"]) == num_files
    assert progress_state["total"] == num_files and progress_state["last_done"] == num_files

    blind_dir = tmp_path / "Blind Files"
    assert blind_dir.exists() and blind_dir.is_dir()
    assert len(list(blind_dir.glob("*.jpg"))) == num_files
    assert len(list(blind_dir.glob("*.txt"))) == 0

    assert len(list(tmp_path.glob("*.txt"))) == num_files
    assert len(list(tmp_path.glob("*.jpg"))) == 0


def test_nofile(tmp_path, monkeypatch):

    """
    Does not find any files to process and correctly handles the case when no files are found
    """
    monkeypatch.setattr(os, "fsync", lambda fd: None)

    num_files = 1000

    for files in range(num_files):
        (tmp_path / f"file{files}.jpg").write_text("x", encoding="utf-8")

    progress_state = {"last_done": 0, "total": None}

    def progress(last_done, total, msg):
        progress_state["last_done"] = last_done
        progress_state["total"] = total

    results = {}

    def finished(summary, mapping):

        results["summary"] = summary
        results["mapping"] = mapping

    run_blinder(
        base_path=tmp_path,
        extension=".txt",
        move_to_blind=True,
        clone_og=False,
        include_subdirs=False,
        progress=progress,
        finished=finished
    )

    assert "mapping" in results and isinstance(results["mapping"], dict) and len(results["mapping"]) == 0
    assert progress_state["total"] is None
    assert progress_state["last_done"] == 0

    assert "No files found" in results["summary"]
    assert ".txt" in results["summary"]


def test_ext(tmp_path, monkeypatch):

    """
    Test the blinder function to ensure it correctly handles different file extensions and processes only the specified extension

    """
    monkeypatch.setattr(os, "fsync", lambda fd: None)

    num_files = 1000

    for files in range(num_files):
        (tmp_path / f"file{files}.JPG").write_text("x", encoding="utf-8")

    progress_state = {"last_done": 0, "total": None}

    def progress(last_done, total, msg):
        progress_state["last_done"] = last_done
        progress_state["total"] = total

    results = {}

    def finished(summary, mapping):

        results["summary"] = summary
        results["mapping"] = mapping

    run_blinder(
        base_path=tmp_path,
        extension=".jpg",
        move_to_blind=True,
        clone_og=False,
        include_subdirs=False,
        progress=progress,
        finished=finished
    )

    assert "mapping" in results and isinstance(results["mapping"], dict) and len(results["mapping"]) == num_files
    assert progress_state["total"] == num_files and progress_state["last_done"] == num_files
    assert len(set(results["mapping"].values())) == len(results["mapping"])
