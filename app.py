import tkinter as tk
from tkinter import messagebox
import gspread
from google.oauth2.service_account import Credentials

# Google Sheets setup
SHEET_ID = "1_IYoZGi6IqEd1ibOkuNB3cZ4LEwWGc0BegmKfMoZJ6M"  # Replace with your actual Google Sheet ID
SERVICE_ACCOUNT_FILE = "secrets/aswb-practice-exam-91c673a5a3a7.json"  # Replace with the path to your JSON file

def load_questions_from_sheet():
    """Load questions and options from Google Sheet."""
    # Set up Google Sheets API
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).sheet1

    # Fetch all data from the sheet
    data = sheet.get_all_records()
    questions = []
    
    # Parse data into the desired structure
    for row in data:
        question = {
            "question": row["question"],
            "options": [row["response1"], row["response2"], row["response3"], row["response4"]],
            # Here we assume that no answer key is provided in the sheet for simplicity.
        }
        questions.append(question)
    
    return questions

# Load questions from the Google Sheet
questions = load_questions_from_sheet()

# Initialize quiz index and answers storage
current_question = 0
user_answers = [None] * len(questions)

# Setup main window
root = tk.Tk()
root.title("Quiz App")
root.geometry("500x300")

# Variable to store user's selected answer
selected_option = tk.StringVar()

def load_question():
    """Load the current question and options."""
    question = questions[current_question]
    question_label.config(text=question["question"])
    selected_option.set(user_answers[current_question])  # Set previous answer if it exists
    for i, option in enumerate(question["options"]):
        option_buttons[i].config(text=option, value=option)

def next_question():
    """Go to the next question."""
    global current_question
    save_answer()
    if current_question < len(questions) - 1:
        current_question += 1
        load_question()
    update_buttons()

def prev_question():
    """Go to the previous question."""
    global current_question
    save_answer()
    if current_question > 0:
        current_question -= 1
        load_question()
    update_buttons()

def save_answer():
    """Save the user's answer for the current question."""
    user_answers[current_question] = selected_option.get()

def update_buttons():
    """Enable or disable navigation buttons based on the question index."""
    prev_button.config(state=tk.NORMAL if current_question > 0 else tk.DISABLED)
    next_button.config(state=tk.NORMAL if current_question < len(questions) - 1 else tk.DISABLED)

def submit():
    """Show the user's answers and thank them for completing the quiz."""
    save_answer()
    # Display a message to show the user's responses, since no answer key is provided
    messagebox.showinfo("Quiz Completed", "Thank you for completing the quiz!")

# UI Elements
question_label = tk.Label(root, text="", wraplength=400, font=("Arial", 14))
question_label.pack(pady=20)

option_buttons = [
    tk.Radiobutton(root, text="", variable=selected_option, font=("Arial", 12))
    for _ in range(4)
]
for button in option_buttons:
    button.pack(anchor="w")

# Navigation Buttons
prev_button = tk.Button(root, text="Previous", command=prev_question)
prev_button.pack(side=tk.LEFT, padx=20, pady=20)

next_button = tk.Button(root, text="Next", command=next_question)
next_button.pack(side=tk.LEFT, padx=20, pady=20)

submit_button = tk.Button(root, text="Submit", command=submit)
submit_button.pack(side=tk.RIGHT, padx=20, pady=20)

# Initialize the first question
load_question()
update_buttons()

# Start the application
root.mainloop()