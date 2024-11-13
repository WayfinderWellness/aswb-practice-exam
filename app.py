import dash
import dash_bootstrap_components as dbc
from dash.dependencies import ALL
from dash import html, dcc, Input, Output, State, callback_context
import json
from dotenv import load_dotenv
import os
import gspread
from google.oauth2.service_account import Credentials
import plotly.graph_objs as go

# Initialize Dash app with desired theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LITERA])
app.title = "ASWB Master's Level Practice Exam"

# Expose the underlying Flask server
server = app.server

# Google Sheets Setup
scope = ["https://www.googleapis.com/auth/spreadsheets"]

# Load environment variables from .env file
load_dotenv()

# Access each environment variable
service_account_info = {
    "type": os.getenv("TYPE"),
    "project_id": os.getenv("PROJECT_ID"),
    "private_key_id": os.getenv("PRIVATE_KEY_ID"),
    "private_key": os.getenv("PRIVATE_KEY"),
    "client_email": os.getenv("CLIENT_EMAIL"),
    "client_id": os.getenv("CLIENT_ID"),
    "auth_uri": os.getenv("AUTH_URI"),
    "token_uri": os.getenv("TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("AUTH_PROVIDER_X509_CERT_URL"),
    "client_x509_cert_url": os.getenv("CLIENT_X509_CERT_URL"),
    "universe_domain": os.getenv("UNIVERSE_DOMAIN")
}

creds = Credentials.from_service_account_info(service_account_info, scopes=scope)
client = gspread.authorize(creds)
SHEET_ID = "1_IYoZGi6IqEd1ibOkuNB3cZ4LEwWGc0BegmKfMoZJ6M"
sheet = client.open_by_key(SHEET_ID).sheet1

# Load questions from Google Sheets
def load_questions():
    data = sheet.get_all_records()
    questions = []
    for row in data:
        question = {
            "question": row["question"],
            "options": [row["response1"], row["response2"], row["response3"], row["response4"]],
            "answer": row.get("answer"),
            "explanation": row.get("explanation", "No explanation provided."),
            "category": row.get("category", "No category provided.")
        }
        questions.append(question)
    return questions

# Define global variables
questions = load_questions()
total_questions = len(questions)

# Unique categories for toggle buttons
categories_for_filter = list(dict.fromkeys([question['category'] for question in questions]))

# Define colors for category labels outside any function
category_colors = {}

# Function to assign a unique color to each category
def get_category_color(category):
    if category not in category_colors:
        # Define a color palette to use for categories
        color_palette = [
            "#c20000", "#0074c2", "#28a745", "#ff7f0e", "#9467bd",
            "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
        ]
        # Assign a new color from the palette or cycle through if exceeded
        color = color_palette[len(category_colors) % len(color_palette)]
        category_colors[category] = color
    return category_colors[category]

# App layout with Bootstrap components
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("ASWB Master's Level Practice Exam", className="text-center my-4"), width=12)
    ]),
    dbc.Row([
        dbc.Col(id='question-container', width=12, className="mb-4")
    ]),
    dbc.Row([
        dbc.Col(
            dcc.RadioItems(id='answer-options', options=[], value=None, className="mb-3"),
            width=12
        )
    ]),
    dbc.Row([
        dbc.Col(dbc.Button("← Previous Question", id='prev-question', outline=True, color="primary", className="me-2"), width="auto"),
        dbc.Col(dbc.Button("Pin Question 📌", id='pin-question', outline=True, color="primary", className="me-2"), width="auto"),
        dbc.Col([
            dbc.Button("Next Question →", id='next-question', outline=True, color="primary", className="me-2"),
            dbc.Button("Submit Test 📋", id='submit-quiz', outline=True, color="primary")
        ], width="auto")
    ], id="navigation-buttons-row", className="mb-4 nav-buttons justify-content-around"),
    dbc.Row([
        dbc.Col(id='pinned-questions', width=12, className="mb-4")
    ], id="pinned-questions-row", className=""),
    dbc.Row([
        dbc.Col(id='score-display', width=12, className="mb-4")
    ]),
    html.Div(id="category-filter-wrapper", children=[
        html.Div(
            category, 
            id={'type': 'category-toggle', 'index': category},
            className="category-button selected",
            style={
                "color": get_category_color(category), 
                "backgroundColor": get_category_color(category), 
                "borderColor": get_category_color(category), 
                "borderWidth": "2px",
                "borderStyle": "solid"
            }
        ) for category in categories_for_filter
    ],  style={"display": "none"} # Initially hidden
    ),
    dbc.Accordion(
        id="filtered-question-accordion",
        start_collapsed=True,
        children=[],
        style={"display": "none"}  # Initially hidden
    ),
    # Hidden Divs for storing state
    dcc.Store(id='current-question', data=0),
    dcc.Store(id='user-answers', data=[None] * len(questions)),
    dcc.Store(id='pins', data=[]),
    dcc.Store(id='jumped-question', data={'index': None}),
    dcc.Store(id='quiz-submitted', data=False),
    dcc.Store(id="category-selection-store", data=categories_for_filter)
], fluid=True, style={"maxWidth": "880px"})

# Callback function to conditionally hide navigation buttons and pinned questions if quiz is submitted
@app.callback(
    [Output('navigation-buttons-row', 'className'),
     Output('pinned-questions-row', 'className')],
    [Input('submit-quiz', 'n_clicks')]
)
def hide_quiz_rows(submit_clicks):
    if submit_clicks:
        navigation_buttons_row_class = "mb-4 nav-buttons justify-content-around hidden"
        pinned_questions_row_class = "hidden"
    else:
        navigation_buttons_row_class = "mb-4 nav-buttons justify-content-around"
        pinned_questions_row_class = ""
    return navigation_buttons_row_class, pinned_questions_row_class

# Callback to update "Pin Question" button text depending upon whether the question has been pinned yet
@app.callback(
    [Output('pin-question', 'children'),
     Output('pin-question', 'className')],
    [Input('current-question', 'data')],
    [State('pins', 'data')]
)
def update_pin_button(current_question, pins):
    # Check if the current question is pinned
    if current_question in pins:
        pin_question_text = "Unpin Question ❌"
        pin_question_class = "me-2 already-pinned"
    else:
        pin_question_text = "Pin Question 📌"
        pin_question_class = "me-2"
    return pin_question_text, pin_question_class

# Callback to conditionally enable/disable buttons
@app.callback(
    [Output('next-question', 'disabled'),
     Output('next-question', 'className'),
     Output('submit-quiz', 'disabled'),
     Output('submit-quiz', 'className')],
    Input('current-question', 'data')
)
def update_button_states(current_question):
    # Check if the user is on the last question
    is_last_question = current_question == total_questions - 1

    # Set disabled state for both buttons
    next_disabled = is_last_question  # Disable Next Question if on the last question
    submit_disabled = not is_last_question  # Enable Submit Test only on the last question

    # Set display CSS attribute for both buttons
    next_class = "button-class-sx" if is_last_question else ""
    submit_class = "button-class-sx" if not is_last_question else ""

    return next_disabled, next_class, submit_disabled, submit_class

# Callback to toggle selected categories
@app.callback(
    Output("category-selection-store", "data"),
    Input({"type": "category-toggle", "index": ALL}, "n_clicks"),
    State("category-selection-store", "data")
)
def toggle_category_selection(n_clicks_list, selected_categories):
    ctx = callback_context
    if not ctx.triggered:
        return selected_categories

    # Identify the clicked category from the triggered ID
    clicked_category = ctx.triggered[0]["prop_id"].split(".")[0]
    category = json.loads(clicked_category)["index"]

    # Toggle the selected category
    if category in selected_categories:
        selected_categories.remove(category)
    else:
        selected_categories.append(category)

    return selected_categories

# Client-side callback to dynamically update button classes
app.clientside_callback(
    """
    function(selectedCategories) {
        const buttons = document.querySelectorAll('.category-button');
        buttons.forEach(button => {
            const category = button.id.split('index":"')[1].split('"')[0];
            if (selectedCategories.includes(category)) {
                button.classList.add("selected");
            } else {
                button.classList.remove("selected");
            }
        });
        return window.dash_clientside.no_update;
    }
    """,
    Output("category-filter-wrapper", "children"),
    Input("category-selection-store", "data")
)

@app.callback(
    Output("filtered-question-accordion", "children"),
    Output("filtered-question-accordion", "style"),
    Output("category-filter-wrapper", "style"),
    [Input("category-selection-store", "data"),
    Input("quiz-submitted", "data")],
    State("user-answers", "data")
)
def update_question_accordion(selected_categories, quiz_submitted, user_answers):
    # Ensure user_answers is defined
    if user_answers is None:
        user_answers = [None] * len(questions)

    # If the quiz hasn't been submitted yet, don't show the accordion
    if not quiz_submitted:
        return [], {"display": "none"}, {"display": "none"}

    # Generate accordion items only for filtered questions
    accordion_items = [
        dbc.AccordionItem(
            [
                html.P([html.Strong("Your Answer: "), f"{user_answers[i] if user_answers[i] else 'No answer selected'}"]),
                html.P([html.Strong("Correct Answer: "), question['answer']]),
                html.P([html.Strong("Explanation: "), question['explanation']])
            ],
            title=dbc.Row([
                dbc.Col(
                    "✅" if user_answers[i] == question['answer'] else "❌", 
                    width="auto", 
                    className="icon-column", 
                    style={"font-size": "1.5em"}
                ),
                dbc.Col(
                    html.Span([
                        html.Strong(f"Question {i + 1}: "),
                        html.Span(question['question'])
                    ]),
                    className="question-column",
                    style={"display": "flex", "align-items": "center"}
                ),
                dbc.Col(
                    html.Div(f"{question['category']}", className="question-category"),
                    width="auto",
                    className="question-accordion-category",
                    style={"background-color": get_category_color(question['category'])}
                )
            ], align="center"),
            className="mb-2 question-result-container " +
                      ("correct-answer-header" if user_answers[i] == question['answer'] else "incorrect-answer-header")
        )
        for i, question in enumerate(questions) if question['category'] in selected_categories
    ]

    # Set the accordion to be visible
    return accordion_items, {"display": "block"}, {"display": "flex"}

# Main callback to handle quiz actions
@app.callback(
    [Output('question-container', 'children'),          # Only question-container children now
     Output('user-answers', 'data'),                    # User answers
     Output('pinned-questions', 'children'),            # Pinned questions list
     Output('score-display', 'children'),               # Score display
     Output('current-question', 'data'),                # Current question
     Output('pins', 'data'),                            # Pins for pinned questions
     Output('quiz-submitted', 'data')],                 # Whether the user has submitted the quiz yet
    [Input('next-question', 'n_clicks'),                # Next button click
     Input('prev-question', 'n_clicks'),                # Previous button click
     Input('submit-quiz', 'n_clicks'),                  # Submit button click
     Input('pin-question', 'n_clicks'),                 # Pin button click
     Input({'type': 'jump-question', 'index': ALL}, 'n_clicks'),   # Jump button clicks
     Input({'type': 'unpin-question', 'index': ALL}, 'n_clicks')], # Unpin question
    [State('jumped-question', 'data'),                  # Track jump to question
     State('user-answers', 'data'),                     # Track user answers
     State('current-question', 'data'),                 # Track current question
     State('answer-options', 'value'),                  # Track selected answer (inside RadioItems)
     State('pins', 'data')]                             # Track pinned questions
)
def handle_quiz_actions(next_clicks, 
                        prev_clicks, 
                        submit_clicks, 
                        pin_clicks, 
                        jump_clicks_list,
                        unpin_clicks_list,
                        jumped_question, 
                        user_answers, 
                        current_question, 
                        selected_answer, 
                        pins):
    ctx = callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
    score_display = dash.no_update
    pinned_display = []

    # Check if a Jump button was clicked
    if triggered_id and 'jump-question' in triggered_id:
        # Identify which Jump button was clicked by checking the `index` in the triggered_id
        button_id = json.loads(triggered_id.split('.')[0])  # Parses the JSON-like ID
        clicked_index = button_id['index']  # Extracts the index
        current_question = clicked_index  # Update current_question to this index

    # Save the selected answer
    if selected_answer is not None:
        user_answers[current_question] = selected_answer

    # Handle navigation: Next or Previous Question
    if triggered_id == 'next-question':
        if current_question < len(questions) - 1:
            current_question += 1

    # Handle nevigation to the previous question        
    elif triggered_id == 'prev-question' and current_question > 0:
        current_question -= 1

    # Handle quiz submission, hiding elements, calculating score, and rendering output
    elif triggered_id == 'submit-quiz':
        quiz_submitted = True
        score = sum(1 for i, answer in enumerate(user_answers) if answer == questions[i]['answer'])

        # Initialize score_display as a list to prevent errors when appending items
        score_display = [
            html.H2("Practice Exam Results", className="mt-4 mb-3"),
            html.P("The chart and table below show your practice test results by question category."),
            html.P(
                "The actual exam consists of 150 questions. Passing scores are graded on a curve, but, typically, "
                "you need between 98-107 correct responses to pass the exam."
            ),
            html.Ul([
                html.Li([
                    "Categories shown in ", 
                    html.Span("green", className="bold green-text"), 
                    " are above the 107 correct pace (more than 71% correct)."
                ]),
                html.Li([
                    "Categories shown in ", 
                    html.Span("yellow", className="bold yellow-text"), 
                    " fall between the 98-107 correct pace (between 65%-71% correct)."
                ]),
                html.Li([
                    "Categories shown in ", 
                    html.Span("red", className="bold red-text"), 
                    " fall below the 98 correct pace (less than 65% correct)."
                ])                
            ])
        ]

        category_scores = {}
        for i, question in enumerate(questions):
            category = question["category"]
            is_correct = user_answers[i] == question['answer']
            
            # Initialize category data if not already present
            if category not in category_scores:
                category_scores[category] = {"correct": 0, "total": 0}
                
            # Update counts
            category_scores[category]["total"] += 1
            if is_correct:
                category_scores[category]["correct"] += 1
        
        # Generate table rows for each category with scores and percentages
        table_rows = []
        categories = []
        scores_percent = []
        for category, score_data in category_scores.items():
            correct = score_data['correct']
            total = score_data['total']
            percent = (correct / total) * 100 if total > 0 else 0
            table_rows.append(html.Tr([
                html.Td(category),
                html.Td(f"{correct} / {total} ({percent:.1f}%)")
            ]))
            # Store data for the chart
            categories.append(category)
            scores_percent.append(percent)
        
        # Create the score table
        category_score_table = dbc.Table(
            [
                html.Thead(html.Tr([
                    html.Th("Category"),
                    html.Th("Your Score")
                ])),
                html.Tbody(table_rows) 
            ],
            bordered=True,
            striped=True,
            hover=True,
            className="mt-3 results-category-table"
        )

        # Add the overall score as the last row with a darker background
        overall_percent = (score / len(questions)) * 100 if len(questions) > 0 else 0
        table_rows.append(html.Tr([
            html.Td("Overall Score", style={"font-weight": "bold", "background-color": "#FFDD6C", "color": "#222222"}),
            html.Td(f"{score} / {len(questions)} ({overall_percent:.1f}%)", style={"font-weight": "bold", "background-color": "#FFDD6C", "color": "#222222"})
        ]))

        # Function to add line breaks for long labels
        def wrap_text(text, max_line_length=22):
            words = text.split()
            wrapped_text = ''
            current_line = '<br>'

            for word in words:
                if len(current_line + word) <= max_line_length:
                    current_line += (word + ' ')
                else:
                    wrapped_text += current_line.rstrip() + '<br>'
                    current_line = word + ' '
            
            wrapped_text += current_line.rstrip()  # Add the last line
            return wrapped_text

        # Add the overall score to the categories
        categories.append("Overall Score")
        scores_percent.append(overall_percent)

        # Apply the function to each category
        wrapped_categories = [wrap_text(category) for category in categories]

        # Define color based on percentage
        def get_color(score):
            if score < 65.33:
                return '#BE2F2B'
            elif 65.33 <= score <= 71.33:
                return '#E4BB3F'
            else:
                return '#348558'
            
        # Generate color list based on scores
        colors = [get_color(score) for score in scores_percent]
        
        # Create the column chart for category scores
        score_chart = dcc.Graph(
            figure={
                "data": [
                    go.Bar(
                        x=wrapped_categories,
                        y=scores_percent,
                        marker_color=colors,
                        text=[f"{round(score, 0)}%" for score in scores_percent],
                        textposition='inside',
                        insidetextanchor="end",
                        textfont=dict(
                            size=14,                
                            color='#FFFFFF', 
                            family="Source Sans Pro", 
                            weight='bold'
                        )
                    )
                ],
                "layout": go.Layout(
                    title="",
                    title_font=dict(size=18),
                    xaxis=dict(
                        title="",
                        title_font=dict(size=14),
                        tickangle=0,
                        automargin=True
                    ),
                    yaxis=dict(title="Score (Percentage)", title_font=dict(size=14), range=[0, 100]),
                    margin=dict(l=40, r=40, t=60, b=80),
                    plot_bgcolor='#F7F0E6',
                    paper_bgcolor='#F7F0E6',
                    shapes=[
                        dict(
                            type="line",
                            x0=0,
                            x1=1,
                            y0=65.33, # Horizontal line at y = 65.33
                            y1=65.33, 
                            xref="paper",  # Use 'paper' to make x-coordinates relative to plot width
                            yref="y",
                            line=dict(color="rgba(34, 34, 34, 0.4)", width=2, dash="dash")
                        ),
                        dict(
                            type="line",
                            x0=0,
                            x1=1,
                            y0=71.33, # Horizontal line at y = 71.33
                            y1=71.33,
                            xref="paper",
                            yref="y",
                            line=dict(color="rgba(34, 34, 34, 0.4)", width=2, dash="dash")
                        )
                    ],
                    annotations=[
                        dict(
                            x=1,  
                            y=65.33,
                            xref="paper",
                            yref="y",
                            text="98", # Position at the end of the line
                            showarrow=False,
                            xanchor="left",
                            font=dict(color="#222222", size=14, weight="bold")
                        ),
                        dict(
                            x=1,
                            y=71.33,
                            xref="paper",
                            yref="y",
                            text="107", # Annotation for the 71.33 line
                            showarrow=False,
                            xanchor="left",
                            font=dict(color="#222222", size=14, weight="bold")
                        )
                    ]
                )
            },
            config={
                'staticPlot': True,  # Disable all interactions
                'displayModeBar': False  # Hide the mode bar that appears on hover
            }
        )

        # Add the score table and chart to the score display
        score_display.extend([score_chart, category_score_table])

        # Add the H2 header for the next section
        individual_question_review_h2 = html.H2("Individual Question Review", className="mt-4 mb-3")
        score_display.extend([individual_question_review_h2])

        # Add the category filter toggle buttons, setting them to be visible
        #category_filter_checklist = dcc.Checklist(
        #    id="category-filter",
        #    options=[
        #        {"label": category, "value": category}
        #        for category in categories_for_filter
        #    ],
        #    value=categories_for_filter,  # Initially select all categories
        #    inline=True,
        #    #inputStyle={"display": "none"},  # Hide native checkbox
        #    style={"display": "flex"}  # Set to visible
        #)

        # Wrap the checklist in a Div with a class for custom CSS styling
        #category_filter_wrapper = html.Div(
        #    category_filter_checklist,
        #    id="category-filter-wrapper",
        #    className="category-toggle"
        #)

        # Add the question accordion, setting it to be visible
        question_accordion = dbc.Accordion(
            id="filtered-question-accordion",
            start_collapsed=True,
            style={"display": "block"}  # Set to visible
        )

        # Extend score_display to include the checklist
        #score_display.extend([category_filter_wrapper, question_accordion])
        score_display.extend(question_accordion)
        
        # Define the question accordion
        #question_accordion = dbc.Accordion(id="filtered-question-accordion", start_collapsed=True)
        
        # Add the accordion to the score display
        #score_display.append(question_accordion)
        
        # Hide other quiz components (optional, based on previous setup)
        current_question = None  # Reset current question if needed
        return None, user_answers, None, score_display, current_question, pins, quiz_submitted

    # Handle pinning questions
    elif triggered_id == 'pin-question':
        if current_question in pins:
            pins.remove(current_question)
        else:
            pins.append(current_question)

    # Handle Unpin if any unpin button was clicked
    if triggered_id and 'unpin-question' in triggered_id:
        button_id = json.loads(triggered_id.split('.')[0])
        unpin_index = button_id['index']
        if unpin_index in pins:
            pins.remove(unpin_index)

    # Prepare pinned questions display
    for pin_index in sorted(pins):
        # Get the current response for each question
        current_response = user_answers[pin_index] if user_answers[pin_index] is not None else "None"

        # Iterate over each pin in pinned questions
        pinned_display.append(
            dbc.ListGroupItem(
                dbc.Row([
                    dbc.Col(
                        html.Span([
                            html.Strong(f"Question {pin_index + 1}: "),
                            f"{questions[pin_index]['question']} (",
                            html.Span([
                                html.Strong("Current response: "),  # Bold "Current response:"
                                f"{current_response})"  # Regular weight for the actual response
                            #], style={"display": "block", "margin-top": "0.33em", "font-size": "1em"})  # Block display for new line
                            ])  # Block display for new line
                        ]),
                        className="pinned-question-text"
                    ),
                    dbc.Col(
                        dbc.Button(f"Go to {pin_index + 1} 🔗", id={'type': 'jump-question', 'index': pin_index}, color="primary", className="ms-2 pinned-question-button go-to-question"),
                        width="auto",
                        className="pinned-question-button-container",
                        id="go-to-question-container"
                    ),
                    dbc.Col(
                        dbc.Button("Unpin ❌", id={'type': 'unpin-question', 'index': pin_index}, color="primary", className="ms-2 pinned-question-button unpin-question"),
                        width="auto",
                        className="pinned-question-button-container",
                        id="unpin-question-container"
                    )
                ], align="center")
            )
        )

    # Prepare to display the current question and options
    question = questions[current_question]
    options = [{'label': option, 'value': option} for option in question["options"]]
    selected_answer = user_answers[current_question] if user_answers[current_question] is not None else None
    
    return (
        dbc.Card([
            dbc.CardHeader(f"Question {current_question + 1}"),
            dbc.CardBody([
                html.H4(question['question'], className="question-text"),
                dcc.RadioItems(
                    id='answer-options',
                    options=[{'label': option, 'value': option} for option in question["options"]],
                    value=selected_answer,
                    className="mt-3",
                ),
            ])
        ]),
        user_answers,
        dbc.ListGroup(pinned_display),
        score_display,
        current_question,
        pins,
        dash.no_update
    )

# Run the app
if __name__ == "__main__":
    #app.run_server(debug=True)
    app.run_server(debug=True, host="0.0.0.0", port=8050)