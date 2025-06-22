import customtkinter as ctk
from customtkinter import CTkFrame, CTkLabel, CTkOptionMenu, CTkProgressBar, CTkEntry, CTkButton
from utils import (get_student_data_path, read_csv, write_csv,
                   DATE_FORMAT, get_current_date_str, parse_date_str)
import os
from collections import defaultdict
from datetime import datetime
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from CTkMessagebox import CTkMessagebox
import random

# Constants
PROGRESS_FILE = "progress.csv"
PROGRESS_HEADERS = ['date', 'subject', 'study_hours', 'cards_reviewed', 'student_id']
USERS_FILE = "data/users.csv"
USER_HEADERS = ['username', 'password', 'role', 'linked_student']

# Progress Tips
PROGRESS_TIPS = [
    "Track your progress daily to stay motivated!",
    "Set small, achievable study goals for each session.",
    "Review your metrics weekly to identify improvement areas.",
    "Celebrate milestones to keep your momentum going!",
    "Mix subjects to keep your study sessions engaging!"
]

def create_matplotlib_chart(parent_frame, data_dict, title, xlabel, ylabel, theme="light"):
    """Creates a Matplotlib bar chart and embeds it into the parent frame."""
    for widget in parent_frame.winfo_children():
        if isinstance(widget, CTkLabel) and widget.cget("text") == "Study Hours per Subject":
            continue
        widget.destroy()

    fig, ax = plt.subplots(figsize=(6, 4))
    
    # Enhanced theme-specific styling
    if theme == "dark":
        fig.patch.set_facecolor("#1a2a44")
        ax.set_facecolor("#2b2b2b")
        ax.tick_params(colors="white", labelsize=10)
        ax.xaxis.label.set_color("white")
        ax.yaxis.label.set_color("white")
        ax.title.set_color("white")
        bar_color = "#4a90e2"
        text_color = "white"
    else:
        fig.patch.set_facecolor("#e6f0ff")
        ax.set_facecolor("#ffffff")
        ax.tick_params(colors="black", labelsize=10)
        ax.xaxis.label.set_color("black")
        ax.yaxis.label.set_color("black")
        ax.title.set_color("black")
        bar_color = "#1f77b4"
        text_color = "black"

    if data_dict:
        subjects = list(data_dict.keys())
        hours = list(data_dict.values())
        bars = ax.bar(subjects, hours, color=bar_color, edgecolor="white", linewidth=0.5)
        
        # Add value labels on top of bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, height, f"{height:.1f}",
                    ha="center", va="bottom", color=text_color, fontsize=9, fontweight="bold")
        
        ax.set_title(title, fontsize=12, fontweight="bold", pad=15)
        ax.set_xlabel(xlabel, fontsize=10)
        ax.set_ylabel(ylabel, fontsize=10)
        plt.xticks(rotation=45, ha="right", fontsize=9)
        plt.tight_layout()
    else:
        ax.text(0.5, 0.5, "No data available", horizontalalignment="center",
                verticalalignment="center", fontsize=12, color=text_color)
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.set_xlabel(xlabel, fontsize=10)
        ax.set_ylabel(ylabel, fontsize=10)
        ax.set_xticks([])
        ax.set_yticks([])

    canvas = FigureCanvasTkAgg(fig, master=parent_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

    return canvas

# Helper functions (assumed to be in utils.py or auth.py)
def student_exists(student_id):
    """Check if a student exists in users.csv."""
    if not student_id:
        return False
    users = read_csv(USERS_FILE, USER_HEADERS)
    return any(user['username'] == student_id and user['role'] == "student" for user in users)

def update_linked_student(parent_username, new_student_id):
    """Update the linked_student field for a parent in users.csv."""
    users = read_csv(USERS_FILE, USER_HEADERS)
    for user in users:
        if user['username'] == parent_username:
            user['linked_student'] = new_student_id
            break
    write_csv(USERS_FILE, users, USER_HEADERS)

class ProgressTab(CTkFrame):
    """GUI Frame for displaying study progress."""
    def __init__(self, parent, username, role, linked_student=None):
        super().__init__(parent, corner_radius=15, fg_color=("#e6f0ff", "#1a2a44"))
        self.current_user_role = role
        self.current_username = username  # Store the parent's username
        self.student_username = linked_student if role == "parent" else username
        self.is_read_only = (role == "parent")
        self.progress_file_path = get_student_data_path(self.student_username, PROGRESS_FILE)

        # Inner frame for shadow effect
        self.inner_frame = CTkFrame(self, corner_radius=15, fg_color=("#ffffff", "#2b2b2b"),
                                    border_width=2, border_color=("#1f77b4", "#4a90e2"))
        self.inner_frame.pack(padx=5, pady=5, fill="both", expand=True)

        # --- Top Frame ---
        self.top_frame = CTkFrame(self.inner_frame, fg_color="transparent")
        self.top_frame.pack(pady=10, padx=10, fill="x")

        self.progress_title_label = CTkLabel(self.top_frame, text="", font=("Comic Sans MS", 18, "bold"))
        self.progress_title_label.pack(side="left")
        self._animate_title(self.progress_title_label, f"Progress for: {self.student_username}")

        if self.is_read_only:
            CTkLabel(self.top_frame, text="(Read-Only)", text_color="orange", font=("Helvetica", 12)).pack(side="left", padx=10)

        # Check if the linked student exists (for parents only)
        self.link_frame = None
        if self.is_read_only and not student_exists(self.student_username):
            self._show_link_student_option()
        else:
            self._build_progress_ui()

    def _show_link_student_option(self):
        """Display a UI to link or re-link a student if the current linked student is invalid."""
        # Clear any existing UI
        for widget in self.inner_frame.winfo_children():
            widget.destroy()

        # Warning message
        warning_label = CTkLabel(self.inner_frame, text=f"⚠️ The linked student '{self.student_username}' does not exist.",
                                 text_color="orange", font=("Helvetica", 14, "bold"), wraplength=500)
        warning_label.pack(pady=10)

        # Instruction
        instruction_label = CTkLabel(self.inner_frame, text="Please enter a valid student username to link:",
                                     font=("Helvetica", 12), wraplength=500)
        instruction_label.pack(pady=5)

        # Entry field for new student ID
        self.new_student_entry = CTkEntry(self.inner_frame, placeholder_text="Enter student username",
                                          width=200, corner_radius=8, font=("Helvetica", 12))
        self.new_student_entry.pack(pady=10)

        # Link button
        link_button = CTkButton(self.inner_frame, text="Link Student", command=self._link_new_student,
                                fg_color=("#1f77b4", "#4a90e2"), hover_color=("#165a92", "#357abd"),
                                corner_radius=8, font=("Helvetica", 12, "bold"))
        link_button.pack(pady=10)
        link_button.bind("<Enter>", lambda event: self._scale_button_in(link_button))
        link_button.bind("<Leave>", lambda event: self._scale_button_out(link_button))

    def _link_new_student(self):
        """Validate and link a new student ID, then rebuild the UI."""
        new_student_id = self.new_student_entry.get().strip()
        
        # Validate the new student ID
        if not new_student_id:
            CTkMessagebox(title="Error", message="Student username cannot be empty.", icon="cancel").get()
            self._shake_animation()
            return

        if not student_exists(new_student_id):
            CTkMessagebox(title="Error", message=f"Student '{new_student_id}' does not exist.", icon="cancel").get()
            self._shake_animation()
            return

        # Update the linked_student field in users.csv
        update_linked_student(self.current_username, new_student_id)

        # Update the internal state
        self.student_username = new_student_id
        self.progress_file_path = get_student_data_path(self.student_username, PROGRESS_FILE)

        # Rebuild the progress UI
        self._build_progress_ui()
        self._update_display()

        # Update the title
        self.progress_title_label.configure(text="")
        self._animate_title(self.progress_title_label, f"Progress for: {self.student_username}")

    def _build_progress_ui(self):
        """Build the main progress UI after linking is resolved."""
        # Clear the link UI if it exists
        for widget in self.inner_frame.winfo_children():
            widget.destroy()

        # Rebuild the top frame
        self.top_frame = CTkFrame(self.inner_frame, fg_color="transparent")
        self.top_frame.pack(pady=10, padx=10, fill="x")

        self.progress_title_label = CTkLabel(self.top_frame, text="", font=("Comic Sans MS", 18, "bold"))
        self.progress_title_label.pack(side="left")
        self._animate_title(self.progress_title_label, f"Progress for: {self.student_username}")

        if self.is_read_only:
            CTkLabel(self.top_frame, text="(Read-Only)", text_color="orange", font=("Helvetica", 12)).pack(side="left", padx=10)

            # Add a "Change Linked Student" button for parents
            self.link_frame = CTkFrame(self.inner_frame, fg_color="transparent")
            self.link_frame.pack(pady=5, padx=10, fill="x")
            change_link_button = CTkButton(self.link_frame, text="Change Linked Student", command=self._show_link_student_option,
                                           fg_color=("#ff9500", "#ff9500"), hover_color=("#cc7700", "#cc7700"),
                                           corner_radius=8, font=("Helvetica", 12, "bold"))
            change_link_button.pack(side="left", padx=5)
            change_link_button.bind("<Enter>", lambda event: self._scale_button_in(change_link_button))
            change_link_button.bind("<Leave>", lambda event: self._scale_button_out(change_link_button))

        # Progress Tip
        tip = random.choice(PROGRESS_TIPS)
        CTkLabel(self.inner_frame, text=f"💡 Tip: {tip}", font=("Helvetica", 10, "italic"),
                 wraplength=600).pack(pady=5)

        # --- Filtering Frame ---
        filter_frame = CTkFrame(self.inner_frame, fg_color="transparent")
        filter_frame.pack(pady=5, padx=10, fill="x")
        CTkLabel(filter_frame, text="📚 Filter by Subject:", width=120, anchor="w",
                 font=("Helvetica", 12)).pack(side="left", padx=5)
        self.subject_filter_var = ctk.StringVar(value="All")
        self.subject_filter_menu = CTkOptionMenu(
            filter_frame,
            variable=self.subject_filter_var,
            values=["All"],
            command=self._update_display,
            width=200,
            corner_radius=8,
            fg_color=("#1f77b4", "#4a90e2"),
            button_color=("#165a92", "#357abd"),
            button_hover_color=("#0f4a7b", "#2a6aa3"),
            text_color=("white", "white"),
            font=("Helvetica", 12)
        )
        self.subject_filter_menu.pack(side="left", padx=5)
        self.subject_filter_menu.bind("<Enter>", lambda event: self._scale_menu_in(self.subject_filter_menu))
        self.subject_filter_menu.bind("<Leave>", lambda event: self._scale_menu_out(self.subject_filter_menu))

        # --- Metrics Display Frame ---
        self.metrics_frame = CTkFrame(self.inner_frame, corner_radius=10, fg_color=("#f5f5f5", "#333333"))
        self.metrics_frame.pack(pady=10, padx=10, fill="x")
        CTkLabel(self.metrics_frame, text="Summary Metrics", font=("Helvetica", 14, "bold")).pack(anchor="w", pady=5)

        self.total_hours_label = CTkLabel(self.metrics_frame, text="⏰ Total Study Hours: N/A", anchor="w",
                                          font=("Helvetica", 12))
        self.total_hours_label.pack(anchor="w", pady=2)
        self.total_cards_label = CTkLabel(self.metrics_frame, text="📝 Total Flashcards Reviewed: N/A", anchor="w",
                                          font=("Helvetica", 12))
        self.total_cards_label.pack(anchor="w", pady=2)
        self.hours_per_subject_label = CTkLabel(self.metrics_frame, text="📊 Hours per Subject: N/A", anchor="w",
                                                font=("Helvetica", 12))
        self.hours_per_subject_label.pack(anchor="w", pady=2)

        # --- Chart Display Frame ---
        self.chart_frame = CTkFrame(self.inner_frame, corner_radius=10, fg_color=("#f5f5f5", "#333333"))
        self.chart_frame.pack(pady=10, padx=10, fill="both", expand=True)
        CTkLabel(self.chart_frame, text="Study Hours per Subject", font=("Helvetica", 14, "bold")).pack(anchor="w", pady=5)

        # Progress Bar for Chart Loading
        self.chart_progress_bar = CTkProgressBar(self.chart_frame, mode="indeterminate", width=200)
        self.chart_progress_bar.pack(pady=10)
        self.chart_progress_bar.start()
        self.chart_canvas = None

        # Load and display initial data
        self._update_display()

    def _animate_title(self, label, text, index=0):
        """Animates the title by typing it out."""
        if index <= len(text):
            label.configure(text=text[:index])
            self.after(50, self._animate_title, label, text, index + 1)

    def _scale_menu_in(self, menu):
        """Scale menu up on hover."""
        menu.configure(height=32)

    def _scale_menu_out(self, menu):
        """Scale menu back on hover out."""
        menu.configure(height=30)

    def _scale_button_in(self, button):
        """Scale button up on hover."""
        button.configure(height=32)

    def _scale_button_out(self, button):
        """Scale button back on hover out."""
        button.configure(height=30)

    def _shake_animation(self):
        """Shakes the inner frame on error."""
        def shake(step=0, direction=1):
            if step < 6:
                offset = 5 * direction
                self.inner_frame.place_configure(relx=0.5, rely=0.5, x=offset, anchor="center")
                self.after(50, shake, step + 1, -direction)
            else:
                self.inner_frame.place_configure(relx=0.5, rely=0.5, x=0, anchor="center")
        shake()

    def _fade_in_metrics(self):
        """Simulates a fade-in effect for metrics by ensuring visibility."""
        self.metrics_frame.pack(pady=10, padx=10, fill="x")

    def _load_progress_data(self):
        if not os.path.exists(self.progress_file_path):
            write_csv(self.progress_file_path, [], PROGRESS_HEADERS)
        return read_csv(self.progress_file_path, PROGRESS_HEADERS)

    def _calculate_metrics(self, progress_data, subject_filter="All"):
        total_hours = 0.0
        total_cards = 0
        hours_by_subject = defaultdict(float)
        subjects = set(["All"])

        for entry in progress_data:
            try:
                subject = entry.get('subject', 'Unknown')
                subjects.add(subject)

                if subject_filter == "All" or subject == subject_filter:
                    hours = float(entry.get('study_hours', 0))
                    cards = int(entry.get('cards_reviewed', 0))

                    total_hours += hours
                    total_cards += cards
                    hours_by_subject[subject] += hours

            except (ValueError, TypeError) as e:
                print(f"Warning: Skipping invalid progress entry: {entry}. Error: {e}")
                continue

        return {
            "total_hours": total_hours,
            "total_cards": total_cards,
            "hours_by_subject": dict(hours_by_subject),
            "all_subjects": sorted(list(subjects))
        }

    def _update_display(self, event=None):
        progress_data = self._load_progress_data()
        current_filter = self.subject_filter_var.get()

        metrics = self._calculate_metrics(progress_data, current_filter)

        self.subject_filter_menu.configure(values=metrics["all_subjects"])
        if current_filter not in metrics["all_subjects"]:
            self.subject_filter_var.set("All")
            metrics = self._calculate_metrics(progress_data, "All")

        # Update metrics with icons
        self.total_hours_label.configure(text=f"⏰ Total Study Hours ({current_filter}): {metrics['total_hours']:.2f}")
        self.total_cards_label.configure(text=f"📝 Total Flashcards Reviewed ({current_filter}): {metrics['total_cards']}")
        
        if current_filter == "All":
            hours_text = "📊 Hours per Subject: " + ", ".join([f"{s}: {h:.2f}" for s, h in metrics['hours_by_subject'].items()])
            self.hours_per_subject_label.configure(text=hours_text if metrics['hours_by_subject'] else "📊 Hours per Subject: None")
        else:
            self.hours_per_subject_label.configure(text="")

        self._fade_in_metrics()

        # Update chart with a progress bar animation
        self.chart_progress_bar.pack(pady=10)
        self.chart_progress_bar.start()
        self.after(1000, self._complete_chart_update, progress_data)

    def _complete_chart_update(self, progress_data):
        current_filter = self.subject_filter_var.get()
        chart_metrics = self._calculate_metrics(progress_data, "All")
        
        if not chart_metrics["hours_by_subject"]:
            CTkMessagebox(title="No Data", message="No study data available to display.", icon="info").get()
            self._shake_animation()

        theme = ctk.get_appearance_mode().lower()
        self.chart_canvas = create_matplotlib_chart(
            parent_frame=self.chart_frame,
            data_dict=chart_metrics['hours_by_subject'],
            title="Total Study Hours per Subject",
            xlabel="Subject",
            ylabel="Total Hours",
            theme=theme
        )

        self.chart_progress_bar.stop()
        self.chart_progress_bar.pack_forget()

    def apply_theme(self, theme):
        self._update_display()

def log_study_session(username, subject, hours, cards, log_date=None):
    if not username: return
    if hours <= 0 and cards <= 0: return

    file_path = get_student_data_path(username, PROGRESS_FILE)
    headers = PROGRESS_HEADERS
    today_str = log_date if log_date and parse_date_str(log_date) else get_current_date_str()

    progress_data = read_csv(file_path, headers)

    updated = False
    for entry in progress_data:
        if entry.get('date') == today_str and entry.get('subject') == subject and entry.get('student_id') == username:
            try:
                entry['study_hours'] = str(float(entry.get('study_hours', 0)) + hours)
                entry['cards_reviewed'] = str(int(entry.get('cards_reviewed', 0)) + cards)
                updated = True
                break
            except (ValueError, TypeError):
                print(f"Error updating progress entry: {entry}")
                continue

    if not updated:
        new_entry = {
            'date': today_str,
            'subject': subject,
            'study_hours': str(hours),
            'cards_reviewed': str(cards),
            'student_id': username
        }
        progress_data.append(new_entry)

    write_csv(file_path, progress_data, headers)
    print(f"Progress logged for {username}: {subject} - {hours:.2f} hrs, {cards} cards on {today_str}")