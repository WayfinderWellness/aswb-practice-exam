import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# Read the CSS file
with open("styles/style.css") as f:
    css = f.read()

# Inject CSS into the Streamlit app
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

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

# Initialize bookmarks in session state if not already present
if 'bookmarks' not in st.session_state:
    st.session_state.bookmarks = set()  # Use a set to avoid duplicates

# Bookmark handling function
def toggle_bookmark(question_index):
    """Add or remove the question from bookmarks."""
    if question_index in st.session_state.bookmarks:
        st.session_state.bookmarks.remove(question_index)
    else:
        st.session_state.bookmarks.add(question_index)

# Jump to a specific question
def go_to_question(index):
    """Set the current question to the specified index."""
    st.session_state.current_question = index

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
    """Display the question, answer choices, and bookmark icon."""
    question = questions[index]
    
    # Display question with a bookmark icon
    bookmark_icon = "⭐" if index in st.session_state.bookmarks else "☆"
    if st.button(f"{bookmark_icon} Bookmark", key=f"bookmark_{index}", on_click=toggle_bookmark, args=(index,)):
        pass  # The button click updates the bookmark state

    # Display question text with the current question number
    st.markdown(f'<div class="current-question"><strong>Question {index + 1}:</strong> {question["question"]}</div>', unsafe_allow_html=True)

    # Determine if there's a previously selected answer
    selected_option = st.session_state.user_answers[index]

    # Add a placeholder option to avoid any preselection
    options_with_placeholder = ["Select an answer"] + question["options"]

    # Display the radio button with the placeholder as the default
    user_answer = st.radio(
        "Choose an answer:", 
        options=options_with_placeholder,
        index=0 if selected_option is None else options_with_placeholder.index(selected_option),
        key=f"question_{index}"
    )

    # Update the answer in session state if a valid option is chosen
    if user_answer != "Select an answer":
        st.session_state.user_answers[index] = user_answer

def calculate_score():
    """Calculate the score based on user answers if an 'answer' field exists in Google Sheet data."""
    score = sum(1 for i, answer in enumerate(st.session_state.user_answers) if answer == questions[i].get("answer"))
    return score

# Display the quiz questions if not yet submitted
if 'quiz_completed' not in st.session_state or not st.session_state.quiz_completed:
    # Calculate progress
    total_questions = len(st.session_state.questions)
    current_question = st.session_state.current_question + 1
    progress_percentage = current_question / total_questions * 100  # Convert to percentage

    # Display progress bar at the top
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

    # Navigation buttons in two columns 
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        st.button("Previous", on_click=prev_question, key="prev_btn", disabled=(st.session_state.current_question == 0))
    with btn_col2:
        if st.session_state.current_question < len(questions) - 1:
            st.button("Next", on_click=next_question, key = "next_btn")
        elif st.session_state.current_question == len(questions) - 1:
            st.button("Submit", on_click = submit_quiz, key = "submit_btn")

    # Expander to show bookmarked questions
    with st.expander("View Bookmarked Questions"):
        if st.session_state.bookmarks:
            for bookmark_index in sorted(st.session_state.bookmarks):
                bookmarked_question = questions[bookmark_index]["question"]
                # Display the question text as a clickable button with a unique key
                if st.button(f"Question {bookmark_index + 1}: {bookmarked_question}", key=f"bookmark_{bookmark_index}_question"):
                    st.session_state.current_question = bookmark_index
        else:
            st.write("No questions bookmarked.")

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

        with st.expander(f"{result_icon} {i + 1}. {question['question']}"):
            st.write(f"**Your Answer:** {user_answer if user_answer else 'No answer selected'}")
            st.write(f"**Correct Answer:** {correct_answer}")
            st.write(f"**Explanation:** {question['explanation']}")