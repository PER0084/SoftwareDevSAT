import customtkinter as ctk
from customtkinter import CTkFrame, CTkLabel, CTkEntry, CTkButton, CTkScrollableFrame, CTkToplevel, CTkProgressBar
from utils import (get_student_data_path, read_csv, write_csv,
                   get_current_date_str, add_days_to_date, parse_date_str,
                   DATE_FORMAT, validate_not_empty)
import os
import random
from datetime import date, datetime, timedelta
import time
from CTkMessagebox import CTkMessagebox

FLASHCARDS_FILE = "flashcards.csv"
FLASHCARDS_HEADERS = ['id', 'question', 'answer', 'topic', 'interval', 'next_review_date', 'ease_factor', 'student_id']

# SM2 Algorithm Constants
INITIAL_EASE = 2.5
MIN_EASE = 1.3
EASY_BONUS = 1.2

# Study Tips for Flashcards
STUDY_TIPS = [
    "Break your study sessions into 25-minute chunks with 5-minute breaks (Pomodoro Technique)!",
    "Review flashcards daily to reinforce memory retention.",
    "Use active recall: try to answer the question before flipping the card.",
    "Group flashcards by topic to make connections between concepts.",
    "Reward yourself after completing a quiz session to stay motivated!"
]

class FlashcardsTab(CTkFrame):
    """GUI Frame for managing and reviewing flashcards."""
    def __init__(self, parent, username, progress_logger):
        super().__init__(parent, corner_radius=15, fg_color=("#e6f0ff", "#1a2a44"))
        self.username = username
        self.progress_logger = progress_logger
        self.flashcards_file_path = get_student_data_path(self.username, FLASHCARDS_FILE)
        self.flashcards_data = []
        self.next_id = 1
        self.current_edit_id = None
        self.selected_row = None
        self.selected_id = None
        self.row_frames = []

        # Inner frame for shadow effect
        self.inner_frame = CTkFrame(self, corner_radius=15, fg_color=("#ffffff", "#2b2b2b"), border_width=2, border_color=("#1f77b4", "#4a90e2"))
        self.inner_frame.pack(padx=5, pady=5, fill="both", expand=True)

        # --- Main Layout Frames ---
        manage_frame = CTkFrame(self.inner_frame, corner_radius=10, fg_color=("#f5f5f5", "#333333"))
        manage_frame.pack(pady=10, padx=10, fill="x")

        quiz_frame = CTkFrame(self.inner_frame, corner_radius=10, fg_color=("#f5f5f5", "#333333"))
        quiz_frame.pack(pady=10, padx=10, fill="x")

        display_frame = CTkFrame(self.inner_frame, corner_radius=10, fg_color=("#f5f5f5", "#333333"))
        display_frame.pack(pady=10, padx=10, fill="both", expand=True)

        # --- Manage Flashcards UI ---
        # Animated Title
        self.manage_title_label = CTkLabel(manage_frame, text="", font=("Comic Sans MS", 18, "bold"))
        self.manage_title_label.pack(pady=5)
        self._animate_title(self.manage_title_label, "Manage Flashcards")

        # Study Tip
        tip = random.choice(STUDY_TIPS)
        CTkLabel(manage_frame, text=f"💡 Tip: {tip}", font=("Helvetica", 12, "italic"), wraplength=600).pack(pady=5)

        # Question
        f_question = CTkFrame(manage_frame, fg_color="transparent")
        CTkLabel(f_question, text="❓", font=("Helvetica", 16)).pack(side="left", padx=(5, 0))
        self.question_entry = CTkEntry(
            f_question,
            width=400,
            placeholder_text="Enter the question",
            corner_radius=8,
            border_width=0,
            fg_color=("#e0e0e0", "#444444")
        )
        self.question_entry.pack(side="left", padx=5, pady=5, fill="x", expand=True)
        f_question.pack(pady=10, padx=20, fill="x")

        # Answer
        f_answer = CTkFrame(manage_frame, fg_color="transparent")
        CTkLabel(f_answer, text="📝", font=("Helvetica", 16)).pack(side="left", padx=(5, 0))
        self.answer_entry = CTkEntry(
            f_answer,
            width=400,
            placeholder_text="Enter the answer",
            corner_radius=8,
            border_width=0,
            fg_color=("#e0e0e0", "#444444")
        )
        self.answer_entry.pack(side="left", padx=5, pady=5, fill="x", expand=True)
        f_answer.pack(pady=10, padx=20, fill="x")

        # Topic
        f_topic = CTkFrame(manage_frame, fg_color="transparent")
        CTkLabel(f_topic, text="📚", font=("Helvetica", 16)).pack(side="left", padx=(5, 0))
        self.topic_entry = CTkEntry(
            f_topic,
            width=200,
            placeholder_text="Enter the topic",
            corner_radius=8,
            border_width=0,
            fg_color=("#e0e0e0", "#444444")
        )
        self.topic_entry.pack(side="left", padx=5, pady=5, fill="x", expand=True)
        f_topic.pack(pady=10, padx=20, fill="x")

        # Buttons Frame
        buttons_frame = CTkFrame(manage_frame, fg_color="transparent")
        self.add_update_button = CTkButton(
            buttons_frame,
            text="Add Card",
            command=self._add_or_update_flashcard,
            corner_radius=8,
            font=("Helvetica", 12, "bold"),
            fg_color=("#1f77b4", "#4a90e2"),
            hover_color=("#165a92", "#357abd")
        )
        self.add_update_button.pack(side="left", padx=5)
        self.add_update_button.bind("<Enter>", lambda event: self._scale_button_in(self.add_update_button))
        self.add_update_button.bind("<Leave>", lambda event: self._scale_button_out(self.add_update_button))

        self.clear_button = CTkButton(
            buttons_frame,
            text="Clear Fields",
            command=self._clear_fields,
            corner_radius=8,
            font=("Helvetica", 12, "bold"),
            fg_color=("#ff9500", "#cc7700"),
            hover_color=("#e68a00", "#b36b00")
        )
        self.clear_button.pack(side="left", padx=5)
        self.clear_button.bind("<Enter>", lambda event: self._scale_button_in(self.clear_button))
        self.clear_button.bind("<Leave>", lambda event: self._scale_button_out(self.clear_button))

        self.delete_button = CTkButton(
            buttons_frame,
            text="Delete Selected",
            command=self._delete_flashcard,
            corner_radius=8,
            font=("Helvetica", 12, "bold"),
            fg_color=("#ff3b30", "#cc2f27"),
            hover_color=("#e6352b", "#b32923")
        )
        self.delete_button.pack(side="left", padx=5)
        self.delete_button.bind("<Enter>", lambda event: self._scale_button_in(self.delete_button))
        self.delete_button.bind("<Leave>", lambda event: self._scale_button_out(self.delete_button))
        buttons_frame.pack(pady=10)

        # --- Quiz UI ---
        self.quiz_title_label = CTkLabel(quiz_frame, text="", font=("Comic Sans MS", 18, "bold"))
        self.quiz_title_label.pack(pady=5)
        self._animate_title(self.quiz_title_label, "Review Flashcards")

        f_quiz = CTkFrame(quiz_frame, fg_color="transparent")
        CTkLabel(f_quiz, text="📖 Filter by Topic:", width=150, anchor="w", font=("Helvetica", 12)).pack(side="left", padx=5)
        self.quiz_topic_filter_entry = CTkEntry(
            f_quiz,
            width=200,
            placeholder_text="Enter topic to filter",
            corner_radius=8,
            border_width=0,
            fg_color=("#e0e0e0", "#444444")
        )
        self.quiz_topic_filter_entry.pack(side="left", padx=5)
        self.start_quiz_button = CTkButton(
            f_quiz,
            text="Start Quiz ▶",
            command=self._start_quiz,
            corner_radius=8,
            font=("Helvetica", 12, "bold"),
            fg_color=("#1f77b4", "#4a90e2"),
            hover_color=("#165a92", "#357abd")
        )
        self.start_quiz_button.pack(side="left", padx=10)
        self.start_quiz_button.bind("<Enter>", lambda event: self._scale_button_in(self.start_quiz_button))
        self.start_quiz_button.bind("<Leave>", lambda event: self._scale_button_out(self.start_quiz_button))
        f_quiz.pack(pady=10, padx=20, fill="x")

        # --- Flashcard Display ---
        self.display_scroll = CTkScrollableFrame(display_frame, corner_radius=10)
        self.display_scroll.pack(fill="both", expand=True)

        # Add headers
        self.header_frame = CTkFrame(self.display_scroll, fg_color=("#d3d3d3", "#555555"))
        headers = ["ID", "Topic", "Question", "Answer", "Next Review", "Interval (d)", "Ease Factor"]
        self.header_widths = [40, 100, 250, 250, 100, 80, 80]
        for header, width in zip(headers, self.header_widths):
            CTkLabel(self.header_frame, text=header, width=width, anchor="w", font=("Helvetica", 10, "bold")).pack(side="left", padx=2)
        self.header_frame.pack(fill="x")

        # Load initial data
        self._load_flashcards()

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

    def _get_max_id(self):
        if not self.flashcards_data:
            return 0
        max_id = 0
        for card in self.flashcards_data:
            try:
                card_id = int(card.get('id', 0))
                if card_id > max_id:
                    max_id = card_id
            except (ValueError, TypeError):
                continue
        return max_id

    def _load_flashcards(self):
        self.flashcards_data = read_csv(self.flashcards_file_path, FLASHCARDS_HEADERS)
        today_str = get_current_date_str()
        for card in self.flashcards_data:
            try:
                card['id'] = int(card.get('id', 0))
                card['interval'] = float(card.get('interval', 0))
                card['ease_factor'] = float(card.get('ease_factor', INITIAL_EASE))
                if not parse_date_str(card.get('next_review_date')):
                    card['next_review_date'] = today_str
            except (ValueError, TypeError) as e:
                print(f"Warning: Error parsing card data: {card}. Error: {e}. Using defaults.")
                card['id'] = card.get('id', 0) if isinstance(card.get('id'), int) else 0
                card['interval'] = card.get('interval', 0) if isinstance(card.get('interval'), (int, float)) else 0
                card['ease_factor'] = card.get('ease_factor', INITIAL_EASE) if isinstance(card.get('ease_factor'), (int, float)) else INITIAL_EASE
                card['next_review_date'] = card.get('next_review_date') if parse_date_str(card.get('next_review_date')) else today_str

        self.next_id = self._get_max_id() + 1
        self._populate_treeview()

    def _save_flashcards(self):
        data_to_save = []
        for card in self.flashcards_data:
            save_card = card.copy()
            save_card['id'] = str(save_card.get('id', ''))
            save_card['interval'] = str(save_card.get('interval', '0'))
            save_card['ease_factor'] = str(round(save_card.get('ease_factor', INITIAL_EASE), 3))
            save_card['next_review_date'] = str(save_card.get('next_review_date', ''))
            data_to_save.append(save_card)

        write_csv(self.flashcards_file_path, data_to_save, FLASHCARDS_HEADERS)

    def _populate_treeview(self):
        for row_frame in self.row_frames:
            row_frame.destroy()
        self.row_frames = []
        self.selected_row = None
        self.selected_id = None

        self.flashcards_data.sort(key=lambda x: (x.get('topic', '').lower(), x.get('question', '').lower()))

        for idx, card in enumerate(self.flashcards_data):
            ease_display = f"{card.get('ease_factor', INITIAL_EASE):.2f}"
            values = (
                card.get('id', ''),
                card.get('topic', ''),
                card.get('question', ''),
                card.get('answer', ''),
                card.get('next_review_date', ''),
                card.get('interval', ''),
                ease_display
            )

            row_frame = CTkFrame(self.display_scroll, fg_color=("gray90", "gray20") if idx % 2 == 0 else ("gray80", "gray30"))
            row_frame.pack(fill="x", pady=2)

            for value, width in zip(values, self.header_widths):
                label = CTkLabel(row_frame, text=str(value), width=width, anchor="w")
                label.pack(side="left", padx=2)

            row_frame.bind("<Button-1>", lambda event, card_id=card['id']: self._select_row(row_frame, card_id))
            for child in row_frame.winfo_children():
                child.bind("<Button-1>", lambda event, card_id=card['id']: self._select_row(row_frame, card_id))

            row_frame.bind("<Double-1>", lambda event, card_id=card['id']: self._load_selected_for_edit(card_id))
            for child in row_frame.winfo_children():
                child.bind("<Double-1>", lambda event, card_id=card['id']: self._load_selected_for_edit(card_id))

            row_frame.bind("<Enter>", lambda event, rf=row_frame: rf.configure(fg_color=("gray75", "gray25")))
            row_frame.bind("<Leave>", lambda event, rf=row_frame, idx=idx: rf.configure(fg_color=("gray90", "gray20") if idx % 2 == 0 else ("gray80", "gray30")))
            self.row_frames.append(row_frame)

    def _select_row(self, row_frame, card_id):
        if self.selected_row:
            idx = self.row_frames.index(self.selected_row)
            self.selected_row.configure(fg_color=("gray90", "gray20") if idx % 2 == 0 else ("gray80", "gray30"))
            for child in self.selected_row.winfo_children():
                child.configure(fg_color=("gray90", "gray20") if idx % 2 == 0 else ("gray80", "gray30"))

        self.selected_row = row_frame
        self.selected_id = card_id
        self.selected_row.configure(fg_color=("gray75", "gray25"))
        for child in self.selected_row.winfo_children():
            child.configure(fg_color=("gray75", "gray25"))

    def _clear_fields(self):
        self.question_entry.delete(0, "end")
        self.answer_entry.delete(0, "end")
        self.topic_entry.delete(0, "end")
        self.current_edit_id = None
        self.add_update_button.configure(text="Add Card")
        if self.selected_row:
            idx = self.row_frames.index(self.selected_row)
            self.selected_row.configure(fg_color=("gray90", "gray20") if idx % 2 == 0 else ("gray80", "gray30"))
            for child in self.selected_row.winfo_children():
                child.configure(fg_color=("gray90", "gray20") if idx % 2 == 0 else ("gray80", "gray30"))
        self.selected_row = None
        self.selected_id = None

    def _load_selected_for_edit(self, card_id=None):
        if card_id is None:
            return

        item_id = int(card_id)
        card_to_edit = None
        for card in self.flashcards_data:
            if card.get('id') == item_id:
                card_to_edit = card
                break

        if card_to_edit:
            self.current_edit_id = item_id
            self.question_entry.delete(0, "end")
            self.question_entry.insert(0, card_to_edit.get('question', ''))
            self.answer_entry.delete(0, "end")
            self.answer_entry.insert(0, card_to_edit.get('answer', ''))
            self.topic_entry.delete(0, "end")
            self.topic_entry.insert(0, card_to_edit.get('topic', ''))
            self.add_update_button.configure(text="Update Card")

    def _add_or_update_flashcard(self):
        question = self.question_entry.get()
        answer = self.answer_entry.get()
        topic = self.topic_entry.get()

        if not validate_not_empty(question, "Question"):
            self._shake_animation()
            return
        if not validate_not_empty(answer, "Answer"):
            self._shake_animation()
            return
        if not validate_not_empty(topic, "Topic"):
            self._shake_animation()
            return

        if self.current_edit_id is not None:
            updated = False
            for i, card in enumerate(self.flashcards_data):
                if card.get('id') == self.current_edit_id:
                    self.flashcards_data[i]['question'] = question
                    self.flashcards_data[i]['answer'] = answer
                    self.flashcards_data[i]['topic'] = topic
                    updated = True
                    break
            if updated:
                CTkMessagebox(title="Update Success", message="Flashcard updated successfully.", icon="check").get()
            else:
                CTkMessagebox(title="Update Error", message="Could not find the card to update.", icon="cancel").get()
                self._clear_fields()
                return
        else:
            new_card = {
                'id': self.next_id,
                'question': question,
                'answer': answer,
                'topic': topic,
                'interval': 0,
                'next_review_date': get_current_date_str(),
                'ease_factor': INITIAL_EASE,
                'student_id': self.username
            }
            self.flashcards_data.append(new_card)
            self.next_id += 1
            CTkMessagebox(title="Add Success", message="Flashcard added successfully.", icon="check").get()

        self._save_flashcards()
        self._populate_treeview()
        self._clear_fields()

    def _delete_flashcard(self):
        if not self.selected_id:
            CTkMessagebox(title="Selection Error", message="Please select a flashcard to delete.", icon="warning").get()
            self._shake_animation()
            return

        item_id_to_delete = self.selected_id

        if CTkMessagebox(title="Confirm Delete", message="Are you sure you want to delete this flashcard?", option_1="Yes", option_2="No").get() == "Yes":
            initial_length = len(self.flashcards_data)
            self.flashcards_data = [card for card in self.flashcards_data if card.get('id') != item_id_to_delete]

            if len(self.flashcards_data) < initial_length:
                self._save_flashcards()
                self._populate_treeview()
                self._clear_fields()
                CTkMessagebox(title="Delete Success", message="Flashcard deleted.", icon="check").get()
            else:
                CTkMessagebox(title="Delete Error", message="Could not find the selected card to delete.", icon="cancel").get()
                self._shake_animation()

    def _start_quiz(self):
        today = date.today()
        topic_filter = self.quiz_topic_filter_entry.get().strip().lower()

        cards_to_review = []
        for card in self.flashcards_data:
            review_date = parse_date_str(card.get('next_review_date'))
            if review_date and review_date <= today:
                if not topic_filter or (topic_filter and card.get('topic', '').lower() == topic_filter):
                    cards_to_review.append(card.copy())

        if not cards_to_review:
            CTkMessagebox(title="Quiz", message="No flashcards due for review today" + (f" with topic '{topic_filter}'." if topic_filter else "."), icon="info").get()
            self._shake_animation()
            return

        random.shuffle(cards_to_review)
        quiz_window = QuizWindow(self, cards_to_review, self.username, self._quiz_finished_callback)

    def _quiz_finished_callback(self, updated_cards, cards_reviewed_count, duration_seconds, subject_times):
        if not updated_cards:
            print("Quiz cancelled or no cards reviewed.")
            return

        updated_ids = {card['id'] for card in updated_cards}
        new_flashcards_data = []
        for original_card in self.flashcards_data:
            if original_card['id'] in updated_ids:
                updated_version = next((uc for uc in updated_cards if uc['id'] == original_card['id']), None)
                if updated_version:
                    new_flashcards_data.append(updated_version)
            else:
                new_flashcards_data.append(original_card)

        self.flashcards_data = new_flashcards_data
        self._save_flashcards()
        self._populate_treeview()

        if cards_reviewed_count > 0 and duration_seconds > 0:
            study_hours = duration_seconds / 3600.0
            self.progress_logger(
                username=self.username,
                subject="Flashcard Review",
                hours=study_hours,
                cards=cards_reviewed_count,
                log_date=get_current_date_str()
            )
            CTkMessagebox(title="Quiz Finished", message=f"Reviewed {cards_reviewed_count} cards in {duration_seconds:.1f} seconds.", icon="check").get()
        else:
            CTkMessagebox(title="Quiz Finished", message="Quiz completed.", icon="check").get()

    def apply_theme(self, theme):
        if theme == "light":
            self.header_frame.configure(fg_color="#d3d3d3")
        else:
            self.header_frame.configure(fg_color="#555555")

class QuizWindow(ctk.CTkToplevel):
    """Modal window for the flashcard quiz process."""
    def __init__(self, parent, cards_to_review, username, callback):
        super().__init__(parent)
        self.transient(parent)
        self.grab_set()
        self.title("Flashcard Quiz")
        self.geometry("500x400")
        self.configure(fg_color=("#e6f0ff", "#1a2a44"))

        self.cards = cards_to_review
        self.username = username
        self.callback = callback
        self.current_card_index = 0
        self.updated_cards_data = []
        self.start_time = time.time()
        self.cards_reviewed_count = 0
        self.subject_times = {}
        self.current_card_start_time = time.time()

        # Inner frame for card effect
        self.inner_frame = CTkFrame(self, corner_radius=15, fg_color=("#ffffff", "#2b2b2b"), border_width=2, border_color=("#1f77b4", "#4a90e2"))
        self.inner_frame.pack(padx=10, pady=10, fill="both", expand=True)

        # Progress Indicator
        self.progress_label = CTkLabel(self.inner_frame, text=f"Card 1/{len(self.cards)}", font=("Helvetica", 12))
        self.progress_label.pack(pady=5)

        # Card Frame for Flip Animation
        self.card_frame = CTkFrame(self.inner_frame, corner_radius=10, fg_color=("#f5f5f5", "#333333"))
        self.card_frame.pack(pady=20, padx=20, fill="both", expand=True)

        self.question_label = CTkLabel(self.card_frame, text="Question:", font=("Helvetica", 14, "bold"), wraplength=440, anchor="center")
        self.question_label.pack(pady=20, padx=10)

        self.answer_label = CTkLabel(self.card_frame, text="", font=("Helvetica", 12), wraplength=440, anchor="center")
        # Don't pack answer label yet

        self.show_answer_button = CTkButton(
            self.inner_frame,
            text="Show Answer 🔄",
            command=self._show_answer,
            corner_radius=8,
            font=("Helvetica", 12, "bold"),
            fg_color=("#1f77b4", "#4a90e2"),
            hover_color=("#165a92", "#357abd")
        )
        self.show_answer_button.pack(pady=10)
        self.show_answer_button.bind("<Enter>", lambda event: self._scale_button_in(self.show_answer_button))
        self.show_answer_button.bind("<Leave>", lambda event: self._scale_button_out(self.show_answer_button))

        # Assessment Buttons
        self.assessment_frame = CTkFrame(self.inner_frame, fg_color="transparent")
        self.again_button = CTkButton(
            self.assessment_frame,
            text="Again (0d)",
            command=lambda: self._assess(0),
            corner_radius=8,
            font=("Helvetica", 12, "bold"),
            fg_color=("#ff3b30", "#cc2f27"),
            hover_color=("#e6352b", "#b32923")
        )
        self.again_button.pack(side="left", padx=10, pady=10)
        self.again_button.bind("<Enter>", lambda event: self._scale_button_in(self.again_button))
        self.again_button.bind("<Leave>", lambda event: self._scale_button_out(self.again_button))

        self.good_button = CTkButton(
            self.assessment_frame,
            text="Good (1+d)",
            command=lambda: self._assess(1),
            corner_radius=8,
            font=("Helvetica", 12, "bold"),
            fg_color=("#ff9500", "#cc7700"),
            hover_color=("#e68a00", "#b36b00")
        )
        self.good_button.pack(side="left", padx=10, pady=10)
        self.good_button.bind("<Enter>", lambda event: self._scale_button_in(self.good_button))
        self.good_button.bind("<Leave>", lambda event: self._scale_button_out(self.good_button))

        self.easy_button = CTkButton(
            self.assessment_frame,
            text="Easy (4+d)",
            command=lambda: self._assess(2),
            corner_radius=8,
            font=("Helvetica", 12, "bold"),
            fg_color=("#34c759", "#2ba844"),
            hover_color=("#2eb350", "#25933b")
        )
        self.easy_button.pack(side="left", padx=10, pady=10)
        self.easy_button.bind("<Enter>", lambda event: self._scale_button_in(self.easy_button))
        self.easy_button.bind("<Leave>", lambda event: self._scale_button_out(self.easy_button))

        # Load first card
        if self.cards:
            self._load_card()
        else:
            self.destroy()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _scale_button_in(self, button):
        button.configure(height=32)

    def _scale_button_out(self, button):
        button.configure(height=30)

    def _flip_animation(self, callback):
        """Simulates a flip animation by scaling the card frame."""
        def flip(step=0):
            if step < 10:
                scale = 1.0 - (0.1 * abs(5 - step))
                self.card_frame.configure(width=440 * scale)
                self.after(30, flip, step + 1)
            else:
                self.card_frame.configure(width=440)
                callback()
        flip()

    def _load_card(self):
        if self.current_card_index < len(self.cards):
            card = self.cards[self.current_card_index]
            self.question_label.configure(text=f"Q: {card.get('question', '')}")
            self.progress_label.configure(text=f"Card {self.current_card_index + 1}/{len(self.cards)}")

            self.answer_label.pack_forget()
            self.answer_label.configure(text="")
            self.assessment_frame.pack_forget()
            self.show_answer_button.pack(pady=10)

            self.current_card_start_time = time.time()
        else:
            self._finish_quiz()

    def _show_answer(self):
        if self.current_card_index < len(self.cards):
            card = self.cards[self.current_card_index]
            self.answer_label.configure(text=f"A: {card.get('answer', '')}")
            self._flip_animation(lambda: (
                self.show_answer_button.pack_forget(),
                self.answer_label.pack(pady=10, padx=10),
                self.assessment_frame.pack(pady=10)
            ))

    def _assess(self, rating):
        if self.current_card_index >= len(self.cards):
            return

        card = self.cards[self.current_card_index]
        today = date.today()

        try:
            interval = float(card.get('interval', 0))
            ease_factor = float(card.get('ease_factor', INITIAL_EASE))
        except (ValueError, TypeError):
            interval = 0.0
            ease_factor = INITIAL_EASE

        if rating == 0:
            interval = 0
            ease_factor = max(MIN_EASE, ease_factor - 0.2)
        else:
            if interval == 0:
                if rating == 1:
                    interval = 1
                    ease_factor += 0.05
                elif rating == 2:
                    interval = 4
                    ease_factor += 0.1
            else:
                if rating == 1:
                    interval = interval * ease_factor
                    ease_factor += 0.05
                elif rating == 2:
                    interval = interval * ease_factor * EASY_BONUS
                    ease_factor += 0.1
            ease_factor = max(MIN_EASE, ease_factor)

        interval_days = max(1, round(interval)) if rating > 0 else 0
        next_review_date_obj = today + timedelta(days=interval_days)
        next_review_date_str = next_review_date_obj.strftime(DATE_FORMAT)

        card['interval'] = round(interval, 2)
        card['ease_factor'] = round(ease_factor, 3)
        card['next_review_date'] = next_review_date_str

        self.updated_cards_data.append(card.copy())
        self.cards_reviewed_count += 1

        time_spent_on_card = time.time() - self.current_card_start_time
        subject = card.get('topic', 'Unknown')
        self.subject_times[subject] = self.subject_times.get(subject, 0) + time_spent_on_card

        self.current_card_index += 1
        self._load_card()

    def _finish_quiz(self):
        duration = time.time() - self.start_time
        self.callback(self.updated_cards_data, self.cards_reviewed_count, duration, self.subject_times)
        self.destroy()

    def _on_close(self):
        if CTkMessagebox(title="Exit Quiz", message="Are you sure you want to exit the quiz? Progress on the current card will be lost, but previous reviews in this session will be saved.", option_1="Yes", option_2="No").get() == "Yes":
            duration = time.time() - self.start_time
            self.callback(self.updated_cards_data, self.cards_reviewed_count, duration, self.subject_times)
            self.destroy()