import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# Define the scope for Google Sheets
scope = ["https://www.googleapis.com/auth/spreadsheets"]

# Load Google Sheets credentials from Streamlit secrets
service_account_info = st.secrets["google_service_account"]
creds = Credentials.from_service_account_info(service_account_info, scopes=scope)
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
                "answer": row.get("answer"),
                "explanation": row.get("explanation", "No explanation provided.")  # Get explanation if available
            }
            questions.append(question)
        return questions

    st.session_state.questions = load_questions_from_sheet()
    st.session_state.current_question = 0
    st.session_state.user_answers = [None] * len(st.session_state.questions)  # Initialize answers to None for each question
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
    st.session_state.quiz_completed = True  # Set a flag to indicate the quiz is complete

def display_question(index):
    """Display the question and answer choices for the current index."""
    question = questions[index]
    st.write(f"**Question {index + 1}:** {question['question']}")

    # Determine if there's a previously selected answer
    selected_option = st.session_state.user_answers[index]
    
    # Set index=None if no answer has been selected for a true unselected state
    if selected_option is None:
        user_answer = st.radio(
            "Choose an answer:", 
            options=question["options"],
            index=None,  # No option selected by default
            key=f"question_{index}"
        )
    else:
        # Display the radio with the previously selected answer as the default
        user_answer = st.radio(
            "Choose an answer:", 
            options=question["options"],
            index=question["options"].index(selected_option),
            key=f"question_{index}"
        )
    
    # Update the answer in session state
    if user_answer:
        st.session_state.user_answers[index] = user_answer

def calculate_score():
    """Calculate the score based on user answers if an 'answer' field exists in Google Sheet data."""
    score = sum(1 for i, answer in enumerate(st.session_state.user_answers) if answer == questions[i].get("answer"))
    return score

# Display the quiz questions if not yet submitted
if 'quiz_completed' not in st.session_state or not st.session_state.quiz_completed:
    # Display the current question
    display_question(st.session_state.current_question)

    # Navigation buttons
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        # Only show "Previous" button if not on the first question
        if st.session_state.current_question > 0:
            st.button("Previous", on_click=prev_question)

    with col2:
        # Show "Next" button if not on the last question
        if st.session_state.current_question < len(questions) - 1:
            st.button("Next", on_click=next_question)
        # Show "Submit" button on the last question
        elif st.session_state.current_question == len(questions) - 1:
            st.button("Submit", on_click=submit_quiz)

else:
    # Display the score after submission
    st.write(f"**Your Score:** {st.session_state.score}/{len(questions)}")

    # Display expanders for each question with feedback
    for i, question in enumerate(questions):
        user_answer = st.session_state.user_answers[i]
        correct_answer = question["answer"]
        is_correct = user_answer == correct_answer

        # Choose emoji based on correctness
        result_icon = "✅" if is_correct else "❌"
        result_text = f"{result_icon} {'Correct' if is_correct else 'Incorrect'}"

        with st.expander(f"Question {i + 1}: {question['question']}"):
            st.write(result_text)
            st.write(f"**Your Answer:** {user_answer if user_answer else 'No answer selected'}")
            st.write(f"**Correct Answer:** {correct_answer}")
            st.write(f"**Explanation:** {question['explanation']}")