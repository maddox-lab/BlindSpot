import os
import sys
from pathlib import Path


if os.name == "nt" and len(sys.argv) == 1:
    import ctypes
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

from .functions.BlindSpot_CLI import blinder_CLI, unblinder_CLI  # type: ignore
from .BlindSpot_MainGUI import CombinedApp  # type: ignore
from .functions.BlindSpot_blindingcode import run_blinder  # type: ignore
from .functions.BlindSpot_unblindingapp import run_unblinder
from .functions.BlindSpot_core import save_final_key
from .BlindSpot_config import LAB, APP_VERSION


def main():
    argv = sys.argv[1:]

    if "--blinder" in argv:
        parser = blinder_CLI()
        args, _ = parser.parse_known_args(argv)

        if not args.base_path:
            parser.error("--base_path is required when using --blinder")
        if not args.extension:
            parser.error("--extension is required when using --blinder")

        result = run_blinder(
            base_path=args.base_path,
            extension=args.extension,
            move_to_blind=args.move_to_blind,
            clone_og=args.clone_og,
            include_subdirs=args.include_subdirs,
        )
        print(result["summary"])
        
        mapping = result["mapping"]
        key_path = Path(args.base_path) / "Blinding_Key.csv"
        
        save_final_key(key_path, mapping)
        print(f"Blinding key saved to: {key_path}")

        return

    if "--unblinder" in argv:
        parser = unblinder_CLI()
        args, _ = parser.parse_known_args(argv)

        if not args.base_folder:
            parser.error("--base_folder is required when using --unblinder")
        if not args.blinding_key:
            parser.error("--blinding_key is required when using --unblinder")

        result = run_unblinder(
            base_path=args.base_path,
            key_csv_path=args.blinding_key,
            restore_folder=args.move_unblind_to or args.base_path,
            overwrite=args.overwrite,
            progress=None,
            total=None,
        )
        
        print(result["summary"])

        return
    
    if "--help" in argv or "-h" in argv or not argv:
        print(f"""
              BlindSpot — The Amy Shaub Maddox Lab
              Version: {APP_VERSION}

              Command Line Usage:
              
              blindspot                          Open the GUI
              blindspot --blinder [options]      Blind files from the command line
              blindspot --unblinder [options]    Unblind files from the command line
              
              Blinder options:
                --base_path PATH       Folder containing files to blinded (required)
                --extension EXT        File extension to blind, e.g. nd2 (required)
                --move_to_blind        Move files to a 'Blind Files' folder
                --clone_og             Copy originals before blinding (safe mode) *Recommended* 
                --include_subdirs      Include subfolders within specified directory

            Unblinder options:
                --base_folder PATH     Folder containing blinded files (required)
                --blinding_key PATH    Path to Blinding_Key.csv (required)
                --move_unblind_to PATH Destination folder for unblinded files
                --overwrite            Overwrite existing files

            
              
            Examples:
                blindspot --blinder --base_path C:/data --extension nd2 --clone_og
                blindspot --unblinder --base_folder C:/data --blinding_key C:/data/Blinding_Key.csv
            """)
        

        if "--help" in argv or "-h" in argv:
            return  

    # GUI
    app = CombinedApp()
    app.mainloop()


if __name__ == "__main__":
    main()