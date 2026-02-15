import os
import csv
import uuid
import time
import shutil
import random
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import webbrowser
import sys

### Used Black package to make code even


APP_NAME = "BlindSpot"
APP_VERSION = "3.3"
AUTHOR = "Jenna Vesey"
LAB = "The Amy Maddox Lab, UNC Chapel Hill"

SPECIAL_THANKS = (
    "Linnea Wethekam, Amy Liu, and Siddharth \n"
    "Sankaranarayanan for their testing, feedback, and support."
)

LICENSE = "MIT License."


# ==================== Core helpers =======================


def gen_name(
    file_ext: str,
):  # made it convertable from UUID to make it more random, 32 million options
    """

    Makes a random 8 character filename with the given file extension

    """

    file_ext = str(file_ext or "").lower()

    if not file_ext.startswith("."):
        file_ext = "." + file_ext

    return uuid.uuid4().hex[:8] + file_ext


def safe_path(base_path, file):  # The person who needed this has a mac
    """
    Generates a cross-compatible relative path from user identified base path to a renamed file

    """

    base_path = Path(base_path).resolve()
    file = Path(file).resolve()

    try:
        return str(file.relative_to(base_path))

    except ValueError:
        return os.path.relpath(str(file), str(base_path))


def safe_relpath(
    base_path, target
):  # I renamed the function halfway through and needed to convert without rewritting it
    """
    Allows the safe path to be recalled by pytesting functions

    """

    return safe_path(base_path, target)


def save_final_key(map_path: Path, final_mapping: dict[str, str]): # Macs did not like the original writing in v3.2 so needed to be updated
    map_path = Path(map_path)
    existing = set()

    if (
        map_path.exists() and map_path.stat().st_size > 0
    ):  # Load all existing rows so no duplicates happen
        with open(map_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                old_name = (row.get("Old file name") or "").strip()
                new_name = (row.get("New file name") or "").strip()
                old_path = (row.get("Old path") or "").strip()
                if old_name and new_name and old_path:
                    existing.add((old_name, new_name, old_path))

    write_header = (not map_path.exists()) or map_path.stat().st_size == 0

    with open(map_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(["Old file name", "New file name", "Old path"])

        for old_full, new_name in final_mapping.items():
            old_full = str(old_full)
            old_name = Path(old_full).name
            old_path = old_full

            row_key = (old_name, new_name, old_path)
            if row_key in existing:
                continue

            writer.writerow([old_name, new_name, old_path])
            existing.add(row_key)


# ================= Crash resistance =====================


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
                str(old_path or ""),
                str(dest_path or ""),
                str(old_name or ""),
                str(new_name or ""),
                str(action or ""),
                str(message or ""),
            ]
        )

        f.flush()  # Makes sure that the fles are saved
        os.fsync(f.fileno())  # Makes sure the data is written in case of crash


track_function = track_action  # Variable naames were updated but tests expect old name and i did not want to rewrite them


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
        old_name = (row.get("Old file name") or "").strip()

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
):  # Make sure things move to the correct place
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
        message="",
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

            old = (row.get("Old file path") or "").strip()
            dest = (row.get("Destination path") or "").strip()

            if old and dest:
                mapping[old] = Path(dest).name

    return mapping  # returns the blinded dictionary


# ==================== The Blinding Function =======================


def run_blinder(
    base_path,
    extension,
    move_to_blind,
    clone_og,
    include_subdirs=False,
    progress=None,
    finished=None,
    **kwargs,  # makes tests resilient to extra args
):
    """
    The main function to run the blinding process on a given directory with user specified options

    """

    try:
        base_path = (
            Path(base_path).expanduser().resolve()
        )  # ensures we have an absolute path to work with (important for cross-compatability)

        ext = str(extension or "")
        if not ext.startswith("."):
            ext = "." + ext

        blind_folder = base_path / "Blind Files"
        journal_path = base_path / "_blinding_log.csv"
        key_csv_path = base_path / "Blinding_Key.csv"

        skip_these = {journal_path.resolve(), key_csv_path.resolve()}

        finalized, aborted, lost = recover_from_journal(journal_path, progress)
        state = build_journal_state(journal_path)

        if move_to_blind:
            blind_folder.mkdir(exist_ok=True)

        finder = base_path.rglob if include_subdirs else base_path.glob

        files = [
            p
            for p in finder("*")
            if p.is_file()
            and p.suffix.lower() == ext.lower()
            and p.resolve() not in skip_these
            and blind_folder not in p.parents
        ]  # finds all files with the chosen extension

        if not files:  # if there are no files to process, return early with a message

            already_blinded = blinding_key_path(journal_path)

            if already_blinded:  # returns sthat files have already been blinded
                msg = (
                    f"No unblinded files found with the extension {ext}. \n"
                    f"Everything has already been blinded. Total number of blinded files already recorded (any extension): {len(already_blinded)}" # Too lazy to add sort by file type
                )

                if finished:
                    finished(msg, already_blinded)

                return {"mapping": already_blinded, "summary": msg}

            else:  # returns a message no files have been found
                msg = f"No files found with the extension {ext}."

                if finished:
                    finished(msg, {})

                return {"mapping": {}, "summary": msg}

        if (not move_to_blind) and (
            not clone_og
        ):  # For rename but not move mode, skip files that are already "blinded" by name (in case of crash)

            existing_blinded_names = set(blinding_key_path(journal_path).values())
            files = [p for p in files if p.name not in existing_blinded_names]

            if not files:
                already_blinded = blinding_key_path(journal_path)

                msg = (
                    f"No unblinded files found with the extension {ext}.\n"
                    f"Everything has already been blinded. Total number of blinded files already recorded (any extension): {len(already_blinded)}"
                )

                if finished:
                    finished(msg, already_blinded)
                return {"mapping": already_blinded, "summary": msg}

        total = len(files)
        done = 0
        if progress:
            progress(0, total, "Starting blinding process")

        moved = 0
        copied = 0
        skipped_done = 0
        skipped_error = 0

        t_start = time.perf_counter()
        eta_samples = []
        eta_window = 5

        for fpath in files:
            t0 = time.perf_counter()
            full_old = str(fpath.resolve())
            rel = safe_path(base_path, fpath)

            info = state.get(full_old)
            if info and info.get("done"):
                skipped_done += 1
                done += 1
                if progress:
                    progress(done, total, f"Already done: {rel}")
                continue

            out_dir = blind_folder if move_to_blind else fpath.parent

            txtid, dest_str, blind_name = where_file_go(
                journal_path,
                full_old,
                fpath.name,
                out_dir,
                ext=fpath.suffix,
                entries=state,
            )

            if not dest_str:
                skipped_done += 1
                done += 1
                continue

            dest_path = Path(dest_str)

            if dest_path.exists():
                track_action(
                    journal_path,
                    TxtID=txtid,
                    old_path=full_old,
                    dest_path=dest_str,
                    old_name=fpath.name,
                    new_name=blind_name,
                    action="done",
                    message="Destination already exists",
                )

                state.setdefault(
                    full_old, {"done": False, "latest_done_new": None, "pending": None}
                )

                state[full_old]["done"] = True
                state[full_old]["pending"] = None

                done += 1

                continue

            try:

                if clone_og:
                    shutil.copy2(str(fpath), str(dest_path))  # lets the og clone move
                    copied += 1
                    track_action(
                        journal_path,
                        TxtID=txtid,
                        old_path=full_old,
                        dest_path=dest_str,
                        old_name=fpath.name,
                        new_name=blind_name,
                        action="copied",
                        message="",
                    )

                else:  # Just clones

                    os.replace(str(fpath), str(dest_path))
                    moved += 1
                    track_action(
                        journal_path,
                        TxtID=txtid,
                        old_path=full_old,
                        dest_path=dest_str,
                        old_name=fpath.name,
                        new_name=blind_name,
                        action="moved",
                        message="",
                    )

                track_action(
                    journal_path,
                    TxtID=txtid,
                    old_path=full_old,
                    dest_path=dest_str,
                    old_name=fpath.name,
                    new_name=blind_name,
                    action="keyed",
                    message="",
                )

                track_action(
                    journal_path,
                    TxtID=txtid,
                    old_path=full_old,
                    dest_path=dest_str,
                    old_name=fpath.name,
                    new_name=blind_name,
                    action="done",
                    message="",
                )

                state.setdefault(
                    full_old, {"done": False, "latest_done_new": None, "pending": None}
                )
                state[full_old]["done"] = True
                state[full_old]["pending"] = None

            except (
                Exception
            ) as e:  # Exception to make sure the program doesn't crash if one file is weird

                skipped_error += 1
                track_action(
                    journal_path,
                    TxtID=txtid,
                    old_path=full_old,
                    dest_path=dest_str,
                    old_name=fpath.name,
                    new_name=blind_name,
                    action="error",
                    message=f"{type(e).__name__}: {e}",
                )

            done += 1

            dt = time.perf_counter() - t0
            eta_samples.append(dt)
            if len(eta_samples) > eta_window:
                eta_samples.pop(0)
            avg = sum(eta_samples) / len(eta_samples)
            eta_sec = int(avg * max(total - done, 0))

            if progress:
                progress(done, total, f"Processed {rel} (ETA {eta_sec}s)")

        elapsed = time.perf_counter() - t_start
        summary = (
            f"Blinding Done!\n\n"
            f"Base folder: {base_path}\n"
            f"Total files: {total}\n"
            f"Blinded moved/renamed: {moved}\n"
            f"Blinded copied: {copied}\n"
            f"Already done skipped: {skipped_done}\n"
            f"Errors skipped: {skipped_error}\n"
            f"Crash recovery: finalized={finalized}, aborted={aborted}, lost={lost}\n"
            f"Elapsed: {int(elapsed)} seconds"
        )  # Readout at end

        final_mapping = blinding_key_path(journal_path)

        if finished:
            finished(summary, final_mapping)

        return {"mapping": final_mapping, "summary": summary}

    except Exception as e:

        msg = f"Error: {e}"
        if finished:
            finished(msg, {})
        return {"mapping": {}, "summary": msg}


# ==================== GUI =========================


class BlinderApp(tk.Tk):
    """
    Gui application class for the BlindSpot blinding tool, built with tkinter.
    """

    def __init__(self):

        super().__init__()

        if getattr(sys, "frozen", False):
            base_path = Path(sys._MEIPASS)

        else:
            base_path = Path(__file__).parent

        self.title(APP_NAME)

        if sys.platform == "win32":

            icon_path = (
                base_path / "lil_timmy.ico"
            )  # Custom icon file for app :D its a worm. I made him in MS Paint. His name is Lil Timmy, be nice to him. He wears sunglasses (blinders) hes cool

            if icon_path.exists():

                self.iconbitmap(icon_path)

        menubar = tk.Menu(self)  # All the code for menu bar
        self.config(menu=menubar)
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

        # GO TARHEELS (everything is Carolina Blue because of course it is)

        outer_frame = tk.Frame(
            self, borderwidth=2, relief="solid", bg="#4B9CD3"
        )  # outer frame for styling
        self.outer = outer_frame
        self.outer.pack(fill="both", expand=True, padx=10, pady=10)

        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("Blue.TLabel", background="#13294B", foreground="white")
        style.configure("Blue.TButton", background="#13294B", foreground="white")
        style.configure("LiteBlue.TButton", background="#4B9CD3", foreground="white")

        style.configure(
            "Blue.TLabelframe.Label", background="#13294B", foreground="white"
        )
        style.configure("Blue.TCheckbutton", background="#13294B", foreground="white")
        style.map(
            "Blue.TCheckbutton",
            foreground=[("active", "white")],
            background=[("active", "#1f2a44")],
        )

        style.configure("Txt.TLabel", background="#13294B", foreground="white")
        style.configure("LightBlue.TLabel", background="#4B9CD3", foreground="#13294B")

        style.layout("Blue.TProgressbar", style.layout("Horizontal.TProgressbar"))

        style.configure(
            "Blue.TProgressbar",
            background="#13294B",
            troughcolor="#4B9CD3",
            bordercolor="black",
        )

        style.configure("White.TLabel", background="White", foreground="#13294B")

        self.path_var = tk.StringVar(value=str(Path.home() / "Desktop"))
        self.file_type = tk.StringVar(value="nd2")
        self.move_var = tk.BooleanVar(value=True)
        self.clone_var = tk.BooleanVar(value=False)
        self.subdirs_var = tk.BooleanVar(value=True)

        self.status_var = tk.StringVar(value="Ready.")
        self.running = False

        self._build_ui()

    def show_about(self):
        """

        Initializes and displays the "About" window with application information and credits.

        """
        win = tk.Toplevel(self)
        win.title("About")
        win.resizable(False, False)
        win.transient(self)
        win.grab_set()

        pad = {"padx": 14, "pady": 8}
        container = tk.Frame(win, background="white", borderwidth=2, relief="raised")
        self.container = container
        container.pack(fill="both", expand=True, **pad)

        ttk.Label(
            container,
            text=APP_NAME,
            style="White.TLabel",
            font=("Helvetica", 16, "bold"),
        ).pack(**pad)
        ttk.Label(container, text=f"Version {APP_VERSION}", style="White.TLabel").pack()

        ttk.Separator(container).pack(fill="x", pady=10)
        ttk.Label(container, text=f"Author: {AUTHOR}", style="White.TLabel").pack(
            anchor="w"
        )
        ttk.Label(container, text=LAB, style="White.TLabel").pack(anchor="w")

        ttk.Separator(container).pack(fill="x", pady=10)
        ttk.Label(
            container,
            text=f"Special thanks to:\n{SPECIAL_THANKS}",
            style="White.TLabel",
        ).pack(anchor="w")

        ttk.Separator(container).pack(fill="x", pady=10)
        ttk.Label(container, text=LICENSE, style="White.TLabel").pack(anchor="w")
        ttk.Button(container, text="OK", command=win.destroy).pack(pady=(12, 4))

    def _build_ui(self):
        """

        Builds the main user interface of the application, including input fields, options, progress bar, and buttons.

        """
        pad = {"padx": 10, "pady": 10}

        frm = tk.Frame(
            self.outer, background="#FFFFFF", relief="raised"
        )  # main content frame
        self.frm = frm
        frm.pack(fill="both", expand=True, **pad)

        row1 = tk.Frame(frm, bg="#13294B", borderwidth=4, relief="raised")
        self.row1 = row1
        row1.pack(fill="x", **pad)

        ttk.Label(row1, text="Base folder:", style="Blue.TLabel").pack(side="left")
        self.path_entry = ttk.Entry(row1, textvariable=self.path_var)
        self.path_entry.pack(side="left", fill="x", expand=True, padx=8)
        browse_btn = ttk.Button(
            row1, text="Browse..", command=self.browse, style="LiteBlue.TButton"
        )
        browse_btn.pack(side="left", padx=8)

        row2 = tk.Frame(frm, bg="#13294B", borderwidth=4, relief="raised")
        self.row2 = row2
        row2.pack(fill="x", **pad)

        ttk.Label(row2, text="File type (extension):", style="Blue.TLabel").pack(
            side="left"
        )
        self.file_type_entry = ttk.Entry(row2, textvariable=self.file_type)
        self.file_type_entry.pack(side="left", fill="x", expand=True, padx=8)

        opts = tk.Frame(frm, bg="#13294B", bd=2, relief="raised")
        opts.pack(fill="x", **pad)
        tk.Label(
            opts,
            text="Options:",
            font=("TkDefaultFont", 10, "bold"),
            bg="#13294B",
            fg="white",
        ).pack(anchor="w", padx=10, pady=(6, 2))

        ttk.Checkbutton(
            opts,
            text="Move to 'Blind Files' folder",
            variable=self.move_var,
            style="Blue.TCheckbutton",
        ).pack(anchor="w", padx=10, pady=4)
        ttk.Checkbutton(
            opts,
            text="Safe mode (copy originals)",
            variable=self.clone_var,
            style="Blue.TCheckbutton",
        ).pack(anchor="w", padx=10, pady=4)
        ttk.Checkbutton(
            opts,
            text="Include subfolders (recursive)",
            variable=self.subdirs_var,
            style="Blue.TCheckbutton",
        ).pack(anchor="w", padx=10, pady=4)

        prog = ttk.Frame(frm, style="Blue.TLabelframe")
        prog.pack(fill="x", **pad)

        self.pbar = ttk.Progressbar(prog, style="Blue.TProgressbar", mode="determinate")
        self.pbar.pack(fill="x", expand=True)

        self.status_lbl = ttk.Label(
            frm, style="Blue.TLabel", textvariable=self.status_var, wraplength=600
        )
        self.status_lbl.pack(fill="x", **pad)

        btns = ttk.Frame(frm, style="White.TLabel")
        btns.pack(fill="x", **pad)

        self.run_btn = ttk.Button(
            btns, text="Run", style="Blue.TButton", command=self.on_run
        )
        self.run_btn.pack(side="left")
        ttk.Button(btns, text="Quit", style="Blue.TButton", command=self.destroy).pack(
            side="right"
        )

        footer = ttk.Frame(self.outer, style="Blue.TLabel")
        footer.pack(side="bottom", fill="x", pady=(1, 3))

        lab_url = "https://asmlab.web.unc.edu/"

        footer_label = ttk.Label(
            footer, text="The Amy Maddox Lab, UNC Chapel Hill", style="Blue.TLabel"
        )

        footer_label.pack()

        footer_label.bind("<Button-1>", lambda e: webbrowser.open_new(lab_url))

    def browse(self):
        """
        Opens a directory selection dialog and updates the path variable with the selected folder.
        """

        folder = filedialog.askdirectory(initialdir=self.path_var.get())
        if folder:
            self.path_var.set(folder)

    def on_run(self):
        """

        Validates user input and starts the blinding process

        """
        if self.running:
            return

        if not self.clone_var.get():
            ok = messagebox.askokcancel(
                f"Warning: {APP_NAME}",
                "This will rename/move files with the target extension.\n"
                "If safe mode is OFF, original names won't remain.\n\n"
                "Continue?",
            )
            if not ok:
                return

        base_path = Path(self.path_var.get()).expanduser()
        if not base_path.exists():
            messagebox.showerror("Error", f"Folder does not exist:\n{base_path}")
            return

        self.running = True
        self.run_btn.configure(state="disabled")
        self.status_var.set("Starting…")
        self.pbar["value"] = 0
        self.pbar["maximum"] = 1

        t = threading.Thread(
            target=run_blinder,
            kwargs=dict(
                base_path=base_path,
                extension=self.file_type.get(),
                move_to_blind=self.move_var.get(),
                clone_og=self.clone_var.get(),
                include_subdirs=self.subdirs_var.get(),
                progress=self.progress_update,
                finished=self.finished,
            ),
            daemon=True,
        )
        t.start()

    def progress_update(self, done, total, msg):
        """

        Updates the progress bar and status message during the blinding process.
        """

        def _ui():

            self.pbar["maximum"] = max(total, 1)
            self.pbar["value"] = done
            self.status_var.set(f"{msg} ({done}/{total})")

        self.after(0, _ui)

    def finished(self, summary, final_mapping):
        """
        Finalized the blinding process, and updates with summary of results. It also saves a user friendly mapping key
        """

        def _ui():
            """
            Updates the GUI with the final summary and saves a Blinding_Key.csv mapping file in the chosen directory
            """
            self.running = False
            self.run_btn.configure(state="normal")
            self.status_var.set("Finished.")
            self.pbar["value"] = self.pbar["maximum"]

            chosen_base = Path(self.path_var.get()).expanduser().resolve()
            map_path = chosen_base / "Blinding_Key.csv"
            save_final_key(map_path, final_mapping)

            messagebox.showinfo(
                APP_NAME, f"{summary}\n\nMappings: {len(final_mapping)}"
            )

            # This part was entirely for my own amusement and I am an agent of chaos.

            messagebox.showinfo(
                APP_NAME,
                random.choice(
                    [
                        "File names are blinded, slay!",
                        "That was so easy dawg.",
                        "Guys, we are making real data!",
                        "It be like that sometimes.",
                        "¡Ay caramba! Could this program be any faster?",
                        "I’m Screaming!!! Nice job processing the files!",
                        "Keep slaying the day",
                        "Blinded files? Facts.",
                        "Like and Subscribe",
                        "Microtubules are the best cytoskeleton filament",
                        "Now your images are C. Elegant",
                        "Speedier than S. cerevisiae ferments!",
                        "Faster than a fly.",
                        "Ate and left no crumbs",
                        "https://www.youtube.com/watch?v=Aq5WXmQQooo&list=RDAq5WXmQQooo&start_radio=1",
                        "Never gonna give you up, never gonna let you down, never gonna run around and desert you",
                        "Oy with the poodles already",
                        "Hey kids, spelling is fun! - Taylor Swift",
                        "I cry a lot, but I am so productive – Taylor Swift",
                        "Gotta catch them all!",
                        "God, what have you done? You’re a pink pony girl.",
                        "Just cause you put syrup on somethin’ don’t make it pancakes ",
                        "Some seriously bad juju mcgumbo went down here",
                        "Y’all hear about pluto? That’s messed up",
                        "What’s new Scooby Doo?",
                        "Zoinks Scoob!",
                        "They don’t think it be like that, but it do. - Oscar Gamble",
                        "I’m not superstitious, but I am a little stitious. - Michael Scott",
                        "Leslie, I typed your symptoms into the thing up here, and it says you could have network connectivity problems.",
                        "Treat! Yo! Self! To some file name blinding",
                        "I made my money the old fashioned way: I got run over by a Lexus. – Jean Ralphio Sapperstein",
                        "I can do what I want. – Ron Swanson",
                        "Uh Oh Spaghettio",
                        "it's tough to be a bug",
                        "may the force be with you",
                        "just keep swimming",
                        "to infinity and beyond!",
                        "i solemnly swear that i am up to no good",
                        "accio blinded files!",
                        "Woohoo Big summer blowout!",
                        "Yabba dabba doo!",
                        "Surely you can't be serious? I am serious... and don't call me Shirley.",
                        "You got it dude!",
                        "Hakuna Matata!",
                        "Blinded by the light",
                        "Me? a princess? Shut up",
                        "My name is Inigo Montoya. You killed my father. Prepare to die.",
                        "untap, upkeep, girlboss",
                        "I am Groot.",
                        "Blinded your files, I have",
                        "Live long and prosper.",
                        "You're killing me smalls!",
                        "Why so serious?",
                        "You sit on a throne of lies. - Buddy the Elf",
                        "Smarter than the average bear.",
                        "I refuse to answer on the grounds that I do not know the answer. - Douglas Adams",
                        "As a boy, I wanted to be a train. Now I am one with blinding files.",
                        "I go to seek a great perhaps.",
                        "How you doin'?",
                        "D'oh!",
                        "No soup for you!",
                        "Yada yada yada.",
                        "To the batmobile!",
                        "Bazinga!",
                        "You shall not pass!",
                        "Vote for Pedro.",
                        "Life is like a box of chocolates.",
                        "I feel the need—the need for speed!",
                        "You are without a doubt the worst pirate I have ever heard of. - Captain Barbosa",
                        "Four for you, Glen Coco! You go, Glen Coco!",
                        "It's Morbin time!",
                        "Put that thing back where it came from or so help me. - Monsters Inc.",
                        "Kachow!",
                        "IT'LL QUENCH YA, IT'S THE QUENCHIEST! - Sokka, Avatar the Last Airbender",
                        "Life happens wherever you are, whether you make it or not. - Uncle Iroh",
                        "Blinding out the haters since 2026.",
                        "Blinded files: Brought to you by a confused grad student",
                        "As a child, I yearned for the mines - Jack Black, Minecraft movie",
                        "I am McLovin' it!",
                        "Get Shreked!",
                        "The risk I took was calculated, but man, am I bad at math. - Percy Jackson",
                        "With great power, comes great need to take a nap. - Nico di Angelo",
                        "Blinded files? Challenge accepted. - Barney Stinson",
                        "I scream, you scream, we all scream for blinded files!",
                        "Just keep blinding, just keep blinding. - Dory",
                        "She doesn't even go here! - Damian, Mean Girls",
                        "No one believed it would work. Especially me.",
                        "We did it Joe!",
                        "Something happened. It worked?",
                        "Got Milk?",
                        "Please don't dull my sparkle",
                        "Runs on audacity and caffiene",
                        "Live Mas",
                        "Ew, David - Alexis Rose",
                        "When life gives you lemonade, make lemons. Life will be all like 'What?!' - Phil Dunphy",
                        "Why is nobody having a good time? I specifically requested it. - Cpt Holt",
                        "Troy and Abed in the morning!",
                        "Wubba Lubba Dub Dub! - Rick Sanchez",
                        "I am the one who blinks! - Walter White",
                        "When there's trouble, you know who to call! - Teen Titans",
                        "Who you gonna call? GHOSTBUSTERS",
                        "You'll never get answers if you're afraid to ask the questions.",
                        "I'm just a gorl",
                        "Ah yes. Science.",
                        "Science? in the year of our lord 2026?",
                        "POV: you're a blinded file",
                        "what does this even mean?",
                        "If this breaks, it's a future me problem",
                        "I have no idea what I'm doing, but I'm doing it.",
                    ]
                ),
            )

        self.after(0, _ui)


if __name__ == "__main__":
    app = BlinderApp()
    app.mainloop()

    ### Previous iterations available upon request
