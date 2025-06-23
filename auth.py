import customtkinter as ctk
from customtkinter import CTkFrame, CTkLabel, CTkEntry, CTkButton, CTkRadioButton, CTkCheckBox, CTkProgressBar
from utils import (USERS_FILE, read_csv, write_csv, hash_password,
                   verify_password, ensure_dir_exists, get_student_dir,
                   validate_not_empty)
import os
from CTkMessagebox import CTkMessagebox
import random

USER_HEADERS = ['username', 'password', 'role', 'linked_student']

# Motivational quotes to display
MOTIVATIONAL_QUOTES = [
    "The beautiful thing about learning is that no one can take it away from you. – B.B. King",
    "Education is the most powerful weapon which you can use to change the world. – Nelson Mandela",
    "Study hard, for the well is deep, and our brains are shallow. – Richard Baxter",
    "Success is the sum of small efforts, repeated day in and day out. – Robert Collier",
    "The only way to do great work is to love what you do. – Steve Jobs"
]

class AuthManager:
    """Handles user authentication (login, signup)."""
    def __init__(self):
        ensure_dir_exists(os.path.dirname(USERS_FILE))
        if not os.path.exists(USERS_FILE) or os.path.getsize(USERS_FILE) == 0:
            write_csv(USERS_FILE, [], USER_HEADERS)

    def _get_users(self):
        return read_csv(USERS_FILE, USER_HEADERS)

    def _save_users(self, users):
        write_csv(USERS_FILE, users, USER_HEADERS)

    def user_exists(self, username):
        users = self._get_users()
        return any(user['username'].lower() == username.lower() for user in users)

    def signup(self, username, password, role, linked_student=None):
        if not validate_not_empty(username, "Username"): return False, "Username cannot be empty."
        if not validate_not_empty(password, "Password"): return False, "Password cannot be empty."
        if role not in ["student", "parent"]: return False, "Invalid role specified."
        if role == "parent" and not validate_not_empty(linked_student, "Linked Student ID"):
            return False, "Parent must provide a Linked Student ID."
        if self.user_exists(username):
            return False, f"Username '{username}' already exists."
        if role == "parent":
            all_users = self._get_users()
            if not any(u['username'] == linked_student and u['role'] == 'student' for u in all_users):
                proceed = CTkMessagebox(
                    title="Student Not Found",
                    message=f"Student ID '{linked_student}' was not found. "
                            f"Do you want to create the parent account anyway? "
                            f"(Ensure the student signs up later with this exact ID).",
                    option_1="Yes",
                    option_2="No"
                ).get() == "Yes"
                if not proceed:
                    return False, "Signup cancelled."

        hashed_pwd = hash_password(password)
        new_user = {
            'username': username,
            'password': hashed_pwd,
            'role': role,
            'linked_student': linked_student if role == "parent" else ""
        }

        users = self._get_users()
        users.append(new_user)
        self._save_users(users)

        if role == 'student':
            get_student_dir(username)

        return True, "Signup successful!"

    def login(self, username, password):
        if not validate_not_empty(username, "Username"): return None, "Username cannot be empty."
        if not validate_not_empty(password, "Password"): return None, "Password cannot be empty."

        users = self._get_users()
        for user in users:
            if user['username'].lower() == username.lower():
                if verify_password(user['password'], password):
                    return user, f"Login successful as {user['role']}."
                else:
                    return None, "Invalid password."
        return None, f"Username '{username}' not found."

# --- GUI Components for Auth ---

class LoginScreen(CTkFrame):
    """GUI Frame for user login."""
    def __init__(self, parent, app_controller):
        super().__init__(parent, corner_radius=15, fg_color=("#e6f0ff", "#1a2a44"))
        self.app = app_controller
        self.auth_manager = app_controller.auth_manager
        self.pack(pady=50, padx=20, expand=True)

        # Inner frame for shadow effect
        self.inner_frame = CTkFrame(self, corner_radius=15, fg_color=("#ffffff", "#2b2b2b"), border_width=2, border_color=("#1f77b4", "#4a90e2"))
        self.inner_frame.pack(padx=5, pady=5, fill="both", expand=True)

        # Animated Title
        self.title_label = CTkLabel(self.inner_frame, text="", font=("Comic Sans MS", 24, "bold"))
        self.title_label.pack(pady=10)
        self._animate_title("Login to Study Buddy")

        # Motivational Quote
        quote = random.choice(MOTIVATIONAL_QUOTES)
        CTkLabel(self.inner_frame, text=quote, font=("Helvetica", 12, "italic"), wraplength=350).pack(pady=5)

        # Username
        f_user = CTkFrame(self.inner_frame, fg_color="transparent")
        CTkLabel(f_user, text="👤", font=("Helvetica", 16)).pack(side="left", padx=(5, 0))
        self.username_entry = CTkEntry(
            f_user,
            width=250,
            placeholder_text="Username",
            corner_radius=8,
            border_width=0,
            fg_color=("#f0f0f0", "#3a3a3a")
        )
        self.username_entry.pack(side="left", padx=5, pady=5, fill="x", expand=True)
        f_user.pack(pady=10, padx=20, fill="x")

        # Password
        f_pass = CTkFrame(self.inner_frame, fg_color="transparent")
        CTkLabel(f_pass, text="🔒", font=("Helvetica", 16)).pack(side="left", padx=(5, 0))
        self.password_entry = CTkEntry(
            f_pass,
            show="*",
            width=250,
            placeholder_text="Password",
            corner_radius=8,
            border_width=0,
            fg_color=("#f0f0f0", "#3a3a3a")
        )
        self.password_entry.pack(side="left", padx=5, pady=5, fill="x", expand=True)
        self.show_password_var = ctk.BooleanVar(value=False)
        CTkCheckBox(
            f_pass,
            text="Show",
            variable=self.show_password_var,
            command=self._toggle_password_visibility,
            fg_color=("#1f77b4", "#4a90e2"),
            hover_color=("#165a92", "#357abd")
        ).pack(side="left", padx=5)
        f_pass.pack(pady=10, padx=20, fill="x")

        # Progress Bar (hidden initially)
        self.progress_bar = CTkProgressBar(self.inner_frame, mode="indeterminate", width=200)
        self.progress_bar.pack_forget()

        # Login Button
        self.login_button = CTkButton(
            self.inner_frame,
            text="Login",
            command=self._perform_login,
            corner_radius=8,
            font=("Helvetica", 14, "bold"),
            height=40,
            fg_color=("#1f77b4", "#4a90e2"),
            hover_color=("#165a92", "#357abd")
        )
        self.login_button.pack(pady=15)
        self.login_button.bind("<Enter>", self._scale_button_in)
        self.login_button.bind("<Leave>", self._scale_button_out)

        # Sign Up Link
        signup_button = CTkButton(
            self.inner_frame,
            text="Need an account? Sign Up",
            command=self.app._show_signup_screen,
            fg_color="transparent",
            text_color=("blue", "lightblue"),
            hover_color=("gray90", "gray30"),
            font=("Helvetica", 12, "underline"),
            corner_radius=0
        )
        signup_button.pack(pady=5)

        # Bind Enter key
        self.username_entry.bind("<Return>", lambda event: self.password_entry.focus())
        self.password_entry.bind("<Return>", lambda event: self._perform_login())

        self.username_entry.focus()

    def _animate_title(self, text, index=0):
        """Animates the title by typing it out."""
        if index <= len(text):
            self.title_label.configure(text=text[:index])
            self.after(50, self._animate_title, text, index + 1)

    def _scale_button_in(self, event):
        """Scale button up on hover."""
        self.login_button.configure(height=42)

    def _scale_button_out(self, event):
        """Scale button back on hover out."""
        self.login_button.configure(height=40)

    def _toggle_password_visibility(self):
        """Toggles password visibility."""
        if self.show_password_var.get():
            self.password_entry.configure(show="")
        else:
            self.password_entry.configure(show="*")


    def _perform_login(self):
        # Show progress bar
        self.login_button.pack_forget()
        self.progress_bar.pack(pady=15)
        self.progress_bar.start()

        # Simulate processing
        self.after(1000, self._complete_login)

    def _complete_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        user_data, message = self.auth_manager.login(username, password)

        # Hide progress bar
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.login_button.pack(pady=15)

        if user_data:
            CTkMessagebox(title="Login Success", message=message, icon="check").get()
            self.app._post_login_setup(user_data)
        else:
            CTkMessagebox(title="Login Failed", message=message, icon="cancel").get()
            self.password_entry.delete(0, "end")
            

    def apply_theme(self, theme):
        pass

    def exit(self):
        """Exits the application."""
        self.app.quit()
        self.destroy()
        

class SignupScreen(CTkFrame):
    """GUI Frame for user signup."""
    def __init__(self, parent, app_controller):
        super().__init__(parent, corner_radius=15, fg_color=("#e6f0ff", "#1a2a44"))
        self.app = app_controller
        self.auth_manager = app_controller.auth_manager
        self.pack(pady=50, padx=20, expand=True)

        # Inner frame for shadow effect
        self.inner_frame = CTkFrame(self, corner_radius=15, fg_color=("#ffffff", "#2b2b2b"), border_width=2, border_color=("#1f77b4", "#4a90e2"))
        self.inner_frame.pack(padx=5, pady=5, fill="both", expand=True)

        # Animated Title
        self.title_label = CTkLabel(self.inner_frame, text="", font=("Comic Sans MS", 24, "bold"))
        self.title_label.pack(pady=10)
        self._animate_title("Join Study Buddy")
        
        
        # Motivational Quote
        quote = random.choice(MOTIVATIONAL_QUOTES)
        CTkLabel(self.inner_frame, text=quote, font=("Helvetica", 12, "italic"), wraplength=350).pack(pady=5)

        # Username
        f_user = CTkFrame(self.inner_frame, fg_color="transparent")
        CTkLabel(f_user, text="👤", font=("Helvetica", 16)).pack(side="left", padx=(5, 0))
        self.username_entry = CTkEntry(
            f_user,
            width=250,
            placeholder_text="Username",
            corner_radius=8,
            border_width=0,
            fg_color=("#f0f0f0", "#3a3a3a")
        )
        self.username_entry.pack(side="left", padx=5, pady=5, fill="x", expand=True)
        f_user.pack(pady=10, padx=20, fill="x")

        # Password
        f_pass = CTkFrame(self.inner_frame, fg_color="transparent")
        CTkLabel(f_pass, text="🔒", font=("Helvetica", 16)).pack(side="left", padx=(5, 0))
        self.password_entry = CTkEntry(
            f_pass,
            show="*",
            width=250,
            placeholder_text="Password",
            corner_radius=8,
            border_width=0,
            fg_color=("#f0f0f0", "#3a3a3a")
        )
        self.password_entry.pack(side="left", padx=5, pady=5, fill="x", expand=True)
        self.show_password_var = ctk.BooleanVar(value=False)
        CTkCheckBox(
            f_pass,
            text="Show",
            variable=self.show_password_var,
            command=self._toggle_password_visibility,
            fg_color=("#1f77b4", "#4a90e2"),
            hover_color=("#165a92", "#357abd")
        ).pack(side="left", padx=5)
        f_pass.pack(pady=10, padx=20, fill="x")

        # Confirm Password
        f_confirm_pass = CTkFrame(self.inner_frame, fg_color="transparent")
        CTkLabel(f_confirm_pass, text="🔒", font=("Helvetica", 16)).pack(side="left", padx=(5, 0))
        self.confirm_password_entry = CTkEntry(
            f_confirm_pass,
            show="*",
            width=250,
            placeholder_text="Confirm Password",
            corner_radius=8,
            border_width=0,
            fg_color=("#f0f0f0", "#3a3a3a")
        )
        self.confirm_password_entry.pack(side="left", padx=5, pady=5, fill="x", expand=True)
        f_confirm_pass.pack(pady=10, padx=20, fill="x")

        # Role Selection
        f_role = CTkFrame(self.inner_frame, fg_color="transparent")
        CTkLabel(f_role, text="Role:", width=120, anchor="w", font=("Helvetica", 12)).pack(side="left", padx=5)
        self.role_var = ctk.StringVar(value="student")
        student_rb = CTkRadioButton(f_role, text="Student", variable=self.role_var, value="student", command=self._toggle_linked_student)
        parent_rb = CTkRadioButton(f_role, text="Parent", variable=self.role_var, value="parent", command=self._toggle_linked_student)
        student_rb.pack(side="left", padx=10)
        parent_rb.pack(side="left", padx=10)
        f_role.pack(pady=10, padx=20, fill="x")

        # Linked Student ID
        self.f_linked_student = CTkFrame(self.inner_frame, fg_color="transparent")
        CTkLabel(self.f_linked_student, text="👥", font=("Helvetica", 16)).pack(side="left", padx=(5, 0))
        self.linked_student_label = CTkLabel(self.f_linked_student, text="Linked Student ID:", width=120, anchor="w", font=("Helvetica", 12))
        self.linked_student_label.pack(side="left", padx=5)
        self.linked_student_entry = CTkEntry(
            self.f_linked_student,
            width=250,
            placeholder_text="Enter student username",
            corner_radius=8,
            border_width=0,
            fg_color=("#f0f0f0", "#3a3a3a")
        )
        self.linked_student_entry.pack(side="left", padx=5, pady=5, fill="x", expand=True)

        # Progress Bar (hidden initially)
        self.progress_bar = CTkProgressBar(self.inner_frame, mode="indeterminate", width=200)
        self.progress_bar.pack_forget()

        # Sign Up Button
        self.signup_button = CTkButton(
            self.inner_frame,
            text="Sign Up",
            command=self._perform_signup,
            corner_radius=8,
            font=("Helvetica", 14, "bold"),
            height=40,
            fg_color=("#1f77b4", "#4a90e2"),
            hover_color=("#165a92", "#357abd")
        )
        self.signup_button.pack(pady=15)
        self.signup_button.bind("<Enter>", self._scale_button_in)
        self.signup_button.bind("<Leave>", self._scale_button_out)

        # Login Link
        login_button = CTkButton(
            self.inner_frame,
            text="Already have an account? Login",
            command=self.app._show_login_screen,
            fg_color="transparent",
            text_color=("blue", "lightblue"),
            hover_color=("gray90", "gray30"),
            font=("Helvetica", 12, "underline"),
            corner_radius=0
        )
        login_button.pack(pady=5)

        # Initial state
        self._toggle_linked_student()

        # Bind Enter key
        self.username_entry.bind("<Return>", lambda event: self.password_entry.focus())
        self.password_entry.bind("<Return>", lambda event: self.confirm_password_entry.focus())
        self.confirm_password_entry.bind("<Return>", lambda event: self.role_var.get() == 'parent' and self.linked_student_entry.focus() or self._perform_signup())
        self.linked_student_entry.bind("<Return>", lambda event: self._perform_signup())

    def _animate_title(self, text, index=0):
        """Animates the title by typing it out."""
        if index <= len(text):
            self.title_label.configure(text=text[:index])
            self.after(50, self._animate_title, text, index + 1)

    def _scale_button_in(self, event):
        """Scale button up on hover."""
        self.signup_button.configure(height=42)

    def _scale_button_out(self, event):
        """Scale button back on hover out."""
        self.signup_button.configure(height=40)

    def _toggle_password_visibility(self):
        """Toggles password visibility."""
        if self.show_password_var.get():
            self.password_entry.configure(show="")
        else:
            self.password_entry.configure(show="*")

    def _toggle_linked_student(self):
        """Shows or hides the Linked Student ID field."""
        if self.role_var.get() == "parent":
            self.f_linked_student.pack(pady=10, padx=20, fill="x")
        else:
            self.f_linked_student.pack_forget()

    def _shake_animation(self):
        """Shakes the frame on failed signup."""
        def shake(step=0, direction=1):
            if step < 6:
                offset = 5 * direction
                self.inner_frame.place_configure(relx=0.5, rely=0.5, x=offset, anchor="center")
                self.after(50, shake, step + 1, -direction)
            else:
                self.inner_frame.place_configure(relx=0.5, rely=0.5, x=0, anchor="center")
        shake()

    def _perform_signup(self):
        # Show progress bar
        self.signup_button.pack_forget()
        self.progress_bar.pack(pady=15)
        self.progress_bar.start()

        # Simulate processing
        self.after(1000, self._complete_signup)

    def _complete_signup(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        confirm_password = self.confirm_password_entry.get()
        role = self.role_var.get()
        linked_student = self.linked_student_entry.get() if role == "parent" else None

        # Hide progress bar
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.signup_button.pack(pady=15)

        if password != confirm_password:
            CTkMessagebox(title="Signup Error", message="Passwords do not match.", icon="cancel").get()
            self.password_entry.delete(0, "end")
            self.confirm_password_entry.delete(0, "end")
            self.password_entry.focus()
            
            return

        success, message = self.auth_manager.signup(username, password, role, linked_student)

        if success:
            CTkMessagebox(title="Signup Success", message=message + "\nPlease log in.", icon="check").get()
            self.app._show_login_screen()
        else:
            CTkMessagebox(title="Signup Failed", message=message, icon="cancel").get()

            

    def apply_theme(self, theme):
        pass