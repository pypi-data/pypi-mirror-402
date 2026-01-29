"""Graphical User Interface for MusicList for Soundiiz with i18n support."""

import os
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import List, Optional

from .duplicate_detector import DuplicateDetector
from .exporter import get_exporter
from .extractor import MusicFileExtractor
from .i18n import I18n, LANGUAGE_NAMES


class MusicListGUI:
    """GUI Application for MusicList for Soundiiz with i18n support."""

    def __init__(self, root):
        """Initialize the GUI."""
        self.root = root
        self.root.geometry("850x750")
        self.root.resizable(True, True)
        
        # Initialize i18n
        self.i18n = I18n("en")  # Default language
        
        # Variables
        self.input_dirs: List[str] = []
        self.output_file = tk.StringVar(value="output.csv")
        self.export_format = tk.StringVar(value="csv")
        self.recursive = tk.BooleanVar(value=True)
        self.detect_duplicates = tk.BooleanVar(value=False)
        self.remove_duplicates = tk.BooleanVar(value=False)
        self.duplicate_strategy = tk.StringVar(value="keep_first")
        self.max_songs_per_file = tk.IntVar(value=200)
        self.current_language = tk.StringVar(value="en")
        self.processing = False
        
        # Setup UI
        self._setup_ui()
        self._update_texts()
        
    def _setup_ui(self):
        """Set up the user interface."""
        # Title frame
        title_frame = ttk.Frame(self.root, padding="10")
        title_frame.pack(fill=tk.X)
        
        # Title and subtitle
        self.title_label = ttk.Label(
            title_frame,
            text="🎵 MusicList for Soundiiz",
            font=("Arial", 20, "bold")
        )
        self.title_label.pack()
        
        self.subtitle_label = ttk.Label(
            title_frame,
            text="Extract music metadata and create playlists",
            font=("Arial", 10)
        )
        self.subtitle_label.pack()
        
        # Language selector
        lang_frame = ttk.Frame(title_frame)
        lang_frame.pack(pady=(5, 0))
        
        self.lang_label = ttk.Label(lang_frame, text="Language:")
        self.lang_label.pack(side=tk.LEFT, padx=(0, 5))
        
        lang_combo = ttk.Combobox(
            lang_frame,
            textvariable=self.current_language,
            values=list(LANGUAGE_NAMES.keys()),
            state="readonly",
            width=15
        )
        lang_combo.pack(side=tk.LEFT)
        lang_combo.bind("<<ComboboxSelected>>", self._change_language)
        
        # Format display names
        def format_func(code):
            return LANGUAGE_NAMES.get(code, code)
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Input directories section
        self._create_input_section(main_frame)
        
        # Output section
        self._create_output_section(main_frame)
        
        # Options section
        self._create_options_section(main_frame)
        
        # Progress section
        self._create_progress_section(main_frame)
        
        # Buttons section
        self._create_buttons_section(main_frame)
        
        # Status bar
        self._create_status_bar()
        
    def _create_input_section(self, parent):
        """Create input directories section."""
        self.input_frame = ttk.LabelFrame(parent, text="📁 Input Directories", padding="10")
        self.input_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Listbox with scrollbar
        list_frame = ttk.Frame(self.input_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.dir_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            selectmode=tk.EXTENDED,
            height=2
        )
        self.dir_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.dir_listbox.yview)
        
        # Hint label
        self.hint_label = ttk.Label(
            self.input_frame,
            text="💡 Tip: Click 'Add Directory' or drag folders here",
            font=("Arial", 9, "italic"),
            foreground="gray"
        )
        self.hint_label.pack(pady=(5, 0))
        
        # Buttons
        btn_frame = ttk.Frame(self.input_frame)
        btn_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.add_btn = ttk.Button(btn_frame, text="Add Directory", command=self._add_directory)
        self.add_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.remove_btn = ttk.Button(btn_frame, text="Remove Selected", command=self._remove_directory)
        self.remove_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.clear_btn = ttk.Button(btn_frame, text="Clear All", command=self._clear_directories)
        self.clear_btn.pack(side=tk.LEFT)
        
    def _create_output_section(self, parent):
        """Create output file section."""
        self.output_frame = ttk.LabelFrame(parent, text="📄 Output", padding="10")
        self.output_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Output file
        file_frame = ttk.Frame(self.output_frame)
        file_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.output_label = ttk.Label(file_frame, text="Output File:")
        self.output_label.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Entry(file_frame, textvariable=self.output_file).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.browse_btn = ttk.Button(file_frame, text="Browse", command=self._browse_output)
        self.browse_btn.pack(side=tk.LEFT)
        
        # Format and max songs
        format_frame = ttk.Frame(self.output_frame)
        format_frame.pack(fill=tk.X)
        
        self.format_label = ttk.Label(format_frame, text="Format:")
        self.format_label.pack(side=tk.LEFT, padx=(0, 5))
        
        for fmt in ["csv", "json", "m3u", "txt"]:
            ttk.Radiobutton(
                format_frame,
                text=fmt.upper(),
                variable=self.export_format,
                value=fmt
            ).pack(side=tk.LEFT, padx=(0, 10))
        
        # Max songs per file
        max_songs_frame = ttk.Frame(self.output_frame)
        max_songs_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.max_songs_label = ttk.Label(max_songs_frame, text="Max songs per file:")
        self.max_songs_label.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Spinbox(
            max_songs_frame,
            from_=10,
            to=10000,
            textvariable=self.max_songs_per_file,
            width=10
        ).pack(side=tk.LEFT)
        
    def _create_options_section(self, parent):
        """Create options section."""
        self.options_frame = ttk.LabelFrame(parent, text="⚙️ Options", padding="10")
        self.options_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Recursive scanning
        self.recursive_check = ttk.Checkbutton(
            self.options_frame,
            text="Scan subdirectories recursively",
            variable=self.recursive
        )
        self.recursive_check.pack(anchor=tk.W)
        
        # Duplicate detection
        self.detect_dup_check = ttk.Checkbutton(
            self.options_frame,
            text="Detect duplicates",
            variable=self.detect_duplicates,
            command=self._toggle_duplicate_options
        )
        self.detect_dup_check.pack(anchor=tk.W)
        
        # Remove duplicates
        self.remove_dup_check = ttk.Checkbutton(
            self.options_frame,
            text="Remove duplicates",
            variable=self.remove_duplicates,
            state=tk.DISABLED
        )
        self.remove_dup_check.pack(anchor=tk.W, padx=(20, 0))
        
        # Duplicate strategy
        strategy_frame = ttk.Frame(self.options_frame)
        strategy_frame.pack(fill=tk.X, padx=(40, 0))
        
        self.strategy_label = ttk.Label(strategy_frame, text="Strategy:")
        self.strategy_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.strategy_combo = ttk.Combobox(
            strategy_frame,
            textvariable=self.duplicate_strategy,
            values=["keep_first", "keep_last", "keep_shortest_path"],
            state="disabled",
            width=20
        )
        self.strategy_combo.pack(side=tk.LEFT)
        
    def _create_progress_section(self, parent):
        """Create progress section."""
        self.progress_frame = ttk.LabelFrame(parent, text="📊 Progress", padding="10")
        self.progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.status_label = ttk.Label(self.progress_frame, text="Ready")
        self.status_label.pack(anchor=tk.W)
        
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            mode='determinate',
            length=300,
            maximum=100
        )
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
        
        # Time estimation label
        self.time_label = ttk.Label(self.progress_frame, text="")
        self.time_label.pack(anchor=tk.W, pady=(2, 0))
        
        self.log_text = tk.Text(self.progress_frame, height=5, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        log_scrollbar = ttk.Scrollbar(self.log_text)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=log_scrollbar.set)
        log_scrollbar.config(command=self.log_text.yview)
        
    def _create_buttons_section(self, parent):
        """Create action buttons section."""
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.process_btn = ttk.Button(
            btn_frame,
            text="🚀 Process Files",
            command=self._process_files
        )
        self.process_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.clear_log_btn = ttk.Button(btn_frame, text="Clear Log", command=self._clear_log)
        self.clear_log_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.help_btn = ttk.Button(btn_frame, text="Help", command=self._show_help)
        self.help_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.about_btn = ttk.Button(btn_frame, text="About", command=self._show_about)
        self.about_btn.pack(side=tk.LEFT)
        
    def _create_status_bar(self):
        """Create status bar."""
        self.status_bar = ttk.Label(
            self.root,
            text="Ready to process music files",
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def _change_language(self, event=None):
        """Change application language."""
        self.i18n.set_language(self.current_language.get())
        self._update_texts()
        
    def _update_texts(self):
        """Update all UI texts according to current language."""
        _ = self.i18n
        
        # Window title
        self.root.title(_.get("window_title"))
        self.title_label.config(text="🎵 " + _.get("window_title"))
        self.subtitle_label.config(text=_.get("subtitle"))
        
        # Sections
        self.input_frame.config(text=_.get("input_directories"))
        self.output_frame.config(text=_.get("output"))
        self.options_frame.config(text=_.get("options"))
        self.progress_frame.config(text=_.get("progress"))
        
        # Input section
        self.add_btn.config(text=_.get("add_directory"))
        self.remove_btn.config(text=_.get("remove_selected"))
        self.clear_btn.config(text=_.get("clear_all"))
        self.hint_label.config(text=_.get("tip_add_directory"))
        
        # Output section
        self.output_label.config(text=_.get("output_file"))
        self.browse_btn.config(text=_.get("browse"))
        self.format_label.config(text=_.get("format"))
        self.max_songs_label.config(text=_.get("max_songs"))
        
        # Options
        self.recursive_check.config(text=_.get("scan_recursive"))
        self.detect_dup_check.config(text=_.get("detect_duplicates"))
        self.remove_dup_check.config(text=_.get("remove_duplicates"))
        self.strategy_label.config(text=_.get("strategy"))
        
        # Buttons
        self.process_btn.config(text=_.get("process_files"))
        self.clear_log_btn.config(text=_.get("clear_log"))
        self.help_btn.config(text=_.get("help"))
        self.about_btn.config(text=_.get("about"))
        self.lang_label.config(text=_.get("language"))
        
        # Status
        if not self.processing:
            self.status_label.config(text=_.get("ready"))
            self.status_bar.config(text=_.get("ready_to_process"))
        
    def _toggle_duplicate_options(self):
        """Toggle duplicate detection options."""
        if self.detect_duplicates.get():
            self.remove_dup_check.config(state=tk.NORMAL)
            self.strategy_combo.config(state="readonly")
        else:
            self.remove_dup_check.config(state=tk.DISABLED)
            self.strategy_combo.config(state="disabled")
            
    def _add_directory(self):
        """Add directory to input list."""
        _ = self.i18n
        directory = filedialog.askdirectory(title=_.get("add_directory"))
        if directory:
            if directory not in self.input_dirs:
                self.input_dirs.append(directory)
                self.dir_listbox.insert(tk.END, directory)
                self._log(f"{_.get('added')} {directory}")
            else:
                messagebox.showinfo(_.get("info"), _.get("already_added"))
                
    def _remove_directory(self):
        """Remove selected directories."""
        _ = self.i18n
        selection = self.dir_listbox.curselection()
        for index in reversed(selection):
            directory = self.dir_listbox.get(index)
            self.dir_listbox.delete(index)
            self.input_dirs.remove(directory)
            self._log(f"{_.get('removed')} {directory}")
            
    def _clear_directories(self):
        """Clear all directories."""
        _ = self.i18n
        self.dir_listbox.delete(0, tk.END)
        self.input_dirs.clear()
        self._log(_.get("cleared"))
        
    def _browse_output(self):
        """Browse for output file."""
        _ = self.i18n
        ext = self.export_format.get()
        filetypes = [(f"{ext.upper()} files", f"*.{ext}"), ("All files", "*.*")]
        filename = filedialog.asksaveasfilename(
            title=_.get("output_file"),
            defaultextension=f".{ext}",
            filetypes=filetypes
        )
        if filename:
            self.output_file.set(filename)
            
    def _log(self, message: str):
        """Add message to log."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        
    def _clear_log(self):
        """Clear log text."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        
    def _update_status(self, message: str):
        """Update status bar."""
        self.status_bar.config(text=message)
        
    def _process_files(self):
        """Process files in background thread."""
        _ = self.i18n
        
        if self.processing:
            messagebox.showwarning(_.get("warning"), _.get("processing_in_progress"))
            return
            
        if not self.input_dirs:
            messagebox.showerror(_.get("error"), _.get("no_input_dir"))
            return
            
        if not self.output_file.get():
            messagebox.showerror(_.get("error"), _.get("no_output_file"))
            return
            
        # Start processing in background thread
        self.processing = True
        self.process_btn.config(state=tk.DISABLED)
        self.progress_bar.start()
        
        thread = threading.Thread(target=self._do_process, daemon=True)
        thread.start()
        
    def _do_process(self):
        """Do the actual processing."""
        _ = self.i18n
        import time
        
        try:
            start_time = time.time()
            self._update_status(_.get("processing"))
            self._log("\n" + "="*50)
            self._log(_.get("starting_processing"))
            
            # Initialize extractor
            extractor = MusicFileExtractor()
            
            # Extract metadata from all directories
            all_metadata = []
            total_dirs = len(self.input_dirs)
            
            for dir_idx, directory in enumerate(self.input_dirs, 1):
                # Update progress bar
                progress_percent = (dir_idx / total_dirs) * 100
                self.progress_bar['value'] = progress_percent
                
                # Update status with progress
                status_msg = f"{_.get('processing')} ({dir_idx}/{total_dirs})"
                self.status_label.config(text=status_msg)
                
                self._log(f"{_.get('scanning')} {directory}")
                metadata_list = extractor.extract_all(
                    directory=directory,
                    recursive=self.recursive.get()
                )
                all_metadata.extend(metadata_list)
                self._log(f"  {_.get('found_files', count=len(metadata_list))}")
                
                # Calculate and display estimated time for scanning
                if dir_idx < total_dirs:
                    elapsed = time.time() - start_time
                    avg_time_per_dir = elapsed / dir_idx
                    remaining_dirs = total_dirs - dir_idx
                    est_seconds = int(avg_time_per_dir * remaining_dirs)
                    
                    if est_seconds < 60:
                        time_str = f"{est_seconds}s"
                    else:
                        minutes = est_seconds // 60
                        seconds = est_seconds % 60
                        time_str = f"{minutes}m {seconds}s"
                    
                    self.time_label.config(text=_.get('estimated_time', time=time_str))
                    self._update_status(f"{status_msg} - {_.get('estimated_time', time=time_str)}")
                
            if not all_metadata:
                self._log(_.get("no_music_files"))
                messagebox.showwarning(_.get("warning"), _.get("no_files_found"))
                return
                
            self._log(_.get("total_found", count=len(all_metadata)))
            
            # Duplicate detection
            metadata_to_export = all_metadata
            if self.detect_duplicates.get() or self.remove_duplicates.get():
                self._log(_.get("checking_duplicates"))
                detector = DuplicateDetector()
                duplicates = detector.find_duplicates(all_metadata)
                
                if duplicates:
                    dup_count = sum(len(v) for v in duplicates.values())
                    self._log(_.get("found_duplicates", groups=len(duplicates), total=dup_count))
                    
                    if self.remove_duplicates.get():
                        unique_list, removed_list = detector.remove_duplicates(
                            all_metadata,
                            strategy=self.duplicate_strategy.get()
                        )
                        metadata_to_export = unique_list
                        self._log(_.get("removed_duplicates", count=len(removed_list)))
                        self._log(_.get("unique_remaining", count=len(unique_list)))
                else:
                    self._log(_.get("no_duplicates"))
                    
            # Export
            fmt = self.export_format.get().upper()
            self._log(_.get("exporting_to", format=fmt))
            
            exporter_kwargs = {"max_songs_per_file": self.max_songs_per_file.get()}
            exporter = get_exporter(self.export_format.get(), **exporter_kwargs)
            exporter.export(metadata_to_export, self.output_file.get())
            
            self._log(_.get("export_completed", file=self.output_file.get()))
            self._log("="*50)
            
            self._update_status(_.get("completed"))
            messagebox.showinfo(
                _.get("success"),
                _.get("success_message", count=len(metadata_to_export), file=self.output_file.get())
            )
            
        except Exception as e:
            self._log(f"❌ {_.get('error')}: {str(e)}")
            self._update_status(_.get("error_occurred"))
            messagebox.showerror(_.get("error"), _.get("error_message", error=str(e)))
            
        finally:
            self.processing = False
            self.progress_bar.stop()
            self.progress_bar['value'] = 0
            self.time_label.config(text="")
            self.process_btn.config(state=tk.NORMAL)
            self._update_status(_.get("ready"))
            
    def _show_help(self):
        """Show help dialog."""
        _ = self.i18n
        messagebox.showinfo(_.get("help_title"), _.get("help_text"))
        
    def _show_about(self):
        """Show about dialog."""
        _ = self.i18n
        messagebox.showinfo(_.get("about_title"), _.get("about_text"))


def main():
    """Main entry point for GUI."""
    root = tk.Tk()
    app = MusicListGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
