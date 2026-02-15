import re
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from BlindSpot3_2 import (gen_name, safe_path)

def test_gen_name():

    """
    Test the gen_name function to ensure it generates a valid filename with the correct extension

    """
    out = gen_name("nd2")
    assert out.endswith(".nd2")
    name, dot, ext = out.partition(".")
    assert len(name) == 8
    assert dot == "."
    assert ext == "nd2"
    assert re.fullmatch(r"^[a-z0-9]{8}\.nd2$", out)




def test_relpath(tmp_path):

    """
    Test the safe_path function to ensure it correctly computes the correct relative path

    
    """
    
    dir = tmp_path
    new_dir = tmp_path/"subdir"/ "file.nd2"

    new_dir.parent.mkdir(parents=True, exist_ok=True)
    new_dir.write_text("test")

    output = safe_path(dir, new_dir)
    assert safe_path(dir, new_dir).replace("\\", "/") == "subdir/file.nd2"



def test_path_outside(tmp_path):

    """
    Test the safe_path function to ensure it correctly identifies when a path is outside the base directory


    """

    dir = tmp_path
    new_dir = tmp_path.parent / "file.nd2"

    new_dir.write_text("Incorrect")

    output = safe_path(dir, new_dir)

    assert output
    assert output.startswith("..") or output.startswith("../") or output.startswith("..\\") # Checks if the output is outside base directory




