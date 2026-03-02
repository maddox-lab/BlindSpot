import tkinter as tk
from tkinter import ttk
from pathlib import Path
import sys

from .BlindSpot_GUI import BlinderApp
from .BlindSpot_unblindinggui import UnblinderApp
from .BlindSpot_config import (
    APP_NAME,
    AUTHOR,
    APP_VERSION,
    LAB,
    DOI,
    SPECIAL_THANKS,
    LICENSE,
)


def resource_path(rel_path: str) -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / rel_path
    return Path(__file__).parent / rel_path


class Splash(tk.Toplevel):
    def __init__(self, master, gif_path, duration_ms=3000):
        super().__init__(master)
        self.configure(bg="white")
        self.overrideredirect(True)

        outer = tk.Frame(self, bg="white", bd=2, relief="solid")
        outer.pack(fill="both", expand=True)

        self.label = tk.Label(outer, bg="white")
        self.label.pack(padx=10, pady=10)

        self.frames = []
        self.delays = []

        try:
            from PIL import Image, ImageTk
            pil_gif = Image.open(str(gif_path))
            for i in range(pil_gif.n_frames):
                pil_gif.seek(i)
                bg = Image.new("RGBA", pil_gif.size, (255, 255, 255, 255))
                frame_img = pil_gif.convert("RGBA")
                bg.paste(frame_img, mask=frame_img.split()[3])
                tk_img = ImageTk.PhotoImage(bg.convert("RGB"))
                self.frames.append(tk_img)
                self.delays.append(pil_gif.info.get("duration", 100))
        except Exception as e:
            print(f"[Splash] Failed to load GIF: {e}")

        if not self.frames:
            self.label.config(text="(splash.gif failed to load)", fg="black", bg="white")
        else:
            self.label.configure(image=self.frames[0])

        self.update_idletasks()
        self.center_position_only()

        self.frame_index = 0
        self.animate()
        self.after(duration_ms, self.destroy)

    def animate(self):
        if self.frames:
            self.label.configure(image=self.frames[self.frame_index])
            self.label.image = self.frames[self.frame_index]
            delay = self.delays[self.frame_index]
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.after(delay, self.animate)

    def center_position_only(self):
        self.update_idletasks()
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"+{x}+{y}")


class CombinedApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.withdraw()

        splash_path = resource_path("assets/splash.gif")
        loading_screen = Splash(self, splash_path, duration_ms=3000)
        self.wait_window(loading_screen)

        self._build_ui()
        self.deiconify()

    def _build_ui(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("White.TLabel", background="white", foreground="#13294B")

        menubar = tk.Menu(self)
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        self.config(menu=menubar)

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)

        style.configure("TNotebook", background="white", borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background="#13294B",
            foreground="white",
            padding=[1, 1],
            borderwidth=0,
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", "#4B9CD3")],
            foreground=[("selected", "white")],
            padding=[("selected", [7, 4])],
        )

        blinder = BlinderApp(nb)
        unblinder = UnblinderApp(nb)

        nb.add(blinder, text="Blind")
        nb.add(unblinder, text="Unblind")

    def show_about(self):
        win = tk.Toplevel(self)
        win.title("About")
        win.resizable(False, False)
        win.transient(self)
        win.grab_set()

        pad = {"padx": 14, "pady": 8}
        container = tk.Frame(win, background="white", borderwidth=2, relief="raised")
        container.pack(fill="both", expand=True, **pad)

        ttk.Label(
            container,
            text=APP_NAME,
            style="White.TLabel",
            font=("Helvetica", 16, "bold"),
        ).pack(**pad)

        ttk.Label(container, text=f"Version {APP_VERSION}", style="White.TLabel").pack()

        ttk.Separator(container).pack(fill="x", pady=10)
        ttk.Label(container, text=f"Author: {AUTHOR}", style="White.TLabel").pack(anchor="w")
        ttk.Label(container, text=LAB, style="White.TLabel").pack(anchor="w")

        ttk.Separator(container).pack(fill="x", pady=0)
        ttk.Label(
            container,
            text=f"If used for your research, please cite using:\n{DOI}",
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


def main():
    CombinedApp().mainloop()


if __name__ == "__main__":
    main()