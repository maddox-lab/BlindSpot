from blindspot.functions.BlindSpot_blindingcode import run_blinder
from blindspot.functions.BlindSpot_unblindingapp import run_unblinder


def main():
    from .BlindSpot_MainGUI import main as gui_main 
    gui_main()