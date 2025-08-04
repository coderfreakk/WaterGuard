from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import smtplib
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

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_prompt = data.get("prompt", "")

    if not user_prompt:
        return jsonify({"reply": "❌ Please provide a valid question."}), 400

    try:
        prompt = (
            "You are AquaBot, an expert on water sanitation and cleaning. "
            "Answer the user's question clearly and accurately with practical and reliable information.\n\n"
            f"User's Question: {user_prompt}\n"
            "Answer:"
        )
        response = llm.invoke([HumanMessage(content=prompt)])
        return jsonify({"reply": response.content.strip()})
    except Exception as e:
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

# --------------------- Book Your Kit Route ---------------------
@app.route('/book-kit', methods=['POST'])
def book_kit():
    data = request.json
    name = data.get("name")
    email = data.get("email")
    phone = data.get("phone")
    address = data.get("address")
    date = data.get("date")

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
@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    name = data.get("name")
    email = data.get("email")

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
