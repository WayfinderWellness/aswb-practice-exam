import streamlit as st

# Load the external CSS file
def load_css(file_path):
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Apply the CSS file
load_css("styles/styles.css")


# Display a title for the app
st.title("Enter Your Information")

# Create a form with Streamlit's built-in features
with st.form("user_form"):
    name = st.text_input("Name")
    email = st.text_input("Email")
    submit_button = st.form_submit_button("Submit")

# Display the submitted information after the form is submitted
if submit_button:
    st.write("Thank You for Submitting!")
    st.write(f"**Name:** {name}")
    st.write(f"**Email:** {email}")