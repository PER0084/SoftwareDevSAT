import customtkinter as ctk
from customtkinter import CTk, CTkFrame, CTkLabel, CTkButton, CTkEntry, CTkTabview
from utils import get_current_datetime_str, TIME_FORMAT_DISPLAY, ensure_dir_exists, read_csv, write_csv
from auth import LoginScreen, SignupScreen, AuthManager
from notes import NotesTab
from scheduling import SchedulingTab
from flashcards import FlashcardsTab
from progress import ProgressTab, log_study_session as log_flashcard_progress
from CTkMessagebox import CTkMessagebox
import sys
import os

# Constants for user data
USERS_FILE = "data/users.csv"
USER_HEADERS = ['username', 'password', 'role', 'linked_student']

class StudyBuddyApp(CTk):
    """Main application class for Study Buddy."""
    def __init__(self):
        super().__init__()
        self.title("Study Buddy")
        self.geometry("900x650")  # Adjusted size for potentially large tables/charts

        # Ensure base data directory exists
        ensure_dir_exists("data")

        self.auth_manager = AuthManager()
        self.current_user = None
        self.current_role = None
        self.linked_student = None  # For parent role
        self.current_theme = "light"  # Default theme

        # Set CustomTkinter appearance mode (light/dark)
        ctk.set_appearance_mode("light")  # Start with light mode (blue-and-white)
        ctk.set_default_color_theme("blue")  # Use blue theme to align with design brief

        # --- Top Bar Frame (Clock, Theme Toggle, Logout, Exit) ---
        self.top_bar = CTkFrame(self, corner_radius=0)
        # Don't pack top_bar yet, show after login

        self.clock_label = CTkLabel(self.top_bar, text="", font=("Helvetica", 12))
        self.theme_button = CTkButton(self.top_bar, text="Toggle Dark Mode", command=self._toggle_theme, corner_radius=8)
        self.logout_button = CTkButton(
            self.top_bar,
            text="Logout 🔓",
            command=self._logout,
            corner_radius=8,
            font=("Helvetica", 12, "bold"),
            fg_color=("#1f77b4", "#4a90e2"),
            hover_color=("#165a92", "#357abd")
        )
        self.logout_button.bind("<Enter>", lambda event: self._scale_button_in(self.logout_button))
        self.logout_button.bind("<Leave>", lambda event: self._scale_button_out(self.logout_button))

        # Exit Button
        self.exit_button = CTkButton(
            self.top_bar,
            text="Exit 🚪",
            command=self._exit_program,
            corner_radius=8,
            font=("Helvetica", 12, "bold"),
            fg_color=("#ff3b30", "#cc2f27"),
            hover_color=("#e6352b", "#b32923")
        )
        self.exit_button.bind("<Enter>", lambda event: self._scale_button_in(self.exit_button))
        self.exit_button.bind("<Leave>", lambda event: self._scale_button_out(self.exit_button))

        # --- Main Content Area ---
        self.main_content_frame = CTkFrame(self, corner_radius=0)
        self.main_content_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Initial State: Show Login Screen ---
        self._show_login_screen()

        # Start clock update loop (will be visible once top_bar is packed)
        self._update_clock()

    def _scale_button_in(self, button):
        """Scale button up on hover."""
        button.configure(height=32)

    def _scale_button_out(self, button):
        """Scale button back on hover out."""
        button.configure(height=30)

    def _exit_program(self):
        """Handle program exit with confirmation."""
        if CTkMessagebox(title="Confirm Exit", message="Are you sure you want to exit the program?\nAll unsaved changes will be lost.",
                         option_1="Yes", option_2="No").get() == "Yes":
            sys.exit()

    def _clear_main_content(self):
        """Removes all widgets from the main content frame."""
        for widget in self.main_content_frame.winfo_children():
            widget.destroy()
        # Hide top bar when logged out
        self.top_bar.pack_forget()

    def _show_login_screen(self):
        """Displays the login screen."""
        self._clear_main_content()
        self.title("Study Buddy - Login")
        login_frame = LoginScreen(self.main_content_frame, self)  # Assumes LoginScreen uses CustomTkinter
        login_frame.pack(pady=50, padx=20, expand=True)

    def _show_signup_screen(self):
        """Displays the signup screen."""
        self._clear_main_content()
        self.title("Study Buddy - Sign Up")
        signup_frame = SignupScreen(self.main_content_frame, self)  # Assumes SignupScreen uses CustomTkinter
        signup_frame.pack(pady=50, padx=20, expand=True)

    def _student_exists(self, student_id):
        """Check if a student exists in users.csv."""
        if not student_id:
            return False
        users = read_csv(USERS_FILE, USER_HEADERS)
        return any(user['username'] == student_id and user['role'] == "student" for user in users)

    def _update_linked_student(self, new_student_id):
        """Update the linked_student field for the current parent in users.csv."""
        users = read_csv(USERS_FILE, USER_HEADERS)
        for user in users:
            if user['username'] == self.current_user:
                user['linked_student'] = new_student_id
                break
        write_csv(USERS_FILE, users, USER_HEADERS)
        self.linked_student = new_student_id

    def _show_link_student_screen(self):
        """Display a UI for the parent to link or re-link a student."""
        self._clear_main_content()
        self.title(f"Study Buddy - Link Student ({self.current_user})")

        link_frame = CTkFrame(self.main_content_frame, corner_radius=15, fg_color=("#e6f0ff", "#1a2a44"))
        link_frame.pack(pady=50, padx=20, expand=True)

        # Warning message
        warning_label = CTkLabel(link_frame, text=f"⚠️ The linked student '{self.linked_student}' does not exist.",
                                 text_color="orange", font=("Helvetica", 14, "bold"), wraplength=500)
        warning_label.pack(pady=10)

        # Instruction
        instruction_label = CTkLabel(link_frame, text="Please enter a valid student username to link:",
                                     font=("Helvetica", 12), wraplength=500)
        instruction_label.pack(pady=5)

        # Entry field for new student ID
        self.new_student_entry = CTkEntry(link_frame, placeholder_text="Enter student username",
                                          width=200, corner_radius=8, font=("Helvetica", 12))
        self.new_student_entry.pack(pady=10)

        # Link button
        link_button = CTkButton(link_frame, text="Link Student", command=self._link_new_student,
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

            return

        if not self._student_exists(new_student_id):
            CTkMessagebox(title="Error", message=f"Student '{new_student_id}' does not exist.", icon="cancel").get()

            return

        # Update the linked_student field in users.csv
        self._update_linked_student(new_student_id)

        # Rebuild the interface with the updated linked_student
        user_data = {
            'username': self.current_user,
            'role': self.current_role,
            'linked_student': self.linked_student
        }
        self._post_login_setup(user_data)


    def _post_login_setup(self, user_data):
        """Sets up the main interface after successful login."""
        self.current_user = user_data['username']
        self.current_role = user_data['role']
        self.linked_student = user_data.get('linked_student')  # Might be None or empty

        # For parents, verify the linked student exists
        if self.current_role == "parent" and (not self.linked_student or not self._student_exists(self.linked_student)):
            self._show_link_student_screen()
            return

        self._clear_main_content()
        self.title(f"Study Buddy - {self.current_user} ({self.current_role})")

        # Pack the top bar now
        self.theme_button.pack(side="left", padx=10, pady=5)
        self.logout_button.pack(side="left", padx=10, pady=5)
        self.exit_button.pack(side="left", padx=10, pady=5)
        self.clock_label.pack(side="right", padx=10, pady=5)
        self.top_bar.pack(fill="x", side="top")

        # --- Tabbed Interface ---
        self.notebook = CTkTabview(self.main_content_frame, corner_radius=10)

        if self.current_role == "student":
            # Add tabs for students
            self.notebook.add("Scheduling")
            self.notebook.add("Notes")
            self.notebook.add("Flashcards")
            self.notebook.add("Progress")

            # Initialize tab content
            self.schedule_tab = SchedulingTab(self.notebook.tab("Scheduling"), self.current_user)
            self.notes_tab = NotesTab(self.notebook.tab("Notes"), self.current_user)
            self.flashcards_tab = FlashcardsTab(self.notebook.tab("Flashcards"), self.current_user, log_flashcard_progress)
            self.progress_tab = ProgressTab(self.notebook.tab("Progress"), self.current_user, self.current_role)

            # Pack tab content
            self.schedule_tab.pack(fill="both", expand=True, padx=10, pady=10)
            self.notes_tab.pack(fill="both", expand=True, padx=10, pady=10)
            self.flashcards_tab.pack(fill="both", expand=True, padx=10, pady=10)
            self.progress_tab.pack(fill="both", expand=True, padx=10, pady=10)

        elif self.current_role == "parent":
            # Add only Progress tab for parents
            self.notebook.add(f"Progress ({self.linked_student})")
            self.progress_tab = ProgressTab(self.notebook.tab(f"Progress ({self.linked_student})"), self.current_user, self.current_role, self.linked_student)
            self.progress_tab.pack(fill="both", expand=True, padx=10, pady=10)

        self.notebook.pack(pady=10, padx=10, fill="both", expand=True)

        # Apply theme to initially loaded tabs
        self._apply_theme_to_tabs()

    def _logout(self):
        """Logs the current user out and returns to the login screen."""
        if CTkMessagebox(title="Logout", message="Are you sure you want to log out?", option_1="Yes", option_2="No").get() == "Yes":
            self.current_user = None
            self.current_role = None
            self.linked_student = None
            # Destroy specific tab references
            self.schedule_tab = None
            self.notes_tab = None
            self.flashcards_tab = None
            self.progress_tab = None
            self._show_login_screen()

    def _update_clock(self):
        """Updates the clock label every second."""
        now_str = get_current_datetime_str(fmt=TIME_FORMAT_DISPLAY)
        self.clock_label.configure(text=now_str)
        self.after(1000, self._update_clock)  # Schedule next update

    def _toggle_theme(self):
        """Switches between light and dark themes."""
        if self.current_theme == "light":
            self.current_theme = "dark"
            ctk.set_appearance_mode("dark")
            self.theme_button.configure(text="Toggle Light Mode")
        else:
            self.current_theme = "light"
            ctk.set_appearance_mode("light")
            self.theme_button.configure(text="Toggle Dark Mode")

        # Apply the new theme to tabs
        self._apply_theme_to_tabs()

    def _apply_theme_to_tabs(self):
        """Applies theme settings to widgets within tabs that need manual updates."""
        if hasattr(self, 'notes_tab') and self.notes_tab:
            self.notes_tab.apply_theme(self.current_theme)
        if hasattr(self, 'progress_tab') and self.progress_tab:
            self.progress_tab.apply_theme(self.current_theme)
        if hasattr(self, 'schedule_tab') and self.schedule_tab:
            self.schedule_tab.apply_theme(self.current_theme)
        if hasattr(self, 'flashcards_tab') and self.flashcards_tab:
            self.flashcards_tab.apply_theme(self.current_theme)

    def run(self):
        """Starts the CustomTkinter main event loop."""
        self.mainloop()
    

# --- Entry Point ---
if __name__ == "__main__":
    app = StudyBuddyApp()
    app.run()