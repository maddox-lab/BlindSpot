import csv
import os
import uuid
from datetime import datetime
from pathlib import Path
from .BlindSpot_core import gen_name, normalize_path, file_hash  # type: ignore




def time_stamp():
    """
    A simple function to create the time for journal entries
    """

    return datetime.now().isoformat(timespec="seconds")


def track_action(
    log_path,
    TxtID="",
    old_path="",
    dest_path="",
    old_name="",
    new_name="",
    action="",
    message="",
):
    """
    tracks actions taken during the blinding process and logs them to a _blinding_log.csv (journal) file

    """

    header = [
        "Timestamp",
        "TxtID",
        "Old file path",
        "Destination path",
        "Old file name",
        "New file name",
        "Action",
        "Message",
    ]

    log_path = Path(log_path)
    write_header = (not log_path.exists()) or (log_path.stat().st_size == 0)

    with open(log_path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(header)

        w.writerow(
            [
                time_stamp(),
                TxtID or "",
                normalize_path(old_path),
                normalize_path(dest_path),
                str(old_name or ""),
                str(new_name or ""),
                str(action or ""),
                str(message or ""),
            ]
        )

        f.flush()  # Makes sure that the fles are saved
        os.fsync(f.fileno())  # Makes sure the data is written in case of crash


track_function = track_action  # Variable naames were updated but tests expect old name and i did not want to rewrite them



def hashes_from_journal(log_path):
    
    hashes = set()

    for row in read_journal(log_path):
        h = (row.get("Message") or "").strip()

        if len(h) == 32: 
            hashes.add(h)

    return hashes


def read_journal(log_path):
    """
    Reads the journal log file and returns a list of dictionaries representing each row

    """

    log_path = Path(log_path)
    if (
        not log_path.exists() or log_path.stat().st_size == 0
    ):  # makes sure the file exists and is not empty
        return []

    with open(log_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = []
        for r in reader:
            row = {
                "Timestamp": (r.get("Timestamp") or "").strip(),
                "TxtID": (r.get("TxtID") or "").strip(),
                "Old file path": (r.get("Old file path") or "").strip(),
                "Destination path": (r.get("Destination path") or "").strip(),
                "Old file name": (r.get("Old file name") or "").strip(),
                "New file name": (r.get("New file name") or "").strip(),
                "Action": (r.get("Action") or "").strip(),
                "Message": (r.get("Message") or "").strip(),
            }

            if (not row["Destination path"]) and row["Message"].startswith(
                "dest="
            ):  # Backwords compatibility for older log files
                row["Destination path"] = row["Message"][
                    5:
                ].strip()  # extracts the dest path from the message box

            rows.append(row)

        return rows


def build_journal_state(
    log_path,
):  # Make sure the actions are saved in the place thaat the files exist
    """
    Writes the journal / log file and tracks the state of each file being processed

    """

    rows = read_journal(log_path)
    state: dict[str, dict] = {}

    for row in rows:
        old = (row.get("Old file path") or "").strip()
        if not old:
            continue

        info = state.setdefault(
            old, {"done": False, "latest_done_new": None, "pending": None}
        )

        action = (row.get("Action") or "").strip().lower()
        txtid = (row.get("TxtID") or "").strip()
        dest = (row.get("Destination path") or "").strip()
        new = (row.get("New file name") or "").strip()
        old_name = normalize_path(row.get("Old file name") or "").strip()

        if action == "done":
            info["done"] = True
            info["latest_done_new"] = new or info["latest_done_new"]
            info["pending"] = None
        elif action == "start":
            info["pending"] = {
                "TxtID": txtid,
                "dest": dest,
                "new": new,
                "old_name": old_name,
            }
        elif action in {"aborted", "lost", "error"}:
            info["pending"] = None

        elif action in {
            "moved",
            "copied",
            "key",
            "keyed",
        }:  # intermediate steps for pending operations, makes crash resistance better
            if info["pending"] is None:
                info["pending"] = {
                    "TxtID": txtid,
                    "dest": dest,
                    "new": new,
                    "old_name": old_name,
                }
            else:  # update any missing info

                if not info["pending"].get("TxtID") and txtid:
                    info["pending"]["TxtID"] = txtid

                if not info["pending"].get("dest") and dest:
                    info["pending"]["dest"] = dest

                if not info["pending"].get("new") and new:
                    info["pending"]["new"] = new

                if not info["pending"].get("old_name") and old_name:
                    info["pending"]["old_name"] = old_name

    return state


def recover_from_journal(log_path, progress=None):  # If crash, fix!
    """
    Attempts to recover the processing state from the journal / log file
    """
    state = build_journal_state(log_path)

    finalized = 0
    aborted = 0
    lost = 0

    for old, info in state.items():
        if info.get("done"):
            continue

        pending = info.get("pending")
        if not pending:
            continue

        txtid = pending.get("TxtID", "") or ""
        dest = pending.get("dest", "") or ""
        new = pending.get("new", "") or ""
        old_name = pending.get("old_name", "") or ""

        old_exists = Path(old).exists()
        dest_exists = Path(dest).exists() if dest else False

        if progress:
            progress(0, 1, f"Crash recovery check: {old_name}")

        if dest and dest_exists:
            try:
                if Path(dest).stat().st_size == 0:
                    raise ValueError("destination is 0 bytes")

                track_action(
                    log_path,
                    TxtID=txtid,
                    old_path=old,
                    dest_path=dest,
                    old_name=old_name,
                    new_name=new,
                    action="done",
                    message="Recovered: destination exists",
                )
                finalized += 1
            except Exception as e:
                track_action(
                    log_path,
                    TxtID=txtid,
                    old_path=old,
                    dest_path=dest,
                    old_name=old_name,
                    new_name=new,
                    action="aborted",
                    message=f"Recovered: invalid dest ({type(e).__name__}: {e})",
                )
                aborted += 1

        elif old_exists and (not dest_exists):
            track_action(
                log_path,
                TxtID=txtid,
                old_path=old,
                dest_path=dest,
                old_name=old_name,
                new_name=new,
                action="aborted",
                message="Recovered: old exists, dest missing",
            )
            aborted += 1

        else:
            track_action(
                log_path,
                TxtID=txtid,
                old_path=old,
                dest_path=dest,
                old_name=old_name,
                new_name=new,
                action="lost",
                message="Recovered: unresolved",
            )
            lost += 1

    return finalized, aborted, lost


def where_file_go(
    log_path,
    old_path,
    old_name,
    out_dir,
    ext=None,
    entries=None,
    extension=None,
    state=None,
    file_hash_value="", 
):  # Make sure things move to the correct place, the test works and failes if this is not in... so we keepign it
    """
    Determines the destination path and new filename for a file to be blinded



    """

    if entries is None:
        entries = state
    if entries is None:
        entries = {}

    if ext is None:
        ext = extension

    ext = str(ext or "")
    if ext and not ext.startswith("."):
        ext = "." + ext

    old_path = str(old_path)
    out_dir = Path(out_dir)

    info = entries.setdefault(
        old_path, {"done": False, "latest_done_new": None, "pending": None}
    )

    if info.get("done"):
        return "", "", ""

    pending = info.get("pending")
    if pending and pending.get("dest"):
        dest = pending["dest"]
        return pending.get("TxtID", ""), dest, pending.get("new") or Path(dest).name

    txtid = uuid.uuid4().hex[
        :10
    ]  # creates a unique txtID to link through the files so in case something goes whack with the name

    def unique_name(dirpath: Path) -> str:
        name = gen_name(ext)
        while (dirpath / name).exists():
            name = gen_name(ext)
        return name

    blind_name = unique_name(out_dir)

    dest_str = str(out_dir / blind_name)

    track_action(
        log_path,
        TxtID=txtid,
        old_path=old_path,
        dest_path=dest_str,
        old_name=old_name,
        new_name=blind_name,
        action="start",
        message= file_hash_value,
    )

    info["pending"] = {
        "TxtID": txtid,
        "dest": dest_str,
        "new": blind_name,
        "old_name": old_name,
    }

    return txtid, dest_str, blind_name


def blinding_key_path(log_path):
    """
    Reads the blinding key from the journal log file and returns a mapping of original file paths to new blinded filenames

    """

    log_path = Path(log_path)
    if not log_path.exists() or log_path.stat().st_size == 0:
        return {}

    mapping: dict[str, str] = {}

    with open(log_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:

            if (row.get("Action") or "").strip().lower() != "done":
                continue

            old = normalize_path(row.get("Old file path") or "").strip()
            dest = normalize_path(row.get("Destination path") or "").strip()

            if old and dest:
                mapping[old] = Path(dest).name

    return mapping  # returns the blinded dictionary