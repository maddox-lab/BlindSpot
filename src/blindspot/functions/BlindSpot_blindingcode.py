import os
import shutil
import time
import threading
from pathlib import Path
from .BlindSpot_journal import (blinding_key_path, recover_from_journal, build_journal_state, track_action, where_file_go, hashes_from_journal)  # type: ignore
from .BlindSpot_core import safe_path, normalize_path, file_hash  # type: ignore



def run_blinder(
    base_path,
    extension,
    move_to_blind,
    clone_og,
    include_subdirs=False,
    stop_event=None, 
    progress=None,
    finished=None,
    **kwargs,  # makes tests resilient to extra args
    ):
    """
    The main function to run the blinding process on a given directory with user specified options

    """

    

    try:

        if stop_event is None:
            stop_event = threading.Event()


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

        already_blinded = blinding_key_path(journal_path)  

       


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

            if already_blinded:  # returns that files have already been blinded
                msg = (
                    f"No unblinded files found with the extension {ext}. \n"
                    f"Everything has already been blinded. Total number of blinded files already recorded (any extension): {len(already_blinded)}"  # Too lazy to add sort by file type
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

            if stop_event.is_set():
                final_mapping = blinding_key_path(journal_path)
                if finished:
                    finished("Cancelled by user.", final_mapping)
                return {"mapping": final_mapping, "summary": "Cancelled by user."}


            t0 = time.perf_counter()
            full_old = normalize_path(str(fpath.resolve()))

            rel = safe_path(base_path, fpath)


            if full_old in already_blinded:
                skipped_done += 1
                done += 1
                if progress:
                    progress(done, total, f"Already mapped: {rel}")
                continue


            info = state.get(full_old)


            if info and info.get("done"):
                skipped_done += 1
                done += 1
                if progress:
                    progress(done, total, f"Already done: {rel}")
                continue
            

            out_dir = blind_folder if move_to_blind else fpath.parent

            file_hash_slinging_hasher = file_hash(fpath)
            if file_hash_slinging_hasher in ("Empty File", "Unreadable File"):
                skipped_error += 1
                done += 1
                if progress:
                    progress(done, total, f"Error with file: {rel}")
                continue


            txtid, dest_str, blind_name = where_file_go(
                journal_path,
                full_old,
                fpath.name,
                out_dir,
                ext=fpath.suffix,
                entries=state,
                file_hash_value=file_hash_slinging_hasher,
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
                    message=file_hash_slinging_hasher,
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
                        message=file_hash_slinging_hasher,
                    )

                else:  # Just replaces no clone.

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
                        message=file_hash_slinging_hasher,
                    )

                track_action(
                    journal_path,
                    TxtID=txtid,
                    old_path=full_old,
                    dest_path=dest_str,
                    old_name=fpath.name,
                    new_name=blind_name,
                    action="keyed",
                    message=file_hash_slinging_hasher,
                )

                track_action(
                    journal_path,
                    TxtID=txtid,
                    old_path=full_old,
                    dest_path=dest_str,
                    old_name=fpath.name,
                    new_name=blind_name,
                    action="done",
                    message=file_hash_slinging_hasher,
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