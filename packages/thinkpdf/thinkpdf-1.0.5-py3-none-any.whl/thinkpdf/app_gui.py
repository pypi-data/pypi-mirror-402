"""
thinkpdf GUI - Modern desktop application for PDF to Markdown conversion.

Features:
- Modern dark/light theme with CustomTkinter
- Drag and drop support
- Progress tracking
- Quality selection
- Batch processing
- Preview panel
"""

from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import List
from tkinter import filedialog, messagebox
import tkinter as tk

try:
    import windnd

    HAS_WINDND = True
except ImportError:
    HAS_WINDND = False

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES

    HAS_TKDND = True
except ImportError:
    HAS_TKDND = False

try:
    import customtkinter as ctk

    HAS_CTK = True
except ImportError:
    HAS_CTK = False
    ctk = None

try:
    from PIL import Image

    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class CTkDnD(ctk.CTk if HAS_CTK else object):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def drop_target_register(self, dndtype="DND_Files"):
        pass

    def dnd_bind(self, sequence, func, add=None):
        pass


__version__ = "1.0.0"

from .core.converter import PDFConverter, ConversionOptions
from .cache.cache_manager import CacheManager
from .logger import logger


COLORS = {
    "dark": {
        "bg": "#1a1a1a",
        "fg": "#f5f5f5",
        "accent": "#f97316",
        "accent_hover": "#fb923c",
        "secondary": "#292524",
        "success": "#22c55e",
        "error": "#ef4444",
        "border": "#f97316",
    },
    "light": {
        "bg": "#fffbeb",
        "fg": "#1c1917",
        "accent": "#ea580c",
        "accent_hover": "#f97316",
        "secondary": "#fef3c7",
        "success": "#22c55e",
        "error": "#ef4444",
        "border": "#ea580c",
    },
}


class thinkpdfApp:
    """Main application window."""

    def __init__(self):
        if not HAS_CTK:
            self._run_fallback()
            return

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.root = CTkDnD() if HAS_TKDND else ctk.CTk()
        self.root.title("thinkpdf - PDF to Markdown Converter")
        self.root.geometry("700x550")
        self.root.minsize(600, 500)

        self.input_files: List[Path] = []
        self.output_folder: Path = None
        self.is_converting = False
        self.cache = CacheManager()

        self._build_ui()

        self._setup_dnd()

    def _run_fallback(self):
        """Run a simple fallback if CustomTkinter is not available."""
        root = tk.Tk()
        root.title("thinkpdf")
        root.geometry("500x300")

        label = tk.Label(
            root,
            text="thinkpdf requires CustomTkinter for the GUI.\n\n"
            "Install it with:\n"
            "pip install customtkinter\n\n"
            "Or use the CLI:\n"
            "thinkpdf input.pdf",
            font=("Arial", 12),
            padx=20,
            pady=20,
        )
        label.pack(expand=True)

        root.mainloop()

    def _build_ui(self):
        """Build the main UI."""
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self._build_header(main_frame)

        self._build_drop_zone(main_frame)

        self._build_output_folder(main_frame)

        self._build_file_list(main_frame)

        self._build_progress(main_frame)

        self._build_buttons(main_frame)

        self._build_status(main_frame)

    def _build_header(self, parent):
        """Build the header section."""
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", pady=(0, 15))

        if HAS_PIL and HAS_CTK:
            logo_path = Path(__file__).parent.parent / "logo.png"
            if logo_path.exists():
                try:
                    logo_img = ctk.CTkImage(
                        light_image=Image.open(logo_path),
                        dark_image=Image.open(logo_path),
                        size=(40, 40),
                    )
                    logo_label = ctk.CTkLabel(header, image=logo_img, text="")
                    logo_label.pack(side="left", padx=(0, 10))
                except Exception:
                    pass

        title = ctk.CTkLabel(
            header,
            text="thinkpdf",
            font=ctk.CTkFont(size=28, weight="bold"),
        )
        title.pack(side="left")

        self.theme_var = ctk.StringVar(value="dark")
        theme_btn = ctk.CTkSegmentedButton(
            header,
            values=["Light", "Dark"],
            command=self._toggle_theme,
            width=150,
            selected_color="#f97316",
            selected_hover_color="#ea580c",
        )
        theme_btn.set("Dark")
        theme_btn.pack(side="right")

    def _build_drop_zone(self, parent):
        """Build the file selection button."""
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkButton(
            btn_frame,
            text="Select PDFs",
            width=150,
            height=35,
            fg_color="#f97316",
            hover_color="#ea580c",
            command=self._browse_files,
        ).pack(side="left")

    def _build_output_folder(self, parent):
        """Build the output folder selector."""
        output_frame = ctk.CTkFrame(parent, fg_color="transparent")
        output_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(output_frame, text="Save to:").pack(side="left", padx=(0, 10))

        self.output_label = ctk.CTkLabel(
            output_frame,
            text="Same folder as PDF",
            text_color="gray",
        )
        self.output_label.pack(side="left", anchor="w")

        ctk.CTkButton(
            output_frame,
            text="Choose Output Folder",
            width=160,
            fg_color="#f97316",
            hover_color="#ea580c",
            command=self._select_output_folder,
        ).pack(side="left", padx=(10, 0))

    def _select_output_folder(self):
        """Open folder dialog to select output folder."""
        folder = filedialog.askdirectory(title="Select output folder")
        if folder:
            self.output_folder = Path(folder)
            self.output_label.configure(
                text=str(self.output_folder), text_color="white"
            )

    def _build_file_list(self, parent):
        """Build the file list section."""
        list_frame = ctk.CTkFrame(parent, height=150)
        list_frame.pack(fill="x", pady=(0, 10))
        list_frame.pack_propagate(False)

        list_header = ctk.CTkFrame(list_frame, fg_color="transparent")
        list_header.pack(fill="x", padx=15, pady=(10, 5))

        ctk.CTkLabel(
            list_header,
            text="Files to Convert",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(side="left")

        clear_btn = ctk.CTkButton(
            list_header,
            text="Clear All",
            width=80,
            height=28,
            fg_color="#f97316",
            hover_color="#ea580c",
            command=self._clear_files,
        )
        clear_btn.pack(side="right")

        self.file_list = ctk.CTkScrollableFrame(list_frame, height=120)
        self.file_list.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        self.file_widgets: List[ctk.CTkFrame] = []

        self.empty_label = ctk.CTkLabel(
            self.file_list,
            text="No files added yet",
            text_color="gray",
        )
        self.empty_label.pack(pady=15)

    def _build_progress(self, parent):
        """Build the progress section."""
        progress_frame = ctk.CTkFrame(parent, fg_color="transparent")
        progress_frame.pack(fill="x", pady=(0, 10))

        self.progress_label = ctk.CTkLabel(
            progress_frame,
            text="Ready to convert",
        )
        self.progress_label.pack(anchor="w")

        self.progress_bar = ctk.CTkProgressBar(
            progress_frame,
            progress_color="#f97316",
        )
        self.progress_bar.pack(fill="x", pady=(5, 0))
        self.progress_bar.set(0)

    def _build_buttons(self, parent):
        """Build the action buttons."""
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(10, 0))

        self.convert_btn = ctk.CTkButton(
            btn_frame,
            text="Convert All",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            fg_color="#f97316",
            hover_color="#ea580c",
            command=self._start_conversion,
        )
        self.convert_btn.pack(side="left", expand=True, fill="x", padx=(0, 10))

        self.open_folder_btn = ctk.CTkButton(
            btn_frame,
            text="Open Folder",
            height=40,
            width=120,
            fg_color="transparent",
            border_width=2,
            command=self._open_output_folder,
        )
        self.open_folder_btn.pack(side="right")

    def _build_status(self, parent):
        """Build the status bar."""
        status_frame = ctk.CTkFrame(parent, fg_color="transparent", height=30)
        status_frame.pack(fill="x", pady=(10, 0))

        self.status_label = ctk.CTkLabel(
            status_frame,
            text=f"thinkpdf v{__version__} | Ready",
            text_color="gray",
        )
        self.status_label.pack(side="left")

    def _setup_dnd(self):
        """Setup drag and drop for Windows."""
        if not HAS_TKDND:
            return

        def on_drop(event):
            files = self.root.tk.splitlist(event.data)
            for f in files:
                path = Path(f)
                if path.suffix.lower() == ".pdf":
                    self._add_file(path)

        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind("<<Drop>>", on_drop)

    def _browse_files(self, event=None):
        """Open file browser to select PDFs."""
        files = filedialog.askopenfilenames(
            title="Select PDF files",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        )

        if files:
            for f in files:
                self._add_file(Path(f))

    def _add_file(self, file_path: Path):
        """Add a file to the list."""
        if file_path in self.input_files:
            return

        self.input_files.append(file_path)

        self.empty_label.pack_forget()

        file_frame = ctk.CTkFrame(self.file_list)
        file_frame.pack(fill="x", pady=2)

        ctk.CTkLabel(
            file_frame,
            text=f"📄 {file_path.name}",
            anchor="w",
        ).pack(side="left", padx=10, pady=8)

        size_mb = file_path.stat().st_size / (1024 * 1024)
        ctk.CTkLabel(
            file_frame,
            text=f"{size_mb:.1f} MB",
            text_color="gray",
        ).pack(side="right", padx=10)

        self.file_widgets.append(file_frame)
        self._update_status()

    def _clear_files(self):
        """Clear all files from the list."""
        self.input_files.clear()

        for widget in self.file_widgets:
            widget.destroy()
        self.file_widgets.clear()

        self.empty_label.pack(pady=30)
        self._update_status()

    def _toggle_theme(self, value):
        """Toggle between light and dark theme."""
        if "Light" in value:
            ctk.set_appearance_mode("light")
        else:
            ctk.set_appearance_mode("dark")

    def _on_quality_change(self, value):
        """Handle quality change."""
        if "Fast" in value:
            self.quality_var.set("fast")
        elif "Maximum" in value:
            self.quality_var.set("maximum")
        else:
            self.quality_var.set("balanced")

    def _update_status(self):
        """Update the status label."""
        count = len(self.input_files)
        if count == 0:
            self.status_label.configure(text=f"thinkpdf v{__version__} | Ready")
        else:
            total_size = sum(f.stat().st_size for f in self.input_files) / (1024 * 1024)
            self.status_label.configure(
                text=f"thinkpdf v{__version__} | {count} files ({total_size:.1f} MB)"
            )

    def _start_conversion(self):
        """Start the conversion process."""
        if not self.input_files:
            messagebox.showwarning("No files", "Please add PDF files to convert.")
            return

        if self.is_converting:
            return

        self.is_converting = True
        self.convert_btn.configure(state="disabled", text="Converting...")

        thread = threading.Thread(target=self._convert_files)
        thread.start()

    def _convert_files(self):
        """Convert all files (runs in background thread)."""
        try:
            total = len(self.input_files)
            success_count = 0

            for i, pdf_path in enumerate(self.input_files):
                self.root.after(
                    0, lambda p=i, t=total: self._update_progress(p, t, pdf_path.name)
                )

                try:
                    converter = PDFConverter()
                    if self.output_folder:
                        output_path = self.output_folder / (pdf_path.stem + ".md")
                    else:
                        output_path = pdf_path.with_suffix(".md")
                    converter.convert(pdf_path, output_path=output_path)

                    success_count += 1

                except Exception as e:
                    logger.error(f"Error converting {pdf_path.name}: {e}")

            self.root.after(0, lambda: self._conversion_complete(success_count, total))

        except Exception as e:
            self.root.after(0, lambda err=e: messagebox.showerror("Error", str(err)))

        finally:
            self.is_converting = False
            self.root.after(
                0,
                lambda: self.convert_btn.configure(state="normal", text="Convert All"),
            )

    def _update_progress(self, current: int, total: int, filename: str):
        """Update progress bar and label."""
        progress = (current + 1) / total
        self.progress_bar.set(progress)
        self.progress_label.configure(
            text=f"Converting: {filename} ({current + 1}/{total})"
        )

    def _conversion_complete(self, success: int, total: int):
        """Handle conversion completion."""
        self.progress_bar.set(1.0)
        self.progress_label.configure(
            text=f"Completed: {success}/{total} files converted successfully"
        )

        if success == total:
            messagebox.showinfo(
                "Conversion Complete", f"Successfully converted {total} files!"
            )
        else:
            messagebox.showwarning(
                "Conversion Complete",
                f"Converted {success}/{total} files.\n"
                f"{total - success} files had errors.",
            )

    def _open_output_folder(self):
        """Open the output folder in file explorer."""
        if self.output_folder:
            folder = self.output_folder
        elif self.input_files:
            folder = self.input_files[0].parent
        else:
            folder = Path.home() / "Desktop"
        os.startfile(str(folder))

    def run(self):
        """Start the application."""
        if HAS_CTK:
            self.root.mainloop()


def main():
    """Entry point for the GUI."""
    app = thinkpdfApp()
    app.run()


if __name__ == "__main__":
    main()
