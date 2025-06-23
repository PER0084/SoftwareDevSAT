import customtkinter as ctk
from customtkinter import CTkFrame, CTkLabel, CTkEntry, CTkButton, CTkOptionMenu, CTkScrollableFrame, CTkProgressBar
from utils import (get_student_data_path, read_csv, write_csv,
                   validate_not_empty, validate_time_range,
                   get_current_datetime_str, parse_datetime_str)
import os
import random
from datetime import datetime
from CTkMessagebox import CTkMessagebox

SCHEDULE_FILE = "schedules.csv"
SCHEDULE_HEADERS = ['subject', 'topic', 'time', 'priority', 'student_id', 'id']

# Scheduling Tips
SCHEDULING_TIPS = [
    "Schedule your most challenging subjects when you're most alert!",
    "Break your study sessions into 25-minute blocks with 5-minute breaks.",
    "Prioritize high-priority tasks early in the day.",
    "Leave buffer time between sessions to avoid burnout.",
    "Review your schedule weekly to stay on track!"
]

class SchedulingTab(CTkFrame):
    """GUI Frame for managing study schedules."""
    def __init__(self, parent, username):
        super().__init__(parent, corner_radius=15, fg_color=("#e6f0ff", "#1a2a44"))
        self.username = username
        self.schedule_file_path = get_student_data_path(self.username, SCHEDULE_FILE)
        self.schedule_data = []
        self.next_id = 1
        self.selected_schedule_id = None
        self.schedule_rows = []

        # Inner frame for shadow effect
        self.inner_frame = CTkFrame(self, corner_radius=15, fg_color=("#ffffff", "#2b2b2b"),
                                    border_width=2, border_color=("#1f77b4", "#4a90e2"))
        self.inner_frame.pack(padx=5, pady=5, fill="both", expand=True)

        # --- Animated Title ---
        self.title_label = CTkLabel(self.inner_frame, text="", font=("Comic Sans MS", 18, "bold"))
        self.title_label.pack(pady=5)
        self._animate_title(self.title_label, "Schedule Your Study Sessions")

        # Scheduling Tip
        tip = random.choice(SCHEDULING_TIPS)
        CTkLabel(self.inner_frame, text=f"💡 Tip: {tip}", font=("Helvetica", 10, "italic"),
                 wraplength=600).pack(pady=5)

        # --- Input Frame ---
        input_frame = CTkFrame(self.inner_frame, fg_color=("#f5f5f5", "#333333"), corner_radius=10)
        input_frame.pack(pady=10, padx=10, fill="x")

        # Subject
        f_subject = CTkFrame(input_frame, fg_color="transparent")
        CTkLabel(f_subject, text="📚", font=("Helvetica", 16)).pack(side="left", padx=(5, 0))
        CTkLabel(f_subject, text="Subject:", width=120, anchor="w", font=("Helvetica", 12)).pack(side="left", padx=5)
        self.subject_entry = CTkEntry(
            f_subject,
            width=200,
            placeholder_text="Enter subject",
            corner_radius=8,
            border_width=0,
            fg_color=("#e0e0e0", "#444444")
        )
        self.subject_entry.pack(side="left", padx=5, fill="x", expand=True)
        f_subject.pack(pady=5, padx=10, fill="x")

        # Topic
        f_topic = CTkFrame(input_frame, fg_color="transparent")
        CTkLabel(f_topic, text="📝", font=("Helvetica", 16)).pack(side="left", padx=(5, 0))
        CTkLabel(f_topic, text="Topic:", width=120, anchor="w", font=("Helvetica", 12)).pack(side="left", padx=5)
        self.topic_entry = CTkEntry(
            f_topic,
            width=200,
            placeholder_text="Enter topic",
            corner_radius=8,
            border_width=0,
            fg_color=("#e0e0e0", "#444444")
        )
        self.topic_entry.pack(side="left", padx=5, fill="x", expand=True)
        f_topic.pack(pady=5, padx=10, fill="x")

        # Time
        f_time = CTkFrame(input_frame, fg_color="transparent")
        CTkLabel(f_time, text="⏰", font=("Helvetica", 16)).pack(side="left", padx=(5, 0))
        CTkLabel(f_time, text="Time (YYYY-MM-DD HH:MM-HH:MM):", width=120, anchor="w", font=("Helvetica", 12)).pack(side="left", padx=5)
        self.time_entry = CTkEntry(
            f_time,
            width=200,
            placeholder_text="e.g., 2025-04-10 09:00-10:00",
            corner_radius=8,
            border_width=0,
            fg_color=("#e0e0e0", "#444444")
        )
        self.time_entry.pack(side="left", padx=5, fill="x", expand=True)
        f_time.pack(pady=5, padx=10, fill="x")

        # Priority
        f_priority = CTkFrame(input_frame, fg_color="transparent")
        CTkLabel(f_priority, text="⚡", font=("Helvetica", 16)).pack(side="left", padx=(5, 0))
        CTkLabel(f_priority, text="Priority:", width=120, anchor="w", font=("Helvetica", 12)).pack(side="left", padx=5)
        self.priority_var = ctk.StringVar(value="Medium")
        self.priority_menu = CTkOptionMenu(
            f_priority,
            variable=self.priority_var,
            values=["High", "Medium", "Low"],
            width=200,
            corner_radius=8,
            fg_color=("#1f77b4", "#4a90e2"),
            button_color=("#165a92", "#357abd"),
            button_hover_color=("#0f4a7b", "#2a6aa3"),
            text_color=("white", "white"),
            font=("Helvetica", 12)
        )
        self.priority_menu.pack(side="left", padx=5, fill="x", expand=True)
        self.priority_menu.bind("<Enter>", lambda event: self._scale_menu_in(self.priority_menu))
        self.priority_menu.bind("<Leave>", lambda event: self._scale_menu_out(self.priority_menu))
        f_priority.pack(pady=5, padx=10, fill="x")

        # Buttons
        button_frame = CTkFrame(input_frame, fg_color="transparent")
        self.add_button = CTkButton(
            button_frame,
            text="Add Schedule ➕",
            command=self._add_schedule,
            corner_radius=8,
            font=("Helvetica", 12, "bold"),
            fg_color=("#1f77b4", "#4a90e2"),
            hover_color=("#165a92", "#357abd")
        )
        self.add_button.pack(side="left", padx=5)
        self.add_button.bind("<Enter>", lambda event: self._scale_button_in(self.add_button))
        self.add_button.bind("<Leave>", lambda event: self._scale_button_out(self.add_button))

        self.delete_button = CTkButton(
            button_frame,
            text="Delete Selected 🗑️",
            command=self._delete_schedule,
            corner_radius=8,
            font=("Helvetica", 12, "bold"),
            fg_color=("#ff3b30", "#cc2f27"),
            hover_color=("#e6352b", "#b32923")
        )
        self.delete_button.pack(side="left", padx=5)
        self.delete_button.bind("<Enter>", lambda event: self._scale_button_in(self.delete_button))
        self.delete_button.bind("<Leave>", lambda event: self._scale_button_out(self.delete_button))

        self.clear_button = CTkButton(
            button_frame,
            text="Clear Fields 🔄",
            command=self._clear_fields,
            corner_radius=8,
            font=("Helvetica", 12, "bold"),
            fg_color=("#ff9500", "#cc7700"),
            hover_color=("#e68a00", "#b36b00")
        )
        self.clear_button.pack(side="left", padx=5)
        self.clear_button.bind("<Enter>", lambda event: self._scale_button_in(self.clear_button))
        self.clear_button.bind("<Leave>", lambda event: self._scale_button_out(self.clear_button))

        self.progress_bar = CTkProgressBar(button_frame, mode="indeterminate", width=100)
        self.progress_bar.pack_forget()
        button_frame.pack(pady=10)

        # --- Schedule Display ---
        tree_frame = CTkFrame(self.inner_frame, corner_radius=10, fg_color=("#f5f5f5", "#333333"))
        tree_frame.pack(pady=10, padx=10, fill="both", expand=True)

        # Header for the schedule display
        self.header_frame = CTkFrame(tree_frame, fg_color=("#d3d3d3", "#555555"))
        CTkLabel(self.header_frame, text="Subject", width=150, anchor="w", font=("Helvetica", 12, "bold")).pack(side="left", padx=5)
        CTkLabel(self.header_frame, text="Topic", width=200, anchor="w", font=("Helvetica", 12, "bold")).pack(side="left", padx=5)
        CTkLabel(self.header_frame, text="Time", width=200, anchor="center", font=("Helvetica", 12, "bold")).pack(side="left", padx=5)
        CTkLabel(self.header_frame, text="Priority", width=80, anchor="center", font=("Helvetica", 12, "bold")).pack(side="left", padx=5)
        self.header_frame.pack(fill="x", pady=(0, 5))

        # Scrollable frame for schedule entries
        self.schedule_scroll = CTkScrollableFrame(tree_frame, corner_radius=10)
        self.schedule_scroll.pack(fill="both", expand=True)

        # Load initial data
        self._load_schedules()

        # Reminder Check
        self._check_reminders()
        self.after(60000, self._check_reminders)

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

    def _scale_menu_in(self, menu):
        """Scale menu up on hover."""
        menu.configure(height=32)

    def _scale_menu_out(self, menu):
        """Scale menu back on hover out."""
        menu.configure(height=30)


    def _fade_in_schedule(self):
        """Simulates a fade-in effect for the schedule display."""
        self.schedule_scroll.pack(fill="both", expand=True)

    def _get_max_id(self):
        if not self.schedule_data:
            return 0
        max_id = 0
        for item in self.schedule_data:
            try:
                item_id = int(item.get('id', 0))
                if item_id > max_id:
                    max_id = item_id
            except (ValueError, TypeError):
                continue
        return max_id

    def _load_schedules(self):
        self.schedule_data = read_csv(self.schedule_file_path, SCHEDULE_HEADERS)
        self.next_id = self._get_max_id() + 1
        self._populate_schedule_display()

    def _save_schedules(self):
        write_csv(self.schedule_file_path, self.schedule_data, SCHEDULE_HEADERS)

    def _populate_schedule_display(self):
        for widget in self.schedule_scroll.winfo_children():
            widget.destroy()
        self.schedule_rows = []
        self.selected_schedule_id = None

        try:
            self.schedule_data.sort(key=lambda x: datetime.strptime(x.get('time', '').split(' ')[0], '%Y-%m-%d') if x.get('time') else datetime.max.date())
        except Exception as e:
            print(f"Warning: Could not sort schedules by time - {e}")

        for idx, item in enumerate(self.schedule_data):
            item_id = item.get('id', '')
            subject = item.get('subject', 'N/A')
            topic = item.get('topic', 'N/A')
            time_str = item.get('time', 'N/A')
            priority = item.get('priority', 'N/A')

            # Color-code priority
            priority_color = {
                "High": ("#ff3b30", "#cc2f27"),
                "Medium": ("#ff9500", "#cc7700"),
                "Low": ("#34c759", "#2ba844")
            }.get(priority, ("gray50", "gray50"))

            row_frame = CTkFrame(self.schedule_scroll,
                                 fg_color=("gray90", "gray20") if idx % 2 == 0 else ("gray80", "gray30"))
            row_frame.pack(fill="x", pady=2)

            def select_row(id_to_select=item_id):
                self._select_schedule(id_to_select)

            CTkButton(
                row_frame,
                text=subject,
                width=150,
                anchor="w",
                command=select_row,
                fg_color="transparent",
                hover_color=("gray70", "gray50"),
                text_color=("black", "white"),
                font=("Helvetica", 12)
            ).pack(side="left", padx=5)
            CTkButton(
                row_frame,
                text=topic,
                width=200,
                anchor="w",
                command=select_row,
                fg_color="transparent",
                hover_color=("gray70", "gray50"),
                text_color=("black", "white"),
                font=("Helvetica", 12)
            ).pack(side="left", padx=5)
            CTkButton(
                row_frame,
                text=time_str,
                width=200,
                anchor="center",
                command=select_row,
                fg_color="transparent",
                hover_color=("gray70", "gray50"),
                text_color=("black", "white"),
                font=("Helvetica", 12)
            ).pack(side="left", padx=5)
            CTkButton(
                row_frame,
                text=priority,
                width=80,
                anchor="center",
                command=select_row,
                fg_color=priority_color,
                hover_color=priority_color,
                text_color=("white", "white"),
                font=("Helvetica", 12, "bold")
            ).pack(side="left", padx=5)

            row_frame.bind("<Enter>", lambda event, rf=row_frame: rf.configure(fg_color=("gray75", "gray25")))
            row_frame.bind("<Leave>", lambda event, rf=row_frame, i=idx: rf.configure(
                fg_color=("gray90", "gray20") if i % 2 == 0 else ("gray80", "gray30")))
            for child in row_frame.winfo_children():
                child.bind("<Enter>", lambda event, rf=row_frame: rf.configure(fg_color=("gray75", "gray25")))
                child.bind("<Leave>", lambda event, rf=row_frame, i=idx: rf.configure(
                    fg_color=("gray90", "gray20") if i % 2 == 0 else ("gray80", "gray30")))

            self.schedule_rows.append((item_id, row_frame))
        self._fade_in_schedule()

    def _select_schedule(self, schedule_id):
        self.selected_schedule_id = schedule_id
        for item_id, row_frame in self.schedule_rows:
            idx = self.schedule_data.index(next(item for item in self.schedule_data if item.get('id') == item_id))
            if item_id == schedule_id:
                row_frame.configure(fg_color=("gray70", "gray50"))
                for widget in row_frame.winfo_children():
                    widget.configure(fg_color=("gray70", "gray50") if widget.cget("text") != "High" and
                                    widget.cget("text") != "Medium" and widget.cget("text") != "Low" else None)
            else:
                row_frame.configure(fg_color=("gray90", "gray20") if idx % 2 == 0 else ("gray80", "gray30"))
                for widget in row_frame.winfo_children():
                    widget.configure(fg_color="transparent" if widget.cget("text") != "High" and
                                    widget.cget("text") != "Medium" and widget.cget("text") != "Low" else None)

    def _clear_fields(self):
        self.subject_entry.delete(0, "end")
        self.topic_entry.delete(0, "end")
        self.time_entry.delete(0, "end")
        self.priority_var.set("Medium")
        if self.selected_schedule_id:
            self.selected_schedule_id = None
            self._populate_schedule_display()

    def _add_schedule(self):
        subject = self.subject_entry.get()
        topic = self.topic_entry.get()
        time_str = self.time_entry.get()
        priority = self.priority_var.get()

        # Validation
        if not validate_not_empty(subject, "Subject"):
            CTkMessagebox(title="Input Error", message="Subject cannot be empty.", icon="warning").get()
            return
        if not validate_not_empty(topic, "Topic"):
            CTkMessagebox(title="Input Error", message="Topic cannot be empty.", icon="warning").get()
            return
        if not validate_time_range(time_str, "Time"):
            CTkMessagebox(title="Input Error", message="Invalid time format. Use YYYY-MM-DD HH:MM-HH:MM.", icon="warning").get()
            return
        if not priority:
            CTkMessagebox(title="Input Error", message="Please select a priority.", icon="warning").get()
            return

        self.add_button.pack_forget()
        self.delete_button.pack_forget()
        self.clear_button.pack_forget()
        self.progress_bar.pack(side="left", padx=5)
        self.progress_bar.start()
        self.after(1000, self._complete_add_schedule, subject, topic, time_str, priority)

    def _complete_add_schedule(self, subject, topic, time_str, priority):
        new_schedule = {
            'id': str(self.next_id),
            'subject': subject,
            'topic': topic,
            'time': time_str,
            'priority': priority,
            'student_id': self.username
        }
        self.schedule_data.append(new_schedule)
        self.next_id += 1
        self._save_schedules()
        self._populate_schedule_display()

        self.subject_entry.delete(0, "end")
        self.topic_entry.delete(0, "end")
        self.time_entry.delete(0, "end")
        self.priority_var.set("Medium")

        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.add_button.pack(side="left", padx=5)
        self.delete_button.pack(side="left", padx=5)
        self.clear_button.pack(side="left", padx=5)

        CTkMessagebox(title="Success", message="Schedule added successfully!", icon="check").get()

    def _delete_schedule(self):
        if not self.selected_schedule_id:
            CTkMessagebox(title="Selection Error", message="Please select a schedule to delete.", icon="warning").get()
            return

        if CTkMessagebox(title="Confirm Delete", message="Are you sure you want to delete this schedule?",
                         option_1="Yes", option_2="No").get() == "Yes":
            self.schedule_data = [item for item in self.schedule_data if item.get('id') != self.selected_schedule_id]
            self._save_schedules()
            self._populate_schedule_display()
            CTkMessagebox(title="Success", message="Schedule deleted successfully!", icon="check").get()

    def _check_reminders(self):
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        current_hour_minute = now.strftime("%H:%M")

        for item in self.schedule_data:
            time_str = item.get('time', '')
            if not time_str:
                continue

            try:
                parts = time_str.split(' ')
                if len(parts) == 2:
                    date_part = parts[0]
                    time_range = parts[1]
                    start_time_str = time_range.split('-')[0]

                    if date_part == today_str and start_time_str == current_hour_minute:
                        subject = item.get('subject', 'N/A')
                        topic = item.get('topic', 'N/A')
                        CTkMessagebox(
                            title="Study Reminder",
                            message=f"Time for your study session!\n\nSubject: {subject}\nTopic: {topic}\nTime: {start_time_str}",
                            icon="info"
                        ).get()
            except Exception as e:
                print(f"Error parsing time for reminder: {time_str} - {e}")

        self.after(60000, self._check_reminders)

    def apply_theme(self, theme):
        if theme == "light":
            self.header_frame.configure(fg_color="#d3d3d3")
        else:
            self.header_frame.configure(fg_color="#555555")