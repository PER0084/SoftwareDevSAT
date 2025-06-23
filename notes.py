import customtkinter as ctk
from customtkinter import CTkFrame, CTkLabel, CTkEntry, CTkButton, CTkTextbox, CTkScrollableFrame, CTkProgressBar
from utils import (get_notes_dir, get_student_data_path, read_csv, write_csv,
                   read_txt, write_txt, delete_file, get_current_datetime_str,
                   DATETIME_FORMAT, validate_not_empty)
import os
import random
from CTkMessagebox import CTkMessagebox

NOTES_METADATA_FILE = "notes_metadata.csv"
NOTES_METADATA_HEADERS = ['title', 'last_modified', 'file_path', 'student_id', 'subject']

# Note-Taking Tips
NOTE_TAKING_TIPS = [
    "Use bullet points to organize your thoughts clearly!",
    "Highlight key concepts with colors to make them stand out.",
    "Summarize your notes at the end for quick review.",
    "Include examples to better understand complex topics.",
    "Review your notes within 24 hours to improve retention!"
]

class NotesTab(CTkFrame):
    """GUI Frame for managing notes."""
    def __init__(self, parent, username):
        super().__init__(parent, corner_radius=15, fg_color=("#e6f0ff", "#1a2a44"))
        self.username = username
        self.notes_dir = get_notes_dir(self.username)
        self.metadata_file_path = get_student_data_path(self.username, NOTES_METADATA_FILE)
        self.notes_metadata = []
        self.current_note_title = None
        self.selected_note_index = -1
        self.note_buttons = []

        # Inner frame for shadow effect
        self.inner_frame = CTkFrame(self, corner_radius=15, fg_color=("#ffffff", "#2b2b2b"), border_width=2, border_color=("#1f77b4", "#4a90e2"))
        self.inner_frame.pack(padx=5, pady=5, fill="both", expand=True)

        # --- Layout: Split Sidebar and Content Area ---
        self.main_frame = CTkFrame(self.inner_frame, corner_radius=0, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # --- Sidebar (Left Pane) ---
        self.sidebar_frame = CTkFrame(self.main_frame, width=200, corner_radius=10, fg_color=("#f5f5f5", "#333333"))
        self.sidebar_frame.pack(side="left", fill="y", padx=(0, 5))

        # Animated Title
        self.title_label = CTkLabel(self.sidebar_frame, text="", font=("Comic Sans MS", 18, "bold"))
        self.title_label.pack(pady=5)
        self._animate_title(self.title_label, "Notes")

        # Note-Taking Tip
        tip = random.choice(NOTE_TAKING_TIPS)
        CTkLabel(self.sidebar_frame, text=f"💡 Tip: {tip}", font=("Helvetica", 10, "italic"), wraplength=180).pack(pady=5)

        # Search Bar
        f_search = CTkFrame(self.sidebar_frame, fg_color="transparent")
        CTkLabel(f_search, text="🔍", font=("Helvetica", 16)).pack(side="left", padx=(5, 0))
        self.search_entry = CTkEntry(
            f_search,
            placeholder_text="Search notes...",
            width=150,
            corner_radius=8,
            border_width=0,
            fg_color=("#e0e0e0", "#444444")
        )
        self.search_entry.pack(side="left", padx=5, pady=5, fill="x", expand=True)
        f_search.pack(pady=5, padx=5, fill="x")
        self.search_entry.bind("<KeyRelease>", self._filter_notes)

        # Scrollable frame for note titles
        self.notes_scroll = CTkScrollableFrame(self.sidebar_frame, corner_radius=10)
        self.notes_scroll.pack(pady=5, padx=5, fill="both", expand=True)

        # Sidebar Buttons Frame
        sidebar_buttons_frame = CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.add_note_button = CTkButton(
            sidebar_buttons_frame,
            text="New Note ✍️",
            command=self._add_new_note,
            corner_radius=8,
            font=("Helvetica", 12, "bold"),
            fg_color=("#1f77b4", "#4a90e2"),
            hover_color=("#165a92", "#357abd")
        )
        self.add_note_button.pack(side="left", padx=5)
        self.add_note_button.bind("<Enter>", lambda event: self._scale_button_in(self.add_note_button))
        self.add_note_button.bind("<Leave>", lambda event: self._scale_button_out(self.add_note_button))

        self.delete_note_button = CTkButton(
            sidebar_buttons_frame,
            text="Delete 🗑️",
            command=self._delete_note,
            corner_radius=8,
            font=("Helvetica", 12, "bold"),
            fg_color=("#ff3b30", "#cc2f27"),
            hover_color=("#e6352b", "#b32923")
        )
        self.delete_note_button.pack(side="left", padx=5)
        self.delete_note_button.bind("<Enter>", lambda event: self._scale_button_in(self.delete_note_button))
        self.delete_note_button.bind("<Leave>", lambda event: self._scale_button_out(self.delete_note_button))
        sidebar_buttons_frame.pack(pady=5)

        # --- Content Area (Right Pane) ---
        self.content_frame = CTkFrame(self.main_frame, corner_radius=10, fg_color=("#f5f5f5", "#333333"))
        self.content_frame.pack(side="left", fill="both", expand=True)

        # Subject, Title, and Last Modified Display
        meta_frame = CTkFrame(self.content_frame, fg_color="transparent")
        meta_frame.pack(pady=5, padx=10, fill="x")

        f_subject = CTkFrame(meta_frame, fg_color="transparent")
        CTkLabel(f_subject, text="📚 Subject:", width=100, anchor="w", font=("Helvetica", 12)).pack(side="left", padx=5)
        self.subject_label = CTkLabel(f_subject, text="", width=300, anchor="w", font=("Helvetica", 12))
        self.subject_label.pack(side="left", padx=5, fill="x", expand=True)
        f_subject.pack(pady=5, fill="x")

        f_title = CTkFrame(meta_frame, fg_color="transparent")
        CTkLabel(f_title, text="📝 Title:", width=100, anchor="w", font=("Helvetica", 12)).pack(side="left", padx=5)
        self.title_label = CTkLabel(f_title, text="", width=300, anchor="w", font=("Helvetica", 12))
        self.title_label.pack(side="left", padx=5, fill="x", expand=True)
        f_title.pack(pady=5, fill="x")

        f_last_modified = CTkFrame(meta_frame, fg_color="transparent")
        CTkLabel(f_last_modified, text="⏰ Last Modified:", width=100, anchor="w", font=("Helvetica", 12)).pack(side="left", padx=5)
        self.last_modified_label = CTkLabel(f_last_modified, text="", width=300, anchor="w", font=("Helvetica", 12))
        self.last_modified_label.pack(side="left", padx=5, fill="x", expand=True)
        f_last_modified.pack(pady=5, fill="x")

        # Note Content Area
        self.note_content_text = CTkTextbox(
            self.content_frame,
            wrap="word",
            height=15,
            width=60,
            corner_radius=8,
            border_width=0,
            fg_color=("#e0e0e0", "#444444")
        )
        self.note_content_text.pack(pady=10, padx=10, fill="both", expand=True)
        self.note_content_text.configure(state="disabled")

        # Save Button and Progress Bar
        self.save_frame = CTkFrame(self.content_frame, fg_color="transparent")
        self.save_button = CTkButton(
            self.save_frame,
            text="Save Changes 💾",
            command=self._save_note,
            corner_radius=8,
            font=("Helvetica", 12, "bold"),
            fg_color=("#34c759", "#2ba844"),
            hover_color=("#2eb350", "#25933b")
        )
        self.save_button.pack(pady=10)
        self.save_button.bind("<Enter>", lambda event: self._scale_button_in(self.save_button))
        self.save_button.bind("<Leave>", lambda event: self._scale_button_out(self.save_button))

        self.progress_bar = CTkProgressBar(self.save_frame, mode="indeterminate", width=200)
        self.progress_bar.pack_forget()
        self.save_frame.pack(pady=5)

        # Load initial data
        self._load_metadata()

    def _animate_title(self, label, text, index=0):
        """Animates the title by typing it out."""
        if index <= len(text):
            label.configure(text=text[:index])
            self.after(50, self._animate_title, label, text, index + 1)

    def _scale_button_in(self, button):
        """Scale button up on hover."""
        button.configure(height=32)

    def _scale_button_out(self, button):
        """Scale button back on hover out."""
        button.configure(height=30)

    def _fade_in_content(self):
        """Fades in the note content area."""
        self.note_content_text.configure(state="normal")
        self.note_content_text.configure(fg_color=("#e0e0e0", "#444444"))

    def _get_note_filepath(self, title):
        safe_filename = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in title).replace(' ', '_')
        safe_filename = (safe_filename[:50] + '.txt') if len(safe_filename) > 50 else (safe_filename + '.txt')
        return os.path.join(self.notes_dir, safe_filename)

    def _load_metadata(self):
        self.notes_metadata = read_csv(self.metadata_file_path, NOTES_METADATA_HEADERS)
        self.notes_metadata.sort(key=lambda x: x.get('last_modified', '0000-00-00 00:00'), reverse=True)
        self._populate_listbox()
        self._clear_content_area()

    def _save_metadata(self):
        write_csv(self.metadata_file_path, self.notes_metadata, NOTES_METADATA_HEADERS)

    def _populate_listbox(self):
        for widget in self.notes_scroll.winfo_children():
            widget.destroy()
        self.note_buttons = []
        self.selected_note_index = -1

        search_query = self.search_entry.get().strip().lower()
        filtered_notes = [
            meta for meta in self.notes_metadata
            if search_query in meta.get('title', 'Untitled').lower()
        ]

        for i, meta in enumerate(filtered_notes):
            title = meta.get('title', 'Untitled')
            btn = CTkButton(
                self.notes_scroll,
                text=f"📝 {title}",
                anchor="w",
                command=lambda idx=i: self._select_note(idx),
                corner_radius=5,
                fg_color=("gray90", "gray20") if i % 2 == 0 else ("gray80", "gray30"),
                hover_color=("gray70", "gray50"),
                text_color=("black", "white"),
                font=("Helvetica", 12)
            )
            btn.pack(fill="x", pady=2)
            btn.bind("<Enter>", lambda event, b=btn: b.configure(fg_color=("gray70", "gray50")))
            btn.bind("<Leave>", lambda event, b=btn, idx=i: b.configure(fg_color=("gray90", "gray20") if idx % 2 == 0 else ("gray80", "gray30")))
            self.note_buttons.append(btn)

        if self.current_note_title:
            for i, meta in enumerate(filtered_notes):
                if meta.get('title') == self.current_note_title:
                    self._select_note(i)
                    break

    def _filter_notes(self, event=None):
        self._populate_listbox()

    def _select_note(self, index):
        if index < 0 or index >= len(self.note_buttons):
            return

        self.selected_note_index = index
        for i, btn in enumerate(self.note_buttons):
            if i == index:
                btn.configure(fg_color=("gray70", "gray50"))
            else:
                btn.configure(fg_color=("gray90", "gray20") if i % 2 == 0 else ("gray80", "gray30"))

        search_query = self.search_entry.get().strip().lower()
        filtered_notes = [
            meta for meta in self.notes_metadata
            if search_query in meta.get('title', 'Untitled').lower()
        ]

        selected_meta = filtered_notes[index]
        self.current_note_title = selected_meta.get('title')
        file_path = selected_meta.get('file_path')
        subject = selected_meta.get('subject', 'N/A')
        last_modified = selected_meta.get('last_modified', 'N/A')

        self.title_label.configure(text=self.current_note_title)
        self.subject_label.configure(text=subject)
        self.last_modified_label.configure(text=last_modified)

        self.note_content_text.configure(state="normal")
        self.note_content_text.delete("1.0", "end")
        if file_path and os.path.exists(file_path):
            content = read_txt(file_path)
            self.note_content_text.insert("1.0", content)
        else:
            self.note_content_text.insert("1.0", f"[Error: Note file not found at {file_path}]")
            print(f"Warning: Note file not found: {file_path} for title '{self.current_note_title}'")
        self._fade_in_content()

    def _clear_content_area(self):
        self.current_note_title = None
        self.selected_note_index = -1
        for btn in self.note_buttons:
            idx = self.note_buttons.index(btn)
            btn.configure(fg_color=("gray90", "gray20") if idx % 2 == 0 else ("gray80", "gray30"))
        self.title_label.configure(text="")
        self.subject_label.configure(text="")
        self.last_modified_label.configure(text="")
        self.note_content_text.delete("1.0", "end")
        self.note_content_text.configure(state="disabled")

    def _add_new_note(self):
        dialog = ctk.CTkInputDialog(title="New Note", text="Enter note title:")
        title = dialog.get_input()
        
        if not title or not title.strip():
            CTkMessagebox(title="Input Error", message="Title cannot be empty.", icon="warning")

            return

        if any(meta.get('title', '').lower() == title.strip().lower() for meta in self.notes_metadata):
            CTkMessagebox(title="Error", message=f"A note with the title '{title}' already exists.", icon="cancel")

            return

        dialog = ctk.CTkInputDialog(title="New Note", text=f"Enter subject for '{title}':")
        subject = dialog.get_input()
        
        if subject is None:
            return
        if not subject.strip():
            subject = "General"

        file_path = self._get_note_filepath(title)
        timestamp = get_current_datetime_str()

        new_meta = {
            'title': title.strip(),
            'subject': subject.strip(),
            'last_modified': timestamp,
            'file_path': file_path,
            'student_id': self.username
        }

        write_txt(file_path, f"# {title.strip()}\n\nSubject: {subject.strip()}\n\n")

        self.notes_metadata.append(new_meta)
        self.notes_metadata.sort(key=lambda x: x.get('last_modified', '0000-00-00 00:00'), reverse=True)
        self._save_metadata()
        self._populate_listbox()

        for i, meta in enumerate(self.notes_metadata):
            if meta.get('title') == title.strip():
                self._select_note(i)
                break

    def _save_note(self):
        if self.current_note_title is None or self.selected_note_index == -1:
            CTkMessagebox(title="Save Error", message="No note selected to save.", icon="warning").get()

            return

        self.save_button.pack_forget()
        self.progress_bar.pack(pady=10)
        self.progress_bar.start()

        self.after(1000, self._complete_save)

    def _complete_save(self):
        current_meta = self.notes_metadata[self.selected_note_index]
        if current_meta.get('title') != self.current_note_title:
            CTkMessagebox(title="Save Error", message=f"Metadata mismatch for '{self.current_note_title}'.", icon="cancel").get()
            self.progress_bar.stop()
            self.progress_bar.pack_forget()
            self.save_button.pack(pady=10)

            return

        content = self.note_content_text.get("1.0", "end").strip()
        file_path = current_meta.get('file_path')
        timestamp = get_current_datetime_str()

        write_txt(file_path, content)

        self.notes_metadata[self.selected_note_index]['last_modified'] = timestamp
        self.last_modified_label.configure(text=timestamp)
        self.notes_metadata.sort(key=lambda x: x.get('last_modified', '0000-00-00 00:00'), reverse=True)
        self._populate_listbox()

        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.save_button.pack(pady=10)

        CTkMessagebox(title="Save Success", message=f"Note '{self.current_note_title}' saved successfully.", icon="check").get()

    def _delete_note(self):
        if self.selected_note_index == -1:
            CTkMessagebox(title="Selection Error", message="Please select a note to delete.", icon="warning").get()

            return

        selected_title = self.notes_metadata[self.selected_note_index].get('title')

        if CTkMessagebox(title="Confirm Delete", message=f"Are you sure you want to permanently delete the note '{selected_title}'?", option_1="Yes", option_2="No").get() == "Yes":
            meta_to_delete = self.notes_metadata[self.selected_note_index]
            file_path = meta_to_delete.get('file_path')
            if file_path:
                delete_file(file_path)
            del self.notes_metadata[self.selected_note_index]
            self._save_metadata()
            self._populate_listbox()
            self._clear_content_area()
            CTkMessagebox(title="Delete Success", message=f"Note '{selected_title}' deleted.", icon="check").get()

    def apply_theme(self, theme):
        pass