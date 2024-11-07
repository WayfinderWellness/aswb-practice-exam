import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# Load Google Sheets credentials from Streamlit secrets
service_account_info = st.secrets["google_service_account"]
creds = Credentials.from_service_account_info(service_account_info)
client = gspread.authorize(creds)

# Specify your Google Sheets ID and open the sheet
SHEET_ID = "1_IYoZGi6IqEd1ibOkuNB3cZ4LEwWGc0BegmKfMoZJ6M"
sheet = client.open_by_key(SHEET_ID).sheet1  # Open the first sheet directly

def load_questions_from_sheet():
    """Load questions and options from Google Sheet."""
    # Fetch all data from the sheet
    data = sheet.get_all_records()
    questions = []
    
    # Parse data into the desired structure
    for row in data:
        question = {
            "question": row["question"],
            "options": [row["response1"], row["response2"], row["response3"], row["response4"]],
            "answer": row.get("answer")  # Optional: Add an "answer" column in Google Sheets if you want scoring
        }
        questions.append(question)
    
    return questions

# Load questions from the Google Sheet
questions = load_questions_from_sheet()

# Initialize session state variables for navigation
if 'current_question' not in st.session_state:
    st.session_state.current_question = 0
if 'user_answers' not in st.session_state:
    st.session_state.user_answers = [None] * len(questions)
if 'score' not in st.session_state:
    st.session_state.score = None

def display_question(index):
    """Display the question and answer choices for the current index."""
    question = questions[index]
    st.write(f"**Question {index + 1}:** {question['question']}")
    selected_option = st.radio(
        "Choose an answer:", 
        options=question["options"],
        index=st.session_state.user_answers[index] if st.session_state.user_answers[index] is not None else 0,
        key=f"question_{index}"
    )
    # Save the answer
    st.session_state.user_answers[index] = selected_option

def calculate_score():
    """Calculate the score based on user answers if an 'answer' field exists in Google Sheet data."""
    score = 0
    for i, user_answer in enumerate(st.session_state.user_answers):
        if user_answer == questions[i].get("answer"):  # Check against correct answer if available
            score += 1
    return score

# Display the current question
display_question(st.session_state.current_question)

# Navigation buttons
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    if st.session_state.current_question > 0:
        if st.button("Previous"):
            st.session_state.current_question -= 1

with col2:
    if st.session_state.current_question < len(questions) - 1:
        if st.button("Next"):
            st.session_state.current_question += 1

with col3:
    if st.session_state.current_question == len(questions) - 1:
        if st.button("Submit"):
            # Calculate the score once all questions are answered
            st.session_state.score = calculate_score()
            st.write(f"**Your Score:** {st.session_state.score}/{len(questions)}")
            st.session_state.current_question = 0  # Reset to the first question