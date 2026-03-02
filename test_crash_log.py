import csv
import os
from pathlib import Path
import shutil
from .functions.BlindSpot_journal import (
    build_journal_state,
    track_action,
    read_journal,
    recover_from_journal,
    where_file_go,
)

from .functions.BlindSpot_core import normalize_path

from .functions.BlindSpot_blindingcode import run_blinder

import pytest


def assert_log_has_action(log_file, action, old_path):
    """
    Function to test is a specific action and old file path combo exist in the _blinding_log.csv file

    """

    rows = read_journal(log_file)
    assert any(r["Action"] == action and r["Old file path"] == old_path for r in rows)


def test_track_function(tmp_path):
    """
    Test the track_action function by writing an entry and making sure it exists

    """

    log_file = tmp_path / "_blinding_log.csv"

    track_action(
        log_file,
        TxtID="73291",
        old_path="old.jpeg",
        dest_path="DEST",
        old_name="old-name",
        new_name="new-name",
        action="start",
        message="This is a test message.",
    )

    with open(log_file, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

        assert rows[0]["TxtID"] == "73291"
        assert rows[0]["Action"] == "start"
        assert rows[0]["Old file path"] == normalize_path("old.jpeg")
        assert rows[0]["Destination path"] == normalize_path("DEST")
        assert rows[0]["Old file name"] == "old-name"
        assert rows[0]["New file name"] == "new-name"
        assert rows[0]["Message"] == "This is a test message."


def test_read_journal(tmp_path):
    """

    Test the read_journal function by writing multiple entries and making sure they are recalled correctly
    """

    log_file = tmp_path / "_blinding_log.csv"

    track_action(
        log_file,
        TxtID="73291",
        old_path=normalize_path("old.jpeg"),
        dest_path=normalize_path("DEST"),
        old_name="old-name",
        new_name="new-name",
        action="start",
        message="This is a test message.",
    )

    track_action(
        log_file,
        TxtID="80329",
        old_path=normalize_path("old-2.jpeg"),
        dest_path=normalize_path("DEST-2"),
        old_name="old2-name",
        new_name="new2-name",
        action="start",
        message="This is a test message.",
    )

    rows = read_journal(log_file)

    assert isinstance(rows, list)

    assert len(rows) == 2
    assert rows[0]["TxtID"] == "73291"
    assert rows[0]["Action"] == "start"
    assert rows[0]["Old file path"] == normalize_path("old.jpeg")
    assert rows[0]["Destination path"] == normalize_path("DEST")
    assert rows[0]["Old file name"] == "old-name"
    assert rows[0]["New file name"] == "new-name"
    assert rows[0]["Message"] == "This is a test message."

    assert rows[1]["TxtID"] == "80329"
    assert rows[1]["Action"] == "start"
    assert rows[1]["Old file path"] == normalize_path("old-2.jpeg")
    assert rows[1]["Destination path"] == normalize_path("DEST-2")
    assert rows[1]["Old file name"] == "old2-name"
    assert rows[1]["New file name"] == "new2-name"
    assert rows[1]["Message"] == "This is a test message."


def test_build_journal(tmp_path):
    """
    Test the build_journal_state function by writing an entry and making sure the journal is written correctly

    """

    log_file = tmp_path / "_blinding_log.csv"

    track_action(
        log_file,
        TxtID="73291",
        old_path=normalize_path("old.jpeg"),
        dest_path=normalize_path("DEST"),
        old_name="old-name",
        new_name="new-name",
        action="start",
        message="This is a test message.",
    )

    journal_state = build_journal_state(log_file)

    assert isinstance(journal_state, dict)
    assert "old.jpeg" in journal_state

    assert journal_state["old.jpeg"]["done"] is False
    assert journal_state["old.jpeg"]["pending"]["TxtID"] == "73291"
    assert journal_state["old.jpeg"]["pending"]["dest"] == "dest"
    assert journal_state["old.jpeg"]["pending"]["new"] == "new-name"


def test_abort_reconcile(tmp_path):
    """
    Test the recover_from_journal function by simulating an aborted operation and making sure it is rerun correctly


    """

    log_file = tmp_path / "_blinding_log.csv"

    old = tmp_path / "old.png"
    old.write_text("data")
    dest = tmp_path / "Blind Files" / "new-name.png"

    track_action(
        log_file,
        TxtID="73291",
        old_path=str(old),
        dest_path=str(dest),
        old_name=old.name,
        new_name=dest.name,
        action="start",
        message="This is a test message.",
    )

    finalized, aborted, lost = recover_from_journal(log_file)

    with open(log_file, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert (finalized, aborted, lost) == (0, 1, 0)
    assert_log_has_action(log_file, "aborted", normalize_path(str(old)))


def test_done_reconcile(tmp_path):
    """
    Test the recover_from_journal function by simulating a completed operation and making sure it is finalized correctly


    """

    log_file = tmp_path / "_blinding_log.csv"

    old = tmp_path / "old.png"
    old.write_text("data")
    dest = tmp_path / "Blind Files" / "new-name.png"
    dest.parent.mkdir(exist_ok=True)

    track_action(
        log_file,
        TxtID="73291",
        old_path=str(old),
        dest_path=str(dest),
        old_name=old.name,
        new_name=dest.name,
        action="start",
        message="This is a test message.",
    )

    old.rename(dest)

    finalized, aborted, lost = recover_from_journal(log_file)

    with open(log_file, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert (finalized, aborted, lost) == (1, 0, 0)
    assert_log_has_action(log_file, "done", normalize_path(str(old)))


def test_lost_reconcile_journal(tmp_path):
    """
    Test the recover_from_journal function by simulating a lost file and making sure it is identified correctly

    """

    log_file = tmp_path / "_blinding_log.csv"

    old = tmp_path / "old.png"
    old.write_text("data")

    dest = tmp_path / "Blind Files" / "new-name.png"

    track_action(
        log_file,
        TxtID="73291",
        old_path=str(old),
        dest_path=str(dest),
        old_name=old.name,
        new_name=dest.name,
        action="start",
        message="This is a test message.",
    )

    old.unlink()  # simulate file being lost before reconciliation

    finalized, aborted, lost = recover_from_journal(log_file)

    with open(log_file, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert (finalized, aborted, lost) == (0, 0, 1)
    assert_log_has_action(log_file, "lost", normalize_path(str(old)))


def test_pending_reconcile_journal(tmp_path):
    """
    Test the recover_from_journal function by simulating a pending operation and making sure it is identified correctly


    """
    log_file = tmp_path / "_blinding_log.csv"

    old = tmp_path / "old.png"
    old.write_text("data")

    dest = tmp_path / "Blind Files" / "new-name.png"

    track_action(
        log_file,
        TxtID="73291",
        old_path=str(old),
        dest_path=str(dest),
        old_name=old.name,
        new_name=dest.name,
        action="start",
        message="This is a test message.",
    )

    finalized, aborted, lost = recover_from_journal(log_file)

    assert (finalized, aborted, lost) == (0, 1, 0)

    journal_state = build_journal_state(log_file)

    assert normalize_path(str(old)) in journal_state
    assert journal_state[normalize_path(str(old))]["done"] is False


def test_where_file_go(tmp_path):
    """
    Test the where_file_go function by simulating a file that needs to be blinded and ends upwith the correct destination and journal state


    """

    log_file = tmp_path / "_blinding_log.csv"
    log_file = tmp_path / "_blinding_log.csv"
    out_dir = tmp_path / "Blind Files"
    out_dir.mkdir()

    old = tmp_path / "old.nd2"
    old.write_text("data")

    state = {}  # nothing known yet

    txtid, dest_str, blind_name = where_file_go(
        log_path=log_file,
        old_path=str(old),
        old_name=old.name,
        out_dir=out_dir,
        extension="nd2",
        state=state,
    )

    assert txtid is not None
    assert dest_str is not None
    assert blind_name is not None
    assert dest_str == str(out_dir / blind_name)
    assert blind_name.endswith(".nd2")

    key = str(old)

    assert state[key]["pending"]["TxtID"] == txtid
    assert state[key]["pending"]["dest"] == dest_str
    assert state[key]["pending"]["new"] == blind_name
    assert state[key]["done"] is False
    assert blind_name != old.name


def test_crash_log(tmp_path):
    """
    Test the full crash log and recovery process by simulating a file that is being blinded when a crash occurs and tests recovery on a rerun


    """

    log_file = tmp_path / "_blinding_log.csv"

    old = tmp_path / "old.txt"
    old.write_text("data")
    dest = tmp_path / "Blind Files" / "new.txt"
    dest.parent.mkdir(exist_ok=True)

    track_action(
        log_file,
        TxtID="73291",
        old_path=normalize_path(str(old)),
        dest_path=normalize_path(str(dest)),
        old_name=old.name,
        new_name=dest.name,
        action="start",
        message="Testing the crash log.",
    )

    journal_state = build_journal_state(log_file)

    key = normalize_path(str(old))

    assert log_file.exists()
    assert key in journal_state
    assert journal_state[key]["done"] is False
    assert journal_state[key]["pending"]["TxtID"] == "73291"
    assert journal_state[key]["pending"]["dest"] == normalize_path(str(dest))
    assert journal_state[key]["pending"]["new"] == "new.txt"
    assert journal_state[key]["pending"]["old_name"] == "old.txt"


def test_reconcile_multi(tmp_path):
    """
    Test the recover_from_journal function by simulating multiple files that are being blinded when a crash occurs and tests recovery on a rerun


    """

    log_file = tmp_path / "_blinding_log.csv"

    old1 = tmp_path / "old1.txt"
    old1.write_text("data")
    dest1 = tmp_path / "Blind Files" / "new1.txt"
    dest1.parent.mkdir(parents=True, exist_ok=True)
    dest1.write_text("data")

    old2 = tmp_path / "old2.txt"
    old2.write_text("data")
    dest2 = tmp_path / "Blind Files" / "new2.txt"

    track_action(
        log_file,
        TxtID="1",
        old_path=str(old1),
        dest_path=str(dest1),
        old_name=old1.name,
        new_name=dest1.name,
        action="start",
        message="m",
    )

    track_action(
        log_file,
        TxtID="2",
        old_path=str(old2),
        dest_path=str(dest2),
        old_name=old2.name,
        new_name=dest2.name,
        action="start",
        message="m",
    )

    finalized, aborted, lost = recover_from_journal(log_file)

    assert (finalized, aborted, lost) == (1, 1, 0)


def test_crash_copy(tmp_path, monkeypatch):
    """
    Test the blinder's behavior when a crash occurs during the copy operation in move_to_blind mode, and ensure that it correctly recovers on a rerun

    """

    monkeypatch.setattr(os, "fsync", lambda fd: None)

    num_files = 1000
    for i in range(num_files):
        (tmp_path / f"img_{i:04d}.nd2").write_text("x", encoding="utf-8")

    num_run = 500

    copy_calls = {"count": 0}
    real_copy2 = shutil.copy2

    def crash_copy2(src, dst, *, follow_symlinks=True):
        if copy_calls["count"] == num_run:
            raise RuntimeError("Simulated crash during copy")
        copy_calls["count"] += 1
        return real_copy2(src, dst, follow_symlinks=follow_symlinks)

    monkeypatch.setattr(shutil, "copy2", crash_copy2)

    result1 = {}

    def finished1(summary, mapping):
        result1["summary"] = summary
        result1["mapping"] = mapping

    run_blinder(
        base_path=tmp_path,
        extension="nd2",
        move_to_blind=True,
        clone_og=True,
        include_subdirs=False,
        progress=None,
        finished=finished1,
    )

    assert (
        copy_calls["count"] == num_run
    )  # make sure the correct number of copies exist

    blind_dir = tmp_path / "Blind Files"
    assert blind_dir.exists()

    assert "mapping" in result1
    assert len(result1["mapping"]) == num_run

    assert (
        len(list(tmp_path.glob("img_*.nd2"))) == num_files
    )  # checks the originals should still exist because clone_og=True

    copied_so_far = len(list(blind_dir.glob("*.nd2")))
    assert copied_so_far == num_run

    # restore real copy2
    monkeypatch.setattr(shutil, "copy2", real_copy2)

    result2 = {}

    def finished2(summary, mapping):
        """
        Callback function to capture the summary and mapping results after the second run of the blinder

        """
        result2["summary"] = summary
        result2["mapping"] = mapping

    run_blinder(
        base_path=tmp_path,
        extension="nd2",
        move_to_blind=True,
        clone_og=True,
        include_subdirs=False,
        progress=None,
        finished=finished2,
    )

    assert len(list(blind_dir.glob("*.nd2"))) == num_files
    assert len(list(tmp_path.glob("img_*.nd2"))) == num_files

    assert "mapping" in result2 and len(result2["mapping"]) == num_files

    for original, blinded_name in result2["mapping"].items():
        orig_path = Path(original)
        blind_path = blind_dir / blinded_name

        assert orig_path.parent == tmp_path
        assert orig_path.exists()

        assert blind_path.exists()
        assert blinded_name != orig_path.name
        assert blinded_name.endswith(".nd2")


def test_crash_nomove(tmp_path, monkeypatch):
    """
    Test the blinder's behavior when a crash occurs during the rename operation if the blinded files are not moved, and ensures that it correctly recovers on a rerun



    """
    monkeypatch.setattr(os, "fsync", lambda fd: None)

    num_files = 1000
    for i in range(num_files):
        (tmp_path / f"img_{i:04d}.nd2").write_text("x", encoding="utf-8")

    num_run = 500
    rename_calls = {"count": 0}

    real_replace = os.replace
    real_rename = os.rename

    def crash_replace(src, dst):
        """
        A patched version of os.replace that simulates a crash when num_run is reached


        """
        if rename_calls["count"] == num_run:
            raise RuntimeError("Simulated crash during rename")
        rename_calls["count"] += 1
        return real_replace(src, dst)

    def crash_rename(src, dst):
        """
        A patched version of os.rename that simulates a crash


        """

        if rename_calls["count"] == num_run:
            raise RuntimeError("Simulated crash during rename")
        rename_calls["count"] += 1
        return real_rename(src, dst)

    monkeypatch.setattr(os, "replace", crash_replace)
    monkeypatch.setattr(os, "rename", crash_rename)

    result1 = {}

    def finished1(summary, mapping):

        result1["summary"] = summary
        result1["mapping"] = mapping

    run_blinder(
        base_path=tmp_path,
        extension="nd2",
        move_to_blind=False,
        clone_og=False,
        include_subdirs=False,
        progress=None,
        finished=finished1,
    )
    assert rename_calls["count"] == num_run
    all_nd2 = list(tmp_path.glob("*.nd2"))
    originals_left = list(tmp_path.glob("img_*.nd2"))
    assert len(all_nd2) == num_files
    assert 0 < len(originals_left) < num_files

    assert "mapping" in result1
    assert len(result1["mapping"]) == num_run
    monkeypatch.setattr(os, "replace", real_replace)
    monkeypatch.setattr(os, "rename", real_rename)

    result2 = {}

    def finished2(summary, mapping):

        result2["summary"] = summary
        result2["mapping"] = mapping

    run_blinder(
        base_path=tmp_path,
        extension="nd2",
        move_to_blind=False,
        clone_og=False,
        include_subdirs=False,
        progress=None,
        finished=finished2,
    )

    assert len(list(tmp_path.glob("img_*.nd2"))) == 0
    assert len(list(tmp_path.glob("*.nd2"))) == num_files
    assert "mapping" in result2
    assert len(result2["mapping"]) == num_files

    for original, blinded_name in result2["mapping"].items():
        orig_path = Path(original)
        new_path = tmp_path / blinded_name

        assert orig_path.parent == tmp_path
        assert new_path.exists()
        assert new_path.name != orig_path.name
        assert new_path.suffix.lower() == ".nd2"


def test_rerun(tmp_path, monkeypatch):
    """
    Test the blinder's behavior when a crash occurs during the blinding process and correctly recovers on a rerun


    """

    monkeypatch.setattr(os, "fsync", lambda fd: None)

    num_files = 1000
    for i in range(num_files):
        (tmp_path / f"img_{i:04d}.nd2").write_text("x", encoding="utf-8")

    num_run = 1000
    count = {"n": 0}

    real_replace = os.replace
    real_rename = os.rename

    def crash_replace(src, dst):

        if (
            count["n"] == num_run
        ):  # simulate crash on the rename/replace step after num_run files have been processed
            raise RuntimeError("Simulated crash during rename/replace")
        count["n"] += 1
        return real_replace(src, dst)

    def crash_rename(src, dst):

        if (
            count["n"] == num_run
        ):  # simulate crash on the rename/replace step after num_run files have been processed
            raise RuntimeError("Simulated crash during rename/replace")
        count["n"] += 1
        return real_rename(src, dst)

    monkeypatch.setattr(os, "replace", crash_replace)
    monkeypatch.setattr(os, "rename", crash_rename)

    result1 = {}

    def finished1(summary, mapping):
        result1["summary"] = summary
        result1["mapping"] = mapping

    run_blinder(
        base_path=tmp_path,
        extension="nd2",
        move_to_blind=False,
        clone_og=False,
        include_subdirs=False,
        progress=None,
        finished=finished1,
    )

    assert count["n"] == num_run

    all_nd2 = list(tmp_path.glob("*.nd2"))
    originals_left = list(tmp_path.glob("img_*.nd2"))

    assert len(all_nd2) == num_files
    assert len(originals_left) == 0

    assert "mapping" in result1
    assert len(result1["mapping"]) == num_run

    monkeypatch.setattr(os, "replace", real_replace)
    monkeypatch.setattr(os, "rename", real_rename)

    result2 = {}

    def finished2(summary, mapping):
        result2["summary"] = summary
        result2["mapping"] = mapping

    calls = {"n": 0}

    def count_replace(src, dst):

        calls["n"] += 1
        return real_replace(src, dst)

    def count_rename(src, dst):

        calls["n"] += 1
        return real_rename(src, dst)

    monkeypatch.setattr(os, "replace", count_replace)
    monkeypatch.setattr(os, "rename", count_rename)

    real_replace = os.replace
    real_rename = os.rename

    run_blinder(
        base_path=tmp_path,
        extension="nd2",
        move_to_blind=False,
        clone_og=False,
        include_subdirs=False,
        progress=None,
        finished=finished2,
    )

    assert len(list(tmp_path.glob("img_*.nd2"))) == 0
    assert len(list(tmp_path.glob("*.nd2"))) == num_files

    assert "mapping" in result2
    assert len(result2["mapping"]) == num_files

    assert calls["n"] == 0

    for original, blinded_name in result2["mapping"].items():
        orig_path = Path(original)
        new_path = tmp_path / blinded_name

        assert orig_path.parent == tmp_path
        assert new_path.exists()
        assert new_path.name != orig_path.name
        assert new_path.suffix.lower() == ".nd2"
