import tkinter as tk
import sys
from pathlib import Path
from tkinter import ttk, filedialog, messagebox
import threading
import webbrowser
import argparse

from .functions.BlindSpot_unblindingapp import run_unblinder # type: ignore
from .functions.BlindSpot_quotes import quote_generator  # type: ignore
from .BlindSpot_config import APP_NAME, APP_VERSION # type: ignore


class UnblinderApp(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)

        if getattr(sys, "frozen", False):
            resource_base = Path(sys._MEIPASS)
        else:
            resource_base = Path(__file__).parent


        self.base_var = tk.StringVar(value=str(Path.home() / "Desktop"))
        self.key_var = tk.StringVar(value="")
        self.restore_var = tk.StringVar(value="")
        self.overwrite_var = tk.BooleanVar(value=False)

        self.status_var = tk.StringVar(value="Ready.")
        self.running = False

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Blue.TLabel", background="#13294B", foreground="white")
        style.configure("Blue.TButton", background="#13294B", foreground="white")
        style.configure("LiteBlue.TButton", background="#4B9CD3", foreground="white")
        style.configure("Blue.TCheckbutton", background="#13294B", foreground="white")
        style.layout("Blue.TProgressbar", style.layout("Horizontal.TProgressbar"))
        style.configure(
            "Blue.TProgressbar",
            background="#13294B",
            troughcolor="#4B9CD3",
            bordercolor="black",
        )

        style.configure("White.TLabel", background="white")

        outer_frame = tk.Frame(
            self, borderwidth=0, relief="solid", bg="#4B9CD3"
        )  # outer frame for styling
        self.outer = outer_frame
        self.outer.pack(fill="both", expand=True)

        pad = {"padx": 10, "pady": 10}

        frm = tk.Frame(self.outer, background="white", relief="raised")
        frm.pack(fill="both", expand=True, **pad)

        row1 = tk.Frame(frm, bg="#13294B", borderwidth=4, relief="raised")
        row1.pack(fill="x", **pad)
        ttk.Label(row1, text="Base folder:", style="Blue.TLabel").pack(side="left")
        self.base_entry = ttk.Entry(row1, textvariable=self.base_var)
        self.base_entry.pack(side="left", fill="x", expand=True, padx=8)
        ttk.Button(
            row1, text="Browse...", style="LiteBlue.TButton", command=self.browse_base
        ).pack(side="left", padx=8)

        row2 = tk.Frame(frm, bg="#13294B", borderwidth=4, relief="raised")
        row2.pack(fill="x", **pad)
        ttk.Label(row2, text="Blinding Key CSV:", style="Blue.TLabel").pack(side="left")
        self.key_entry = ttk.Entry(row2, textvariable=self.key_var)
        self.key_entry.pack(side="left", fill="x", expand=True, padx=8)
        ttk.Button(
            row2, text="Browse...", style="LiteBlue.TButton", command=self.browse_key
        ).pack(side="left", padx=8)

        row3 = tk.Frame(frm, bg="#13294B", borderwidth=4, relief="raised")
        row3.pack(fill="x", **pad)
        ttk.Label(row3, text="Move unblind to:", style="Blue.TLabel").pack(side="left")
        self.restore_entry = ttk.Entry(row3, textvariable=self.restore_var)
        self.restore_entry.pack(side="left", fill="x", expand=True, padx=8)
        ttk.Button(
            row3,
            text="Browse...",
            style="LiteBlue.TButton",
            command=self.browse_restore,
        ).pack(side="left", padx=8)

        options = tk.Frame(frm, bg="#13294B", bd=2, relief="raised")
        options.pack(fill="x", **pad)
        ttk.Checkbutton(
            options,
            text="Overwrite if original filename exists",
            variable=self.overwrite_var,
            style="Blue.TCheckbutton",
        ).pack(anchor="w", padx=10, pady=6)

        prog = ttk.Frame(frm)
        prog.pack(fill="x", **pad)
        self.pbar = ttk.Progressbar(prog, style="Blue.TProgressbar", mode="determinate")
        self.pbar.pack(fill="x", expand=True)

        self.status_lbl = ttk.Label(
            frm, style="Blue.TLabel", textvariable=self.status_var, wraplength=650
        )
        self.status_lbl.pack(fill="x", **pad)

        btns = ttk.Frame(frm, style="White.TLabel")
        btns.pack(fill="x", **pad)

        self.stop_event = threading.Event()

        self.run_btn = ttk.Button(
            btns, text="Unblind", style="Blue.TButton", command=self.on_run
        )
        self.run_btn.pack(side="left")
        ttk.Button(btns, text="Stop", style="Blue.TButton", command=lambda: self.stop_event.set()).pack(
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


        self._sync_defaults()

    def _sync_defaults(self):
        base = Path(self.base_var.get()).expanduser()

        if not self.key_var.get():
            self.key_var.set(str(base / "Blinding_Key.csv"))

        if not self.restore_var.get():
            self.restore_var.set(str(base))

    def browse_base(self):
        folder = filedialog.askdirectory(initialdir=self.base_var.get())
        if folder:
            self.base_var.set(folder)
            self._sync_defaults()

    def browse_key(self):
        initial = (
            str(Path(self.key_var.get()).parent)
            if self.key_var.get()
            else self.base_var.get()
        )
        f = filedialog.askopenfilename(
            initialdir=initial,
            title="Select Blinding_Key.csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if f:
            self.key_var.set(f)

    def browse_restore(self):
        folder = filedialog.askdirectory(
            initialdir=self.restore_var.get() or self.base_var.get()
        )
        if folder:
            self.restore_var.set(folder)

    def on_run(self):

        self.stop_event.clear()

        if self.running:
            return

        base = Path(self.base_var.get()).expanduser().resolve()
        key = Path(self.key_var.get()).expanduser().resolve()
        restore = Path(self.restore_var.get()).expanduser().resolve()
        overwrite = bool(self.overwrite_var.get())

        if not base.exists():
            messagebox.showerror("Error", f"Base folder does not exist:\n{base}")
            return

        if not key.exists():
            messagebox.showerror("Error", f"Key CSV does not exist:\n{key}")
            return

        self.running = True
        self.run_btn.configure(state="disabled")
        self.status_var.set("Starting...")
        self.pbar["value"] = 0
        self.pbar["maximum"] = 1

        def worker():
            try:
                result = run_unblinder(
                base_path=base,
                key_csv_path=key,
                restore_folder=restore,
                overwrite=overwrite,
                progress=self.progress_update,
                total=None,
            )
                self.finished(result["summary"])
            except Exception as e:
                self.finished(f"Error: {e}")

        threading.Thread(target=worker, daemon=True).start()

    def progress_update(self, done, total, msg):

        if self.stop_event.is_set():
                raise RuntimeError("Stopped by user") 
        
        def _ui():
            
            
            self.pbar["maximum"] = max(int(total or 1), 1)
            self.pbar["value"] = int(done or 0)
            self.status_var.set(f"{msg} ({done}/{total})")

        self.after(0, _ui)

    def finished(self, summary_text):
        def _ui():
            self.running = False
            self.run_btn.configure(state="normal")
            self.status_var.set("Finished")
            self.pbar["value"] = self.pbar["maximum"]

            messagebox.showinfo(APP_NAME, summary_text)

            try:
                messagebox.showinfo(APP_NAME, quote_generator())
            except Exception:
                pass

        self.after(0, _ui)


if __name__ == "__main__":
    app = UnblinderApp()
    app.mainloop()