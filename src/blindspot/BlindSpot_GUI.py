import random
import sys
import threading
import webbrowser
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from .BlindSpot_config import (APP_NAME, APP_VERSION, AUTHOR, LAB, LINK, DOI, SPECIAL_THANKS, LICENSE) # type: ignore
from .functions.BlindSpot_blindingcode import run_blinder  # type: ignore
from .functions.BlindSpot_core import save_final_key # type: ignore
from .functions.BlindSpot_quotes import quote_generator # type: ignore


class BlinderApp(tk.Frame):
    """
    Gui application class for the BlindSpot blinding tool, built with tkinter.
    """

    def __init__(self, master=None):

        super().__init__(master)

        if getattr(sys, "frozen", False):
            base_path = Path(sys._MEIPASS)

        else:
            base_path = Path(__file__).parent

        # GO TARHEELS (everything is Carolina Blue because of course it is)

        outer_frame = tk.Frame(
            self, borderwidth=0, relief="solid", bg="#4B9CD3"
        )  # outer frame for styling
        self.outer = outer_frame
        self.outer.pack(fill="both", expand=True)

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
        self.clone_var = tk.BooleanVar(value=True)
        self.subdirs_var = tk.BooleanVar(value=True)

        self.status_var = tk.StringVar(value="Ready.")
        self.running = False
        self.stop_event = threading.Event()

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
        ttk.Label(container, text=f"Developed by {AUTHOR}", style="White.TLabel").pack(
            anchor="w"
        )
        ttk.Label(container, text=LAB, style="White.TLabel").pack(anchor="w")

        ttk.Separator(container).pack(fill="x", pady = 10)
        ttk.Label(container, text=f"Link to repository: {LINK}", style="White.TLabel").pack(
            anchor="w" )

        ttk.Separator(container).pack(fill="x", pady=10)
        ttk.Label(
            container,
            text=f"If used for your research, please cite using:\n{DOI} or the CIFF file in the repository",
            style="White.TLabel",
        ).pack(anchor="w")

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

        ttk.Label(row2, text="File type (extension):", style="Blue.TLabel").pack(side="left")


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
        ttk.Button(btns, text="Stop", style="Blue.TButton", command=lambda: self.stop_event.set()).pack(
            side="right")

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
        self.stop_event.clear()

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
                stop_event=self.stop_event, 
                progress=self.progress_update,
                finished=self.finished,
            ), # allows for thread to update the GUI with progress and final results without freezing the interface
            daemon=True,
        )
        t.start()

    def progress_update(self, done, total, msg):
        """

        Updates the progress bar and status message during the blinding process.
        """
        if self.stop_event.is_set():
            return
    
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

            # This part was entirely for my own amusement. I do not own these quotes

            messagebox.showinfo(APP_NAME, quote_generator())

        self.after(0, _ui)