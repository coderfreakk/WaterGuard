from flask import Flask, request, jsonify
from flask_cors import CORS
import smtplib
from email.message import EmailMessage

app = Flask(__name__)
CORS(app)

# 🔐 Your credentials
SENDER_EMAIL = "tamannaberma11a@gmail.com"
SENDER_PASS = "nhyi pnfn wbyv xhka"

# 📧 Helper function
def send_email(to, subject, body):
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = to

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(SENDER_EMAIL, SENDER_PASS)
        smtp.send_message(msg)

# 📦 Route: Book your kit
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

# 👤 Route: Signup
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

# 🏃 Run this app separately
if __name__ == '__main__':
    app.run(port=5001, debug=True)

    
