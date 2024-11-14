import dash
import dash_bootstrap_components as dbc
from dash import html
from dotenv import load_dotenv
import os
import gspread
from google.oauth2.service_account import Credentials

# Initialize Dash app
app = dash.Dash(__name__, requests_pathname_prefix="/aswb-masters-exam/", serve_locally=True, external_stylesheets=[dbc.themes.LITERA])
app.title = "ASWB Master's Level Practice Exam"

# Load environment variables
load_dotenv()

# Google Sheets Setup
scope = ["https://www.googleapis.com/auth/spreadsheets"]
service_account_info = {
    "type": os.getenv("TYPE"),
    "project_id": os.getenv("PROJECT_ID"),
    "private_key_id": os.getenv("PRIVATE_KEY_ID"),
    "private_key": os.getenv("PRIVATE_KEY").replace('\\n', '\n'),  # Ensure line breaks are handled correctly
    "client_email": os.getenv("CLIENT_EMAIL"),
    "client_id": os.getenv("CLIENT_ID"),
    "auth_uri": os.getenv("AUTH_URI"),
    "token_uri": os.getenv("TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("AUTH_PROVIDER_X509_CERT_URL"),
    "client_x509_cert_url": os.getenv("CLIENT_X509_CERT_URL"),
    "universe_domain": os.getenv("UNIVERSE_DOMAIN")
}

try:
    creds = Credentials.from_service_account_info(service_account_info, scopes=scope)
    client = gspread.authorize(creds)
    # Retrieve data
    SHEET_ID = "1_IYoZGi6IqEd1ibOkuNB3cZ4LEwWGc0BegmKfMoZJ6M"
    sheet = client.open_by_key(SHEET_ID).sheet1
    data = sheet.get_all_records()
    google_sheets_status = "Google Sheets loaded successfully."
except Exception as e:
    google_sheets_status = f"Error loading Google Sheets: {e}"

app.layout = html.Div([
    html.H1("Google Sheets Test Layout"),
    html.P(google_sheets_status),
    dbc.Row([
        dbc.Col(html.H1("ASWB Master's Level Practice Exam", className="text-center my-4"), width=12),
        dbc.Col(html.P(google_sheets_status), width=12),
    ])
])

if __name__ == "__main__":
    app.run_server(debug=True)