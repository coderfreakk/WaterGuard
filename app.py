from flask import Flask, request, jsonify, render_template, current_app
from flask_cors import CORS
import json
from datetime import date
import traceback
import os
import re
import smtplib
import threading #for db
from email.message import EmailMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Flask App Initialization
app = Flask(__name__)
CORS(app)

# --------------------- Gemini Chatbot Config ---------------------
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise Exception("❌ GOOGLE_API_KEY not found in .env")
os.environ['GOOGLE_API_KEY'] = GOOGLE_API_KEY

llm = ChatGoogleGenerativeAI(
    model="models/gemini-1.5-flash-latest",
    temperature=0.4
)
# @app.route('/test-mail', methods=['GET'])
# def test_mail():
#     try:
#         send_email(
#             to="vermatamanna409@gmail.com",
#             subject="Test Email",
#             body="If you got this, mailing works."
#         )
#         return jsonify({"message": "✅ Test email sent!"})
#     except Exception as e:
#         return jsonify({"message": f"❌ Failed: {str(e)}"})


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')

@app.route('/signup-form')
def signup_form():
    return render_template('signup.html')

@app.route('/water_test')
def water_test():
    return render_template('water_test.html')

@app.route('/book_kit')
def book_kit_page():
    return render_template('book_kit.html')



# ----------------------------------------------------------------------


@app.route('/chat', methods=['POST'])
def chat():
    data = request.json or {}
    user_prompt = data.get("prompt", "").strip()

    if not user_prompt:
        return jsonify({"reply": "❌ Please provide a valid question."}), 400

    try:
        prompt = (
            "You are AquaBot, an expert on water sanitation and cleaning. "
            "Give answers in bullet points where possible. "
            "Keep it concise and to the point, under 250 words. "
            "Avoid markdown symbols like ** and format each key point as a new line.\n\n"
            f"User's Question: {user_prompt}\n"
            "Answer:"
        )

        response = llm.invoke([HumanMessage(content=prompt)])
        raw = response.content.strip()

        # remove markdown bold and other simple markdown tokens
        text = re.sub(r"\*\*(.*?)\*\*", r"\1", raw)
        text = re.sub(r"`{1,3}(.*?)`{1,3}", r"\1", text)   # inline code backticks
        text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text)   # links [text](url) -> text

        # split into meaningful lines
        lines = []
        for line in text.splitlines():
            ln = line.strip()
            if not ln:
                continue
            # remove common list markers
            ln = re.sub(r'^[\-\*\u2022]\s*', '', ln)   # -, *, • 
            ln = re.sub(r'^\d+\.\s*', '', ln)          # 1. 2. etc
            lines.append(ln)

        # Fallback: if only one long line, try split by semicolon or comma into bullets
        if len(lines) <= 1:
            single = lines[0] if lines else text
            if len(single) > 120 and (',' in single or ';' in single):
                parts = re.split(r';\s+|,\s+', single)
                parts = [p.strip() for p in parts if p.strip()]
                if len(parts) > 1:
                    lines = parts

        # Build HTML reply
        if len(lines) > 1:
            html = "<ul>" + "".join(f"<li>{re.sub(r'<', '&lt;', item)}</li>" for item in lines) + "</ul>"
        else:
            # single short reply — preserve paragraphs
            # convert double-newlines to <p> blocks
            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
            html = "".join(f"<p>{re.sub(r'<', '&lt;', p)}</p>" for p in paragraphs)

        return jsonify({"reply": html})

    except Exception as e:
        current_app.logger.error("Chat handler error: %s", e, exc_info=True)
        return jsonify({"reply": f"❌ An error occurred: {str(e)}"}), 500


# --------------------- Email Sender Config ---------------------
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASS = os.getenv("SENDER_PASS")

if not SENDER_EMAIL or not SENDER_PASS:
    raise Exception("❌ Email credentials not found in .env")

def send_email(to, subject, body):
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = to

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(SENDER_EMAIL, SENDER_PASS)
        smtp.send_message(msg)


# --------------------- JSON STORAGE SETUP (ADDED) ---------------------
# --- ADDED: data directory and file paths
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
BOOKINGS_FILE = os.path.join(DATA_DIR, "bookings.json")

# --- ADDED: ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# --- ADDED: simple thread lock to reduce concurrent write collisions
_file_lock = threading.Lock()

def _read_json_file(path):
    """Return list from JSON file, or empty list if not present or invalid."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        # If file is corrupted, backup and start fresh list
        try:
            os.rename(path, path + ".bak")
        except Exception:
            pass
        return []

def _write_json_file(path, data):
    """Write JSON atomically (simple)."""
    # Acquire lock for thread-safety within the same process
    with _file_lock:
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        # atomic replace
        os.replace(tmp_path, path)

# ----------------------------------------------------------------------

# --------------------- Book Your Kit Route ---------------------
@app.route('/book-kit', methods=['GET', 'POST'])
def book_kit():
    if request.method == 'GET':
         return render_template("book_kit.html")

    data = request.json
    name = data.get("name")
    email = data.get("email")
    phone = data.get("phone")
    address = data.get("address")
    date_val = data.get("date")

        # --- ADDED: Save booking to bookings.json (minimal fields)
    try:
        booking_entry = {
            "name": name,
            "email": email,
            "phone": phone,
            "address": address,
            "date": date_val,
            "saved_at": str(date.today())
        }
        bookings = _read_json_file(BOOKINGS_FILE)
        bookings.append(booking_entry)
        _write_json_file(BOOKINGS_FILE, bookings)
    except Exception as ex:
        # log but do not break main flow
        current_app.logger.error("Failed to save booking to JSON: %s", ex, exc_info=True)

        # ---------------------------
    subject = "✅ WaterGuard Kit Booking Confirmed!"
    body = f"""Hi {name},

Thanks for booking your Water Testing Kit with 💧 WaterGuard!

📍 Address:
{address}

📦 Your kit will reach your doorstep by: {date}

📘 The kit includes:
- pH Level Tester
- TDS Meter
- Turbidity Check
- Temperature Sensor
- Setup Manual with Step-by-Step Instructions

If you have any questions, feel free to chat with AquaBot or reach out to our team!

Stay safe & drink clean 🌊  
— Team WaterGuard
"""
    try:
        send_email(email, subject, body)
        return jsonify({"message": "✅ Booking confirmed and email sent!"})
    except Exception as e:
        return jsonify({"message": f"❌ Email sending failed: {str(e)}"}), 500

# --------------------- Signup Route ---------------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template("signup.html")

    data = request.json
    name = data.get("name")
    email = data.get("email")

        # --- ADDED: capture optional phone and password if client sends them
    phone = data.get("phone")
    password = data.get("password")  # NOTE: storing plaintext — see warnings below

    # --- ADDED: Save signup to users.json
    try:
        user_entry = {
            "name": name,
            "email": email,
            "phone": phone,
            "password": password,
            "signup_date": str(date.today())
        }
        users = _read_json_file(USERS_FILE)
        users.append(user_entry)
        _write_json_file(USERS_FILE, users)
    except Exception as ex:
        current_app.logger.error("Failed to save signup to JSON: %s", ex, exc_info=True)

    subject = "🎉 Welcome to WaterGuard!"
    body = f"""Hi {name},

Thank you for signing up to 💧 WaterGuard — your smart partner for clean and safe water!

🚀 Features you now have access to:
- Check your water quality instantly
- Book doorstep testing kits
- Chat with AquaBot for water safety advice
- Get personalized insights & alerts

We’re excited to have you onboard!
Explore now: https://your-waterguard-site.com

Clean water. Clear life.  
— Team WaterGuard
"""
    try:
        send_email(email, subject, body)
        return jsonify({"message": "✅ Signup successful. Welcome email sent!"})
    except Exception as e:
        return jsonify({"message": f"❌ Email failed: {str(e)}"}), 500

# --------------------- Run the Combined App ---------------------
if __name__ == '__main__':
    app.run(debug=True, port=5000)
