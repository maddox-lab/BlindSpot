import os
import csv
from pathlib import Path
from .BlindSpot_journal import track_action  # type: ignore


def _get(row: dict, *keys: str) -> str:
    """Fetch first non-empty key from row (case-sensitive), stripped."""
    for k in keys:
        v = (row.get(k) or "").strip()
        if v:
            return v
    return ""


def _find_blinded_file(base_path: Path, filename: str) -> Path | None:
    """Find a blinded file by name in common locations."""
    p = base_path / filename
    if p.exists():
        return p

    p2 = base_path / "Blind Files" / filename
    if p2.exists():
        return p2

    matches = list(base_path.rglob(filename))
    return matches[0] if matches else None


def run_unblinder(
    base_path: Path,
    key_csv_path: Path,
    restore_folder: Path,
    overwrite: bool,
    progress=None,
    total=None,
):
    base_path = Path(base_path).expanduser().resolve()
    key_csv_path = Path(key_csv_path).expanduser().resolve()
    restore_folder = Path(restore_folder).expanduser().resolve()

    unblind_log = base_path / "_unblinding_log.csv"

    if not key_csv_path.exists():
        raise FileNotFoundError(f"Key file not found: {key_csv_path}")

    restore_folder.mkdir(parents=True, exist_ok=True)

    with open(key_csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    total_rows = len(rows)
    if total is None:
        total = total_rows

    done = 0
    restored = 0
    skipped_exists = 0
    skipped_missing = 0
    errors = 0

    for row in rows:
        done += 1

        # Support common header variants
        old_name = _get(row, "Old file name", "Original file name", "Original name")
        new_name = _get(row, "New file name", "Blinded file name", "Blind file name", "Blinded name")
        old_path_str = _get(row, "Old path", "Old file path", "Original path", "Original file path")

        # If key file is missing essential fields, skip
        if not old_name or not new_name:
            skipped_missing += 1
            if progress:
                progress(done, total, "Skipping row (missing name fields)")
            continue

        # Determine which name is the blinded file by checking disk
        blinded_file = _find_blinded_file(base_path, new_name)
        original_name = old_name
        blinded_name = new_name

        # If not found, try swapped (some keys swap old/new naming)
        if blinded_file is None:
            blinded_file = _find_blinded_file(base_path, old_name)
            if blinded_file is not None:
                blinded_name = old_name
                original_name = new_name

        if blinded_file is None:
            skipped_missing += 1
            track_action(
                unblind_log,
                old_path=str(base_path / blinded_name),
                dest_path=str(restore_folder / original_name),
                old_name=blinded_name,
                new_name=original_name,
                action="unblind_missing",
                message="Blinded file not found",
            )
            if progress:
                progress(done, total, f"Missing: {blinded_name}")
            continue

        # Destination: prefer full original path from key if present, else restore_folder/original_name
        dest_path = Path(old_path_str).expanduser().resolve() if old_path_str else (restore_folder / original_name)

        # If destination exists and overwrite is False, skip
        if dest_path.exists() and not overwrite:
            skipped_exists += 1
            track_action(
                unblind_log,
                old_path=str(blinded_file),
                dest_path=str(dest_path),
                old_name=blinded_name,
                new_name=original_name,
                action="unblind_skip",
                message="Original exists; not overwriting",
            )
            if progress:
                progress(done, total, f"Exists (skip): {dest_path.name}")
            continue

        try:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            os.replace(str(blinded_file), str(dest_path))
            restored += 1

            track_action(
                unblind_log,
                old_path=str(blinded_file),
                dest_path=str(dest_path),
                old_name=blinded_name,
                new_name=original_name,
                action="unblinded",
                message="File successfully unblinded",
            )
            if progress:
                progress(done, total, f"Restored: {dest_path.name}")

        except Exception as e:
            errors += 1
            track_action(
                unblind_log,
                old_path=str(blinded_file),
                dest_path=str(dest_path),
                old_name=blinded_name,
                new_name=original_name,
                action="unblind_error",
                message=f"{type(e).__name__}: {e}",
            )
            if progress:
                progress(done, total, f"Error: {dest_path.name}")

    summary = (
        f"Unblinding complete\n\n"
        f"Base: {base_path}\n"
        f"Key: {key_csv_path}\n"
        f"Restore folder: {restore_folder}\n"
        f"Total rows: {total_rows}\n"
        f"Restored: {restored}\n"
        f"Skipped (exists): {skipped_exists}\n"
        f"Missing (skipped): {skipped_missing}\n"
        f"Errors: {errors}\n"
        f"Log: {unblind_log}"
    )

    return {
        "restored": restored,
        "skipped": skipped_exists + skipped_missing,
        "missing": skipped_missing,
        "errors": errors,
        "total": total_rows,
        "summary": summary,
    }