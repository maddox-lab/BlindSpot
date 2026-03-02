
import sys
from .BlindSpot_CLI import blinder_CLI # type: ignore
from ..BlindSpot_GUI import BlinderApp  # type: ignore
from .BlindSpot_blindingcode import run_blinder # type: ignore

if __name__ == "__main__":

    command_line = blinder_CLI()

    args, unknown = command_line.parse_known_args()


    if args.blinder:
        if not args.base_path:
            print("Error: --base_path is required when using command line mode")
            sys.exit(0)

        if not args.extension:
            print("Error: --extension is required when using command line mode")
            sys.exit(0)

        result = run_blinder(
            base_path=args.base_path,
            extension=args.extension,
            move_to_blind=args.move_to_blind,
            clone_og=args.clone_og,
            include_subdirs=args.include_subdirs,
        )

        print(result["summary"])

        sys.exit(0)
    
    app = BlinderApp()
    app.mainloop()

    ### Previous iterations available upon request
