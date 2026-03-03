import argparse
from ..BlindSpot_config import (APP_NAME, APP_VERSION) # type: ignore



def blinder_CLI():
    """
    Runs BlindSpot in the command line without use of the GUI
    """

    CLI = argparse.ArgumentParser(description=f'{APP_NAME} version: {APP_VERSION}: A microscopy imaging name blinder for easy access')

    CLI.add_argument("--blinder", action="store_true", help="Run in the terminal (No GUI)")
    
    
    CLI.add_argument("--base_path", type=str, help="Folder where the files to be blinded are located")
    CLI.add_argument("--extension", type=str, help="File extension to target for blinding (e.g.'nd2', 'tif')")
    CLI.add_argument("--move_to_blind", action="store_true", help="Move files to a 'Blind Files' subfolder instead being in the same place as the original")
    CLI.add_argument("--clone_og", action="store_true", help="Safe mode: create blinded copies and keep originals instead of renaming/moving")
    CLI.add_argument("--include_subdirs", action="store_true", help="Include subdirectories in the blinding process")


    return CLI


def unblinder_CLI():

    """
    Runs BlindSpot in the command line without use of the GUI
    """

    CLI_U = argparse.ArgumentParser(description=f'{APP_NAME} version: {APP_VERSION}: A microscopy imaging name blinder for easy access')
   
    CLI_U.add_argument("--unblinder", action="store_true", help="Run in the terminal (No GUI)")
    
    
    CLI_U.add_argument("--base_path", type=str, help="Folder where the files to be unblinded are located")
    CLI_U.add_argument("--blinding_key", type=str, help="Location for Blinding_Key.csv file")
    CLI_U.add_argument("--move_unblind_to", type=str, help="Where the user wants the unblinded files moved to")
    CLI_U.add_argument("--overwrite", action="store_true", help="Overwrite existing files in the unblinded location if they have the same name")

    return CLI_U



   # https://grp-bio-it-workshops.embl-community.io/intermediate-python/04-argparse/index.html