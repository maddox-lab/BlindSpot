import csv
import os
import uuid
from pathlib import Path
import unicodedata
import hashlib



def gen_name(file_ext: str):  # made it convertable from UUID to make it more random, 32 million options
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

    base_path = Path(base_path).expanduser()
    file = Path(file).expanduser()


    base_path_abs = base_path.absolute()
    file_path_abs = file.absolute()

    try:
        cross_comp_base = file_path_abs.relative_to(base_path_abs)
        cross_comp = cross_comp_base.as_posix()

    except ValueError:
        cross_comp = os.path.relpath(str(file_path_abs), str(base_path_abs)).replace("\\", "/")

    cross_comp_path = unicodedata.normalize("NFC", cross_comp)
    cross_comp_path = os.path.normcase(cross_comp_path)

    return cross_comp_path

def normalize_path(p):

    path_variable = str(p or "").strip()

    if not path_variable:
        return ""
    
    path_variable = unicodedata.normalize("NFC", path_variable)
    path_variable = os.path.normcase(path_variable)
    path_variable = os.path.normpath(path_variable)
    return path_variable


def safe_relpath(
    base_path, target
):  # I renamed the function halfway through and needed to convert without rewritting it
    """
    Allows the safe path to be recalled by pytesting functions

    """

    return safe_path(base_path, target)

def file_hash(path, chunk_size= 2 * 1024 * 1024):
    """
    Generates a hash for a file to allow for comparison without relying on filename or path

    """

    hash_slinging_hasher = hashlib.md5() # Live love spongebob

    try:

        file_size = os.path.getsize(path)

        if chunk_size == 0:
            return "Empty File"


        with open(path, "rb") as f:

            if file_size <= chunk_size *2:
                hash_slinging_hasher.update(f.read())
                return hash_slinging_hasher.hexdigest()
            

            hash_start = f.read(chunk_size)

            f.seek(-chunk_size, 2)

            hash_end = f.read(chunk_size)

            hash_slinging_hasher.update(hash_start)
            hash_slinging_hasher.update(hash_end)

            return hash_slinging_hasher.hexdigest()


    except Exception:

        return "Unreadable File"


    
    


def save_final_key(
    map_path: Path, final_mapping: dict[str, str]
):  # Macs did not like the original writing in v3.2 so needed to be updated
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