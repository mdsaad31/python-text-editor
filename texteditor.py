import tkinter as tk
from tkinter import filedialog, messagebox, font, scrolledtext
import os
import json
from datetime import datetime
import re

class TextEditor:
    def __init__(self, root):
        self.root = root
        self.setup_window()
        self.setup_variables()
        self.setup_theme()
        self.create_widgets()
        self.setup_menu()
        self.setup_bindings()
        self.load_session()
        
        # Apply theme after everything is created
        self.apply_theme()

    def setup_window(self):
        """Configure the main window"""
        self.root.title("PyEdit - Text Editor")
        self.root.geometry("1000x700")
        self.root.minsize(600, 400)

    def setup_variables(self):
        """Initialize editor variables"""
        self.current_file = None
        self.auto_save = False
        self.auto_save_interval = 300000  # 5 minutes
        self.dark_mode = False
        self.session_file = "editor_session.json"
        self.syntax_highlighting = True

    def setup_theme(self):
        """Define color themes and syntax highlighting colors"""
        self.light_theme = {
            'bg': '#FFFFFF', 'fg': '#000000',
            'text_bg': '#FFFFFF', 'text_fg': '#000000',
            'select_bg': '#CCCCCC', 'select_fg': '#000000',
            'status_bg': '#F0F0F0', 'status_fg': '#000000',
            'menu_bg': '#F0F0F0', 'menu_fg': '#000000'
        }
        
        self.dark_theme = {
            'bg': '#2E2E2E', 'fg': '#E0E0E0',
            'text_bg': '#1E1E1E', 'text_fg': '#E0E0E0',
            'select_bg': '#3E3E3E', 'select_fg': '#FFFFFF',
            'status_bg': '#1E1E1E', 'status_fg': '#E0E0E0',
            'menu_bg': '#1E1E1E', 'menu_fg': '#E0E0E0'
        }
        
        self.syntax_colors = {
            'keyword': '#0000FF', 'string': '#008000',
            'comment': '#808080', 'number': '#FF00FF',
            'builtin': '#800080'
        }

        # Python keywords and builtins for syntax highlighting
        self.python_keywords = [
            'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await',
            'break', 'class', 'continue', 'def', 'del', 'elif', 'else', 'except',
            'finally', 'for', 'from', 'global', 'if', 'import', 'in', 'is',
            'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise', 'return',
            'try', 'while', 'with', 'yield'
        ]
        
        self.python_builtins = [
            'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'bytearray', 'bytes',
            'callable', 'chr', 'classmethod', 'compile', 'complex', 'delattr',
            'dict', 'dir', 'divmod', 'enumerate', 'eval', 'exec', 'filter',
            'float', 'format', 'frozenset', 'getattr', 'globals', 'hasattr',
            'hash', 'help', 'hex', 'id', 'input', 'int', 'isinstance',
            'issubclass', 'iter', 'len', 'list', 'locals', 'map', 'max',
            'memoryview', 'min', 'next', 'object', 'oct', 'open', 'ord',
            'pow', 'print', 'property', 'range', 'repr', 'reversed', 'round',
            'set', 'setattr', 'slice', 'sorted', 'staticmethod', 'str',
            'sum', 'super', 'tuple', 'type', 'vars', 'zip'
        ]

    def create_widgets(self):
        """Create all UI widgets"""
        # Main text area
        self.text_frame = tk.Frame(self.root)
        self.text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.text = scrolledtext.ScrolledText(
            self.text_frame,
            wrap=tk.WORD,
            font=('Consolas', 12),
            undo=True,
            maxundo=-1
        )
        self.text.pack(fill=tk.BOTH, expand=True)
        
        # Find/replace panel (hidden by default)
        self.find_frame = tk.Frame(self.root)
        
        tk.Label(self.find_frame, text="Find:").pack(side=tk.LEFT)
        self.find_entry = tk.Entry(self.find_frame)
        self.find_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        tk.Button(self.find_frame, text="Find", command=self.find_text).pack(side=tk.LEFT, padx=5)
        
        tk.Label(self.find_frame, text="Replace:").pack(side=tk.LEFT, padx=(10, 0))
        self.replace_entry = tk.Entry(self.find_frame)
        self.replace_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        tk.Button(self.find_frame, text="Replace", command=self.replace_text).pack(side=tk.LEFT)
        tk.Button(self.find_frame, text="Replace All", command=self.replace_all).pack(side=tk.LEFT, padx=5)
        
        self.case_sensitive = tk.IntVar()
        tk.Checkbutton(self.find_frame, text="Case Sensitive", variable=self.case_sensitive).pack(side=tk.LEFT, padx=5)
        
        # Status bar
        self.status = tk.StringVar()
        self.status.set("Ready")
        self.statusbar = tk.Label(
            self.root,
            textvariable=self.status,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)

    def setup_menu(self):
        """Create the menu bar"""
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)
        
        # File menu
        file_menu = tk.Menu(self.menubar, tearoff=0)
        file_menu.add_command(label="New", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Open", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As", command=self.save_as)
        file_menu.add_separator()
        
        self.auto_save_var = tk.IntVar(value=self.auto_save)
        file_menu.add_checkbutton(label="Auto Save", variable=self.auto_save_var, 
                                command=self.toggle_auto_save)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.exit_editor)
        self.menubar.add_cascade(label="File", menu=file_menu)
        
        # Edit menu
        edit_menu = tk.Menu(self.menubar, tearoff=0)
        edit_menu.add_command(label="Undo", command=self.text.edit_undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self.text.edit_redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", command=self.cut_text, accelerator="Ctrl+X")
        edit_menu.add_command(label="Copy", command=self.copy_text, accelerator="Ctrl+C")
        edit_menu.add_command(label="Paste", command=self.paste_text, accelerator="Ctrl+V")
        edit_menu.add_separator()
        edit_menu.add_command(label="Find", command=self.show_find_panel, accelerator="Ctrl+F")
        edit_menu.add_command(label="Replace", command=self.show_replace_panel, accelerator="Ctrl+H")
        edit_menu.add_separator()
        edit_menu.add_command(label="Select All", command=self.select_all, accelerator="Ctrl+A")
        self.menubar.add_cascade(label="Edit", menu=edit_menu)
        
        # View menu
        view_menu = tk.Menu(self.menubar, tearoff=0)
        self.dark_mode_var = tk.IntVar(value=self.dark_mode)
        view_menu.add_checkbutton(label="Dark Mode", variable=self.dark_mode_var, 
                                command=self.toggle_dark_mode)
        view_menu.add_separator()
        
        self.syntax_var = tk.IntVar(value=self.syntax_highlighting)
        view_menu.add_checkbutton(label="Syntax Highlighting", variable=self.syntax_var, 
                                command=self.toggle_syntax)
        self.menubar.add_cascade(label="View", menu=view_menu)
        
        # Format menu
        format_menu = tk.Menu(self.menubar, tearoff=0)
        
        # Font family submenu
        font_menu = tk.Menu(format_menu, tearoff=0)
        self.font_family = tk.StringVar(value="Consolas")
        for f in ['Consolas', 'Courier New', 'Arial', 'Helvetica', 'Times New Roman']:
            font_menu.add_radiobutton(label=f, variable=self.font_family, 
                                     command=self.change_font)
        
        # Font size submenu
        size_menu = tk.Menu(format_menu, tearoff=0)
        self.font_size = tk.IntVar(value=12)
        for s in [8, 10, 12, 14, 16, 18, 20, 24]:
            size_menu.add_radiobutton(label=str(s), variable=self.font_size,
                                    command=self.change_font)
        
        format_menu.add_cascade(label="Font", menu=font_menu)
        format_menu.add_cascade(label="Size", menu=size_menu)
        self.menubar.add_cascade(label="Format", menu=format_menu)

    def setup_bindings(self):
        """Set up keyboard shortcuts"""
        self.root.bind("<Control-n>", lambda e: self.new_file())
        self.root.bind("<Control-o>", lambda e: self.open_file())
        self.root.bind("<Control-s>", lambda e: self.save_file())
        self.root.bind("<Control-f>", lambda e: self.show_find_panel())
        self.root.bind("<Control-h>", lambda e: self.show_replace_panel())
        self.root.bind("<Control-a>", lambda e: self.select_all())
        
        self.text.bind("<KeyRelease>", self.update_status)
        if self.syntax_highlighting:
            self.text.bind("<KeyRelease>", self.highlight_syntax)

    # File operations
    def new_file(self):
        """Create a new file"""
        if self.text.edit_modified():
            if not messagebox.askyesno("Unsaved Changes", "Discard changes?"):
                return
        
        self.text.delete(1.0, tk.END)
        self.current_file = None
        self.root.title("PyEdit - Untitled")
        self.status.set("New file created")
        self.text.edit_modified(False)

    def open_file(self):
        """Open an existing file"""
        if self.text.edit_modified():
            if not messagebox.askyesno("Unsaved Changes", "Discard changes?"):
                return
        
        file_path = filedialog.askopenfilename(
            filetypes=[("Text Files", "*.txt"), ("Python Files", "*.py"), ("All Files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r') as file:
                    self.text.delete(1.0, tk.END)
                    self.text.insert(1.0, file.read())
                    self.current_file = file_path
                    self.root.title(f"PyEdit - {os.path.basename(file_path)}")
                    self.status.set(f"Opened: {file_path}")
                    self.text.edit_modified(False)
                    
                    if self.syntax_highlighting:
                        self.highlight_syntax()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file:\n{e}")

    def save_file(self):
        """Save the current file"""
        if self.current_file:
            try:
                with open(self.current_file, 'w') as file:
                    file.write(self.text.get(1.0, tk.END))
                self.status.set(f"Saved: {self.current_file}")
                self.text.edit_modified(False)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file:\n{e}")
        else:
            self.save_as()

    def save_as(self):
        """Save file with new name"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("Python Files", "*.py"), ("All Files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as file:
                    file.write(self.text.get(1.0, tk.END))
                self.current_file = file_path
                self.root.title(f"PyEdit - {os.path.basename(file_path)}")
                self.status.set(f"Saved as: {file_path}")
                self.text.edit_modified(False)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file:\n{e}")

    # Edit operations
    def cut_text(self):
        """Cut selected text"""
        self.text.event_generate("<<Cut>>")

    def copy_text(self):
        """Copy selected text"""
        self.text.event_generate("<<Copy>>")

    def paste_text(self):
        """Paste from clipboard"""
        self.text.event_generate("<<Paste>>")

    def select_all(self):
        """Select all text"""
        self.text.tag_add(tk.SEL, "1.0", tk.END)
        self.text.mark_set(tk.INSERT, "1.0")
        self.text.see(tk.INSERT)
        return "break"

    # Find/replace functionality
    def show_find_panel(self):
        """Show the find panel"""
        self.find_frame.pack(fill=tk.X, padx=5, pady=5)
        self.find_entry.focus_set()

    def show_replace_panel(self):
        """Show the replace panel"""
        self.find_frame.pack(fill=tk.X, padx=5, pady=5)
        self.replace_entry.focus_set()

    def find_text(self):
        """Find text in document"""
        self.text.tag_remove('found', '1.0', tk.END)
        search = self.find_entry.get()
        
        if search:
            idx = '1.0'
            while True:
                idx = self.text.search(search, idx, nocase=not self.case_sensitive.get(),
                                     stopindex=tk.END)
                if not idx:
                    break
                
                last_idx = f"{idx}+{len(search)}c"
                self.text.tag_add('found', idx, last_idx)
                idx = last_idx
            
            self.text.tag_config('found', background='yellow')
            self.status.set(f"Found: {search}")

    def replace_text(self):
        """Replace next occurrence of found text"""
        search = self.find_entry.get()
        replace = self.replace_entry.get()
        
        if search and replace:
            if self.text.tag_ranges(tk.SEL):
                idx = self.text.index(tk.SEL_FIRST)
            else:
                idx = '1.0'
            
            idx = self.text.search(search, idx, nocase=not self.case_sensitive.get(),
                                 stopindex=tk.END)
            
            if idx:
                last_idx = f"{idx}+{len(search)}c"
                self.text.delete(idx, last_idx)
                self.text.insert(idx, replace)
                self.status.set(f"Replaced: {search} with {replace}")
                self.find_text()

    def replace_all(self):
        """Replace all occurrences of text"""
        search = self.find_entry.get()
        replace = self.replace_entry.get()
        
        if search and replace:
            self.text.tag_remove('found', '1.0', tk.END)
            count = 0
            idx = '1.0'
            
            while True:
                idx = self.text.search(search, idx, nocase=not self.case_sensitive.get(),
                                     stopindex=tk.END)
                if not idx:
                    break
                
                last_idx = f"{idx}+{len(search)}c"
                self.text.delete(idx, last_idx)
                self.text.insert(idx, replace)
                count += 1
                idx = f"{idx}+{len(replace)}c"
            
            self.status.set(f"Replaced {count} occurrences")

    # View/Format operations
    def toggle_dark_mode(self):
        """Toggle between light and dark mode"""
        self.dark_mode = not self.dark_mode
        self.apply_theme()
        self.status.set(f"Dark mode {'on' if self.dark_mode else 'off'}")

    def toggle_syntax(self):
        """Toggle syntax highlighting"""
        self.syntax_highlighting = not self.syntax_highlighting
        if self.syntax_highlighting:
            self.text.bind("<KeyRelease>", self.highlight_syntax)
            self.highlight_syntax()
            self.status.set("Syntax highlighting on")
        else:
            self.text.unbind("<KeyRelease>")
            self.clear_syntax()
            self.status.set("Syntax highlighting off")

    def toggle_auto_save(self):
        """Toggle auto-save feature"""
        self.auto_save = not self.auto_save
        if self.auto_save:
            self.setup_auto_save()
            self.status.set("Auto-save enabled")
        else:
            self.status.set("Auto-save disabled")

    def change_font(self):
        """Change the editor font"""
        family = self.font_family.get()
        size = self.font_size.get()
        self.text.config(font=(family, size))

    # Syntax highlighting
    def highlight_syntax(self, event=None):
        """Apply syntax highlighting"""
        if not self.syntax_highlighting:
            return
        
        self.clear_syntax()
        
        # Highlight Python keywords
        for word in self.python_keywords:
            self.highlight_pattern(r'\b' + word + r'\b', 'keyword')
        
        # Highlight builtins
        for word in self.python_builtins:
            self.highlight_pattern(r'\b' + word + r'\b', 'builtin')
        
        # Highlight strings and comments
        self.highlight_pattern(r'"[^"\\]*(\\.[^"\\]*)*"', 'string')
        self.highlight_pattern(r"'[^'\\]*(\\.[^'\\]*)*'", 'string')
        self.highlight_pattern(r'#[^\n]*', 'comment')
        self.highlight_pattern(r'\b[0-9]+\b', 'number')

    def highlight_pattern(self, pattern, tag):
        """Helper function to highlight text patterns"""
        self.text.tag_remove(tag, '1.0', tk.END)
        start = '1.0'
        
        while True:
            start = self.text.search(pattern, start, regexp=True, 
                                   stopindex=tk.END)
            if not start:
                break
            
            end = f"{start}+{len(self.text.get(start, f'{start} lineend'))}c"
            self.text.tag_add(tag, start, end)
            start = end

    def clear_syntax(self):
        """Clear all syntax highlighting"""
        for tag in ['keyword', 'string', 'comment', 'number', 'builtin']:
            self.text.tag_remove(tag, '1.0', tk.END)

    # Theme and appearance
    def apply_theme(self):
        """Apply the current theme colors"""
        theme = self.dark_theme if self.dark_mode else self.light_theme
        
        # Configure main widgets
        self.root.config(bg=theme['bg'])
        self.text_frame.config(bg=theme['bg'])
        
        self.text.config(
            bg=theme['text_bg'],
            fg=theme['text_fg'],
            insertbackground=theme['fg'],
            selectbackground=theme['select_bg'],
            selectforeground=theme['select_fg']
        )
        
        # Configure find/replace panel
        self.find_frame.config(bg=theme['bg'])
        for widget in self.find_frame.winfo_children():
            if isinstance(widget, (tk.Label, tk.Button, tk.Checkbutton)):
                widget.config(bg=theme['bg'], fg=theme['fg'])
            elif isinstance(widget, tk.Entry):
                widget.config(
                    bg=theme['text_bg'],
                    fg=theme['text_fg'],
                    insertbackground=theme['fg']
                )
        
        # Configure status bar
        self.statusbar.config(
            bg=theme['status_bg'],
            fg=theme['status_fg']
        )
        
        # Re-apply syntax highlighting with new colors
        if self.syntax_highlighting:
            self.setup_syntax_tags()
            self.highlight_syntax()

    def setup_syntax_tags(self):
        """Configure tags for syntax highlighting"""
        for tag, color in self.syntax_colors.items():
            self.text.tag_configure(tag, foreground=color)

    # Session management
    def save_session(self):
        """Save editor session"""
        session = {
            'file': self.current_file,
            'geometry': self.root.geometry(),
            'dark_mode': self.dark_mode,
            'syntax': self.syntax_highlighting,
            'font': self.font_family.get(),
            'size': self.font_size.get()
        }
        
        try:
            with open(self.session_file, 'w') as f:
                json.dump(session, f)
        except Exception as e:
            print(f"Error saving session: {e}")

    def load_session(self):
        """Load editor session"""
        try:
            if os.path.exists(self.session_file):
                with open(self.session_file) as f:
                    session = json.load(f)
                
                if session.get('geometry'):
                    self.root.geometry(session['geometry'])
                
                if session.get('dark_mode'):
                    self.dark_mode = session['dark_mode']
                    self.dark_mode_var.set(self.dark_mode)
                
                if session.get('syntax'):
                    self.syntax_highlighting = session['syntax']
                    self.syntax_var.set(self.syntax_highlighting)
                
                if session.get('font'):
                    self.font_family.set(session['font'])
                
                if session.get('size'):
                    self.font_size.set(session['size'])
                
                if session.get('file') and os.path.exists(session['file']):
                    self.current_file = session['file']
                    self.open_file()
        except Exception as e:
            print(f"Error loading session: {e}")

    # Auto-save functionality
    def setup_auto_save(self):
        """Setup auto-save timer"""
        if self.auto_save:
            self.auto_save_job()

    def auto_save_job(self):
        """Auto-save the current file"""
        if self.auto_save and self.text.edit_modified():
            self.save_file()
            self.status.set(f"Auto-saved at {datetime.now().strftime('%H:%M')}")
        
        if self.auto_save:
            self.root.after(self.auto_save_interval, self.auto_save_job)

    # Status bar
    def update_status(self, event=None):
        """Update status bar information"""
        line, col = self.text.index(tk.INSERT).split('.')
        lines = len(self.text.get('1.0', tk.END).splitlines())
        modified = "*" if self.text.edit_modified() else ""
        self.status.set(f"Line: {line}, Col: {col} | Lines: {lines} {modified}")

    def exit_editor(self):
        """Clean up and exit the editor"""
        if self.text.edit_modified():
            if not messagebox.askyesno("Unsaved Changes", "Exit without saving?"):
                return
        
        self.save_session()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    editor = TextEditor(root)
    root.mainloop()