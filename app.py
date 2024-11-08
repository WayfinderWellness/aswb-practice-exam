import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
#from streamlit_elements import elements, mui

# Read the CSS file
with open("styles/style.css") as f:
    css = f.read()

# Inject CSS into the Streamlit app
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# Define the scope for Google Sheets and load Google Sheets credentials from Streamlit secrets
scope = ["https://www.googleapis.com/auth/spreadsheets"]
service_account_info = st.secrets["google_service_account"]
creds = Credentials.from_service_account_info(service_account_info, scopes=scope)
client = gspread.authorize(creds)
SHEET_ID = "1_IYoZGi6IqEd1ibOkuNB3cZ4LEwWGc0BegmKfMoZJ6M"
sheet = client.open_by_key(SHEET_ID).sheet1

# Define function to load questions from Google Sheets
def load_questions():
    data = sheet.get_all_records()
    questions = []
    for row in data:
        question = {
            "question": row["question"],
            "options": [row["response1"], row["response2"], row["response3"], row["response4"]],
            "answer": row.get("answer"),
            "explanation": row.get("explanation", "No explanation provided.")
        }
        questions.append(question)
    return questions

# Initialize session state variables
if 'questions' not in st.session_state:
    st.session_state.questions = load_questions()
    st.session_state.current_question = 0
    st.session_state.user_answers = [None] * len(st.session_state.questions)
    st.session_state.score = None
    st.session_state.quiz_completed = False
    st.session_state.pins = set()

questions = st.session_state.questions

# Function to get the user's selected answer or return an empty string if not answered
def get_user_answer(index):
    return st.session_state.user_answers[index] if st.session_state.user_answers[index] is not None else ""

# Navigation functions
def next_question():
    if st.session_state.current_question < len(questions) - 1:
        st.session_state.current_question += 1

def prev_question():
    if st.session_state.current_question > 0:
        st.session_state.current_question -= 1

# Pin toggle function
def toggle_pin(question_index):
    if question_index in st.session_state.pins:
        st.session_state.pins.remove(question_index)
    else:
        st.session_state.pins.add(question_index)

def jump_to_pinned_question(pin_index):
    st.session_state.current_question = pin_index

def submit_quiz():
    st.session_state.score = calculate_score()
    st.session_state.quiz_completed = True

def display_question(index):
    question = questions[index]

    # Display question text and options
    st.markdown(f'<div class="current-question"><strong>Question {index + 1}:</strong> {question["question"]}</div>', unsafe_allow_html=True)
    
    selected_option = st.session_state.user_answers[index]
    
    # Radio button with no initial selection if no answer has been selected
    user_answer = st.radio(
        "Choose an answer:", 
        options=question["options"],
        index=None if selected_option is None else question["options"].index(selected_option),
        key=f"question_option_{index}"
    )

    # Update selected answer in session state
    if user_answer:
        st.session_state.user_answers[index] = user_answer

def render_nav_btns(index):
    btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])

    with btn_col1:
        st.button("← Previous Question", on_click=prev_question, key="prev_btn", disabled=(st.session_state.current_question == 0))

    with btn_col2:
        pin_icon = "⭐" if index in st.session_state.pins else "☆"
        if st.button(f"{pin_icon} Pin Question", key=f"pin_toggle_{index}", on_click=toggle_pin, args=(index,)):
            pass 

    with btn_col3:
        if st.session_state.current_question < len(questions) - 1:
            st.button("Next Question →", on_click=next_question, key="next_btn")
        else:
            st.button("Submit Test ✓", on_click=submit_quiz, key="submit_btn")    

def calculate_score():
    return sum(1 for i, answer in enumerate(st.session_state.user_answers) if answer == questions[i].get("answer"))

# Display questions and navigation
if not st.session_state.quiz_completed:
    total_questions = len(st.session_state.questions)
    current_question = st.session_state.current_question + 1
    progress_percentage = current_question / total_questions * 100

    # Progress bar
    st.markdown(f"""
        <style>
            .progress-container {{
                width: 100%;
                background-color: rgba(0, 0, 0, 0.1);
                border: 1px solid rgba(0, 0, 0, 0.3);
                border-radius: 5px;
                height: 20px;
                margin-bottom: 20px;
            }}
            .progress-bar {{
                width: {progress_percentage}%;
                height: 100%;
                background-color: #348558;
                opacity: 0.9;
                border-radius: 5px 0 0 5px;
            }}
        </style>
        
        <div class="progress-container">
            <div class="progress-bar"></div>
        </div>
    """, unsafe_allow_html=True)

    # Display the current question
    display_question(st.session_state.current_question)

    render_nav_btns(st.session_state.current_question) 

    # Header row using three columns for "#", "Question", and "Your Answer"
    if len(st.session_state.pins) > 0:
        st.markdown(
            """
            <div class="table-header-row">
                <div class="table-header-cell" id="pinned-question-header-col1">Pinned Questions</div>
            </div>
            """, unsafe_allow_html = True
        )

    # Loop over pinned questions to display each question in a new row
    for pin_index in sorted(st.session_state.pins):
        pinned_question = questions[pin_index]["question"]
        options = [""] + questions[pin_index]["options"]
        current_answer = get_user_answer(pin_index) or "None"

        col1, col2 = st.columns([2, 10], vertical_alignment = "center")

        with col1:
            if st.button(f"Jump to {pin_index + 1}", key=f"jump_to_question_{pin_index}"):
                jump_to_pinned_question(pin_index)

        with col2:
            st.write(f"{pinned_question}\n\n\\(**Current Response:** {current_answer}\\)")

# Display score and feedback after submission
else:
    st.write(f"**Your Score:** {st.session_state.score}/{len(questions)}")
    for i, question in enumerate(questions):
        user_answer = st.session_state.user_answers[i]
        correct_answer = question["answer"]
        is_correct = user_answer == correct_answer
        result_icon = "✅" if is_correct else "❌"
        
        with st.expander(f"{result_icon} {i + 1}. {question['question']}"):
            st.write(f"**Your Answer:** {user_answer if user_answer else 'No answer selected'}")
            st.write(f"**Correct Answer:** {correct_answer}")
            st.write(f"**Explanation:** {question['explanation']}")