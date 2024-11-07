import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# Define the scope for Google Sheets
scope = ["https://www.googleapis.com/auth/spreadsheets"]

# Test locally
#SERVICE_ACCOUNT_FILE = 'secrets/aswb-practice-exam-91c673a5a3a7.json'
#creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes = scope)

# Load Google Sheets credentials from Streamlit secrets
service_account_info = st.secrets["google_service_account"]
creds = Credentials.from_service_account_info(service_account_info, scopes = scope)
client = gspread.authorize(creds)

# Specify your Google Sheets ID and open the sheet
SHEET_ID = "1_IYoZGi6IqEd1ibOkuNB3cZ4LEwWGc0BegmKfMoZJ6M"
sheet = client.open_by_key(SHEET_ID).sheet1  # Open the first sheet directly

# Load questions from Google Sheets only once per session
if 'questions' not in st.session_state:
    def load_questions_from_sheet():
        """Load questions and options from Google Sheet."""
        data = sheet.get_all_records()
        questions = []
        for row in data:
            question = {
                "question": row["question"],
                "options": [row["response1"], row["response2"], row["response3"], row["response4"]],
                "answer": row.get("answer")  # Optional: Add an "answer" column in Google Sheets if you want scoring
            }
            questions.append(question)
        return questions

    st.session_state.questions = load_questions_from_sheet()
    st.session_state.current_question = 0
    st.session_state.user_answers = [None] * len(st.session_state.questions)
    st.session_state.score = None

questions = st.session_state.questions

# Navigation functions to handle button clicks
def next_question():
    if st.session_state.current_question < len(questions) - 1:
        st.session_state.current_question += 1

def prev_question():
    if st.session_state.current_question > 0:
        st.session_state.current_question -= 1

def submit_quiz():
    st.session_state.score = calculate_score()

def display_question(index):
    """Display the question and answer choices for the current index."""
    question = questions[index]
    st.write(f"**Question {index + 1}:** {question['question']}")
    
    # Set default index if no answer is selected
    default_index = question["options"].index(st.session_state.user_answers[index]) if st.session_state.user_answers[index] in question["options"] else 0
    
    selected_option = st.radio(
        "Choose an answer:", 
        options=question["options"],
        index=default_index,
        key=f"question_{index}"
    )
    
    # Save the answer
    st.session_state.user_answers[index] = selected_option

def calculate_score():
    """Calculate the score based on user answers if an 'answer' field exists in Google Sheet data."""
    score = sum(1 for i, answer in enumerate(st.session_state.user_answers) if answer == questions[i].get("answer"))
    return score

# Display the current question
display_question(st.session_state.current_question)

# Navigation buttons
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    st.button("Previous", on_click=prev_question)

with col2:
    st.button("Next", on_click=next_question)

with col3:
    st.button("Submit", on_click=submit_quiz)

# Display the score after submission
if st.session_state.score is not None:
    st.write(f"**Your Score:** {st.session_state.score}/{len(questions)}")