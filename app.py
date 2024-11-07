from flask import Flask, render_template, request

app = Flask(__name__)

# Route for displaying the form
@app.route('/')
def index():
    return '''
        <h2>Enter Your Information</h2>
        <form method="POST" action="/submit">
            <label for="name">Name:</label>
            <input type="text" id="name" name="name" required><br><br>
            <label for="email">Email:</label>
            <input type="email" id="email" name="email" required><br><br>
            <input type="submit" value="Submit">
        </form>
    '''

# Route for handling form submission
@app.route('/submit', methods=['POST'])
def submit():
    # Retrieve user input from form fields
    name = request.form.get('name')
    email = request.form.get('email')
    
    # Display the user input on a new page
    return f'''
        <h2>Thank You for Submitting!</h2>
        <p><strong>Name:</strong> {name}</p>
        <p><strong>Email:</strong> {email}</p>
        <a href="/">Go back</a>
    '''

if __name__ == '__main__':
    app.run(debug=True)