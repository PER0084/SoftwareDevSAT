import hashlib
import csv
import os
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime, timedelta, date
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# --- Constants ---
BASE_DIR = "data"
USERS_FILE = os.path.join(BASE_DIR, "users.csv")
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M"
TIME_FORMAT_DISPLAY = "%H:%M, %d/%m/%Y" # For the clock

# --- File/Directory Handling ---
def ensure_dir_exists(dir_path):
    """Ensures a directory exists, creates it if not."""
    os.makedirs(dir_path, exist_ok=True)

def get_student_dir(username):
    """Returns the path to the student's data directory."""
    path = os.path.join(BASE_DIR, username)
    ensure_dir_exists(path)
    return path

def get_notes_dir(username):
    """Returns the path to the student's notes directory."""
    path = os.path.join(get_student_dir(username), "notes")
    ensure_dir_exists(path)
    return path

def get_student_data_path(username, filename):
    """Returns the full path for a student's specific data file."""
    return os.path.join(get_student_dir(username), filename)

# --- CSV Handling ---
def read_csv(file_path, expected_headers=None):
    """Reads a CSV file and returns a list of dictionaries."""
    data = []
    if not os.path.exists(file_path):
        if expected_headers:
             # Create file with headers if it doesn't exist
            try:
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(expected_headers)
                return [] # Return empty list as the file was just created
            except IOError as e:
                messagebox.showerror("File Error", f"Could not create file {file_path}: {e}")
                return [] # Return empty on error
        else:
            return [] # File doesn't exist and no headers specified

    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            # Check headers if provided
            if expected_headers and reader.fieldnames != expected_headers:
                 # Handle potentially corrupted file or incorrect format
                 # Option 1: Show error and return empty
                 print(f"Warning: Header mismatch in {file_path}. Expected {expected_headers}, got {reader.fieldnames}. Attempting to read anyway.")
                 # Option 2: Try reading anyway (might fail later)
                 # Option 3: Offer to recreate/fix (more complex)
                 # For now, let's try reading anyway, but log the warning.
                 # If critical, raise an error or return []
                 # messagebox.showerror("File Error", f"Incorrect headers in {file_path}. Expected {expected_headers}.")
                 # return []

            # Reset reader if headers were checked
            f.seek(0) # Go back to the start
            reader = csv.DictReader(f) # Recreate reader
            data = list(reader)
    except FileNotFoundError:
        pass # Handled above by initial check
    except Exception as e:
        messagebox.showerror("Read Error", f"Error reading {file_path}: {e}")
    return data

def write_csv(file_path, data, headers):
    """Writes a list of dictionaries to a CSV file."""
    try:
        ensure_dir_exists(os.path.dirname(file_path)) # Ensure directory exists
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)
    except IOError as e:
        messagebox.showerror("Write Error", f"Error writing to {file_path}: {e}")
    except Exception as e:
         messagebox.showerror("Write Error", f"An unexpected error occurred writing to {file_path}: {e}")


# --- Text File Handling ---
def read_txt(file_path):
    """Reads content from a text file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "" # Return empty string if file doesn't exist
    except Exception as e:
        messagebox.showerror("Read Error", f"Error reading {file_path}: {e}")
        return ""

def write_txt(file_path, content):
    """Writes content to a text file."""
    try:
        ensure_dir_exists(os.path.dirname(file_path))
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    except IOError as e:
        messagebox.showerror("Write Error", f"Error writing to {file_path}: {e}")

def delete_file(file_path):
    """Deletes a file if it exists."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except OSError as e:
        messagebox.showerror("Delete Error", f"Error deleting file {file_path}: {e}")


# --- Security ---
def hash_password(password):
    """Hashes a password using SHA-256."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def verify_password(stored_hash, provided_password):
    """Verifies a provided password against a stored hash."""
    return stored_hash == hash_password(provided_password)

# --- Date/Time Handling ---
def get_current_datetime_str(fmt=DATETIME_FORMAT):
    """Gets the current date and time as a formatted string."""
    return datetime.now().strftime(fmt)

def get_current_date_str(fmt=DATE_FORMAT):
    """Gets the current date as a formatted string."""
    return date.today().strftime(fmt)

def parse_datetime_str(datetime_str, fmt=DATETIME_FORMAT):
    """Parses a datetime string into a datetime object."""
    try:
        return datetime.strptime(datetime_str, fmt)
    except (ValueError, TypeError):
        return None

def parse_date_str(date_str, fmt=DATE_FORMAT):
    """Parses a date string into a date object."""
    try:
        return datetime.strptime(date_str, fmt).date()
    except (ValueError, TypeError):
        return None

def add_days_to_date(base_date_str, days_to_add, fmt=DATE_FORMAT):
    """Adds days to a date string and returns a new date string."""
    base_date = parse_date_str(base_date_str, fmt)
    if base_date and isinstance(days_to_add, (int, float)):
        new_date = base_date + timedelta(days=int(days_to_add))
        return new_date.strftime(fmt)
    return base_date_str # Return original if parsing failed or days invalid

# --- Validation ---
def validate_not_empty(value, field_name):
    """Checks if a value is not empty."""
    if not value or not value.strip():
        messagebox.showwarning("Input Error", f"{field_name} cannot be empty.")
        return False
    return True

def validate_date_format(date_str, field_name):
    """Checks if a string is in YYYY-MM-DD format."""
    if parse_date_str(date_str) is None:
         messagebox.showwarning("Input Error", f"{field_name} must be in YYYY-MM-DD format.")
         return False
    return True

def validate_time_range(time_str, field_name):
     """Checks if a string is in YYYY-MM-DD HH:MM-HH:MM format."""
     parts = time_str.split(' ')
     if len(parts) != 2:
         messagebox.showwarning("Input Error", f"{field_name} format incorrect. Use 'YYYY-MM-DD HH:MM-HH:MM'.")
         return False

     date_part = parts[0]
     time_parts = parts[1].split('-')

     if not validate_date_format(date_part, field_name):
         return False

     if len(time_parts) != 2:
         messagebox.showwarning("Input Error", f"{field_name} time range format incorrect. Use 'HH:MM-HH:MM'.")
         return False

     try:
         start_time = datetime.strptime(time_parts[0], "%H:%M").time()
         end_time = datetime.strptime(time_parts[1], "%H:%M").time()
         if end_time <= start_time:
             messagebox.showwarning("Input Error", f"{field_name}: End time must be after start time.")
             return False
     except ValueError:
         messagebox.showwarning("Input Error", f"{field_name} time format incorrect. Use 'HH:MM'.")
         return False

     return True


# --- UI Helpers ---
def clear_treeview(tree):
    """Removes all items from a ttk.Treeview."""
    for item in tree.get_children():
        tree.delete(item)

def setup_style(theme="light"):
    """Configures ttk styles for light/dark mode."""
    style = ttk.Style()
    if theme == "dark":
        # Define dark theme colors
        bg_color = "#333333"
        fg_color = "#ffffff"
        entry_bg = "#555555"
        entry_fg = "#ffffff"
        accent_color = "#4a90e2" # A slightly brighter blue for dark mode
        tree_bg = "#444444"
        tree_fg = "#ffffff"
        tree_heading_bg = "#555555"

        style.theme_use('clam') # 'clam' often works better for coloring

        style.configure(".", background=bg_color, foreground=fg_color)
        style.configure("TFrame", background=bg_color)
        style.configure("TLabel", background=bg_color, foreground=fg_color)
        style.configure("TButton", background=accent_color, foreground=fg_color, borderwidth=1)
        style.map("TButton", background=[('active', '#6aa0f0')]) # Lighter blue on hover/press
        style.configure("TEntry", fieldbackground=entry_bg, foreground=entry_fg, insertcolor=fg_color)
        style.configure("TCombobox", fieldbackground=entry_bg, foreground=entry_fg)
        style.map('TCombobox', fieldbackground=[('readonly', entry_bg)])
        # Explicitly configure Listbox background/foreground (not ttk)
        # This needs to be applied directly to the widget instance

        # Treeview styling
        style.configure("Treeview", background=tree_bg, foreground=tree_fg, fieldbackground=tree_bg)
        style.configure("Treeview.Heading", background=tree_heading_bg, foreground=fg_color, font=('Helvetica', 10, 'bold'))
        style.map("Treeview.Heading", background=[('active', '#666666')])
        # Highlight color for selected item
        style.map('Treeview', background=[('selected', accent_color)], foreground=[('selected', fg_color)])

    else: # Light theme (Default-like with blue accents)
        bg_color = "#ffffff"
        fg_color = "#000000"
        entry_bg = "#ffffff"
        entry_fg = "#000000"
        accent_color = "#0000ff" # Blue
        tree_bg = "#ffffff"
        tree_fg = "#000000"
        tree_heading_bg = "#eeeeee"

        # Use a default theme that allows modifications
        try:
             style.theme_use('vista') # Try 'vista' on Windows, 'aqua' on Mac, 'clam' or 'alt' on Linux
        except tk.TclError:
             style.theme_use('clam') # Fallback theme

        style.configure(".", background=bg_color, foreground=fg_color)
        style.configure("TFrame", background=bg_color)
        style.configure("TLabel", background=bg_color, foreground=fg_color)
        style.configure("TButton", background=accent_color, foreground=bg_color, borderwidth=1)
        style.map("TButton", background=[('active', '#4444ff')]) # Slightly lighter blue on hover/press
        style.configure("TEntry", fieldbackground=entry_bg, foreground=entry_fg, insertcolor=fg_color)
        style.configure("TCombobox", fieldbackground=entry_bg, foreground=entry_fg)
        style.map('TCombobox', fieldbackground=[('readonly', entry_bg)])

        # Treeview styling
        style.configure("Treeview", background=tree_bg, foreground=tree_fg, fieldbackground=tree_bg)
        style.configure("Treeview.Heading", background=tree_heading_bg, foreground=fg_color, font=('Helvetica', 10, 'bold'))
        style.map("Treeview.Heading", background=[('active', '#dddddd')])
        # Highlight color for selected item
        style.map('Treeview', background=[('selected', accent_color)], foreground=[('selected', bg_color)])

# --- Matplotlib Embedding ---
def create_matplotlib_chart(parent_frame, data_dict, title, xlabel, ylabel):
    """Creates and embeds a matplotlib bar chart in a Tkinter frame."""
    # Clear previous widgets in the frame
    for widget in parent_frame.winfo_children():
        widget.destroy()

    if not data_dict:
        ttk.Label(parent_frame, text="No data to display.").pack(pady=20)
        return None # Return None if no chart was created

    fig = plt.Figure(figsize=(6, 4), dpi=100) # Adjust size as needed
    ax = fig.add_subplot(111)

    subjects = list(data_dict.keys())
    values = list(data_dict.values())

    bars = ax.bar(subjects, values, color='#0000ff') # Use blue accent

    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis='x', rotation=45, labelsize=8) # Rotate labels if needed
    fig.tight_layout() # Adjust layout

    # Determine colors based on current theme (difficult to access style directly here)
    # For simplicity, using fixed colors for the chart itself, background can be set on figure
    # fig.patch.set_facecolor(parent_frame.cget('background')) # Try to match frame background
    # ax.set_facecolor(parent_frame.cget('background'))

    canvas = FigureCanvasTkAgg(fig, master=parent_frame)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(fill=tk.BOTH, expand=True)
    canvas.draw()

    return canvas # Return canvas object if needed