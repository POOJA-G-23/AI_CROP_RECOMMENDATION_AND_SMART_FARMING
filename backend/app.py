from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS
import random, os, json, math, datetime, hashlib
from functools import wraps
import smtplib, threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "aicropadvisor_secret_2026")
CORS(app, supports_credentials=True)

# ══════════════════════════════════════════════════════════════════════════════
#  EMAIL CONFIG  (set these env vars before running)
#  MAIL_SENDER  – your Gmail address e.g. yourapp@gmail.com
#  MAIL_PASSWORD – Gmail App Password (16-char, not your login password)
#                  Generate at: myaccount.google.com → Security → App Passwords
# ══════════════════════════════════════════════════════════════════════════════
MAIL_SENDER   = os.environ.get("MAIL_SENDER", "")
MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
MAIL_ENABLED  = bool(MAIL_SENDER and MAIL_PASSWORD)

def _send_email_worker(to_email: str, subject: str, html_body: str):
    """Send an HTML email via Gmail SMTP (runs in background thread)."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"AI Crop Advisor <{MAIL_SENDER}>"
        msg["To"]      = to_email
        msg.attach(MIMEText(html_body, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as server:
            server.login(MAIL_SENDER, MAIL_PASSWORD)
            server.sendmail(MAIL_SENDER, to_email, msg.as_string())
        print(f"✅ Email sent → {to_email} | {subject}")
    except Exception as e:
        print(f"❌ Email failed → {to_email} | {e}")

def send_email(to_email: str, subject: str, html_body: str):
    """Fire-and-forget: send email in a background thread so it never blocks the API."""
    if not MAIL_ENABLED:
        print("⚠️  Email skipped — set MAIL_SENDER and MAIL_PASSWORD env vars")
        return
    threading.Thread(target=_send_email_worker, args=(to_email, subject, html_body), daemon=True).start()

def welcome_email_html(name: str) -> str:
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;border:1px solid #e0e0e0;border-radius:8px;overflow:hidden">
      <div style="background:#2e7d32;padding:24px;text-align:center">
        <h1 style="color:#fff;margin:0;font-size:24px">🌱 AI Crop Advisor</h1>
      </div>
      <div style="padding:32px">
        <h2 style="color:#2e7d32">Welcome, {name}!</h2>
        <p style="color:#333;font-size:15px;line-height:1.6">
          Your account has been created successfully. You can now log in and start
          getting AI-powered crop recommendations tailored to your soil and climate.
        </p>
        <div style="text-align:center;margin:32px 0">
          <a href="#" style="background:#2e7d32;color:#fff;padding:12px 28px;border-radius:6px;text-decoration:none;font-size:15px">
            Get Started →
          </a>
        </div>
        <hr style="border:none;border-top:1px solid #eee;margin:24px 0">
        <p style="color:#888;font-size:12px;text-align:center">
          AI Crop Advisor — Smart farming, better yields.
        </p>
      </div>
    </div>"""

def prediction_email_html(name: str, result: dict) -> str:
    crop        = result.get("crop", "N/A")
    season      = result.get("season", "N/A")
    profit      = result.get("profit_per_acre", "N/A")
    yield_est   = result.get("yield_est", "N/A")
    fertilizer  = result.get("fertilizer", "N/A")
    intercrop1  = result.get("intercrop_1", "N/A")
    intercrop2  = result.get("intercrop_2", "N/A")
    location    = result.get("location", "your area")
    soil_score  = result.get("soil_score", "N/A")
    market      = result.get("market_status", "N/A")
    tips        = result.get("soil_tips", [])
    schemes     = result.get("gov_schemes", [])
    top3        = result.get("top3", [])
    pred_id     = result.get("_id", "")

    tips_html = "".join(f"<li style='color:#555;margin:4px 0'>{t}</li>" for t in tips) if tips else "<li style='color:#aaa'>No issues detected</li>"
    schemes_html = ", ".join(schemes) if schemes else "N/A"
    top3_html = "".join(
        f"<tr><td style='padding:8px;border-bottom:1px solid #eee'>{c['crop']}</td>"
        f"<td style='padding:8px;border-bottom:1px solid #eee'>{c['season']}</td>"
        f"<td style='padding:8px;border-bottom:1px solid #eee'>{c['profit']}</td></tr>"
        for c in top3
    )

    return f"""
    <div style="font-family:Arial,sans-serif;max-width:640px;margin:auto;border:1px solid #e0e0e0;border-radius:8px;overflow:hidden">
      <div style="background:#388e3c;padding:24px;text-align:center">
        <h1 style="color:#fff;margin:0;font-size:22px">🌾 Your Crop Prediction is Ready!</h1>
        <p style="color:#c8e6c9;margin:6px 0 0">AI Crop Advisor — {location}</p>
      </div>
      <div style="padding:28px">
        <p style="color:#333;font-size:15px">Hi <strong>{name}</strong>,</p>
        <p style="color:#555;font-size:14px">Here's your AI-powered crop recommendation based on your soil and weather data.</p>

        <div style="background:#e8f5e9;border-left:4px solid #388e3c;border-radius:6px;padding:16px;margin:20px 0">
          <h2 style="color:#2e7d32;margin:0 0 4px">✅ Recommended Crop: {crop}</h2>
          <p style="color:#555;margin:0;font-size:14px">Season: <strong>{season}</strong> &nbsp;|&nbsp; Market: <strong>{market}</strong></p>
        </div>

        <table style="width:100%;border-collapse:collapse;margin:16px 0;font-size:14px">
          <tr style="background:#f5f5f5">
            <td style="padding:10px;font-weight:bold;color:#555;width:45%">💰 Expected Profit</td>
            <td style="padding:10px;color:#333">{profit}</td>
          </tr>
          <tr>
            <td style="padding:10px;font-weight:bold;color:#555">📦 Estimated Yield</td>
            <td style="padding:10px;color:#333">{yield_est} kg/acre</td>
          </tr>
          <tr style="background:#f5f5f5">
            <td style="padding:10px;font-weight:bold;color:#555">🧪 Fertilizer</td>
            <td style="padding:10px;color:#333">{fertilizer}</td>
          </tr>
          <tr>
            <td style="padding:10px;font-weight:bold;color:#555">🌿 Intercropping</td>
            <td style="padding:10px;color:#333">{intercrop1}, {intercrop2}</td>
          </tr>
          <tr style="background:#f5f5f5">
            <td style="padding:10px;font-weight:bold;color:#555">🧬 Soil Health Score</td>
            <td style="padding:10px;color:#333">{soil_score} / 100</td>
          </tr>
          <tr>
            <td style="padding:10px;font-weight:bold;color:#555">🏛 Govt Schemes</td>
            <td style="padding:10px;color:#333">{schemes_html}</td>
          </tr>
        </table>

        {"<h3 style='color:#e65100;font-size:14px;margin:16px 0 8px'>⚠️ Soil Tips</h3><ul style='margin:0;padding-left:20px'>" + tips_html + "</ul>" if tips else ""}

        {"<h3 style='color:#1565c0;font-size:14px;margin:20px 0 8px'>🏆 Other Top Picks</h3><table style='width:100%;border-collapse:collapse;font-size:13px'><tr style='background:#e3f2fd'><th style='padding:8px;text-align:left'>Crop</th><th style='padding:8px;text-align:left'>Season</th><th style='padding:8px;text-align:left'>Profit</th></tr>" + top3_html + "</table>" if top3 else ""}

        <div style="background:#fff8e1;border:1px solid #ffe082;border-radius:6px;padding:16px;margin:24px 0">
          <h3 style="color:#f57f17;margin:0 0 8px">📝 After Harvesting — Share Your Feedback!</h3>
          <p style="color:#555;font-size:13px;margin:0;line-height:1.6">
            Once you harvest your crop, please come back and submit your feedback on the app.
            Tell us what you actually grew, your yield, and profit — it helps improve predictions for
            all farmers in your community!
          </p>
        </div>

        <hr style="border:none;border-top:1px solid #eee;margin:20px 0">
        <p style="color:#888;font-size:12px;text-align:center">AI Crop Advisor — Smart farming, better yields.</p>
      </div>
    </div>"""

def feedback_thankyou_email_html(name: str, actual_crop: str, rating: int, total_profit: float, total_yield: float) -> str:
    stars = "⭐" * rating + "☆" * (5 - rating)
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;border:1px solid #e0e0e0;border-radius:8px;overflow:hidden">
      <div style="background:#00695c;padding:24px;text-align:center">
        <h1 style="color:#fff;margin:0;font-size:22px">🙏 Thank You for Your Feedback!</h1>
      </div>
      <div style="padding:28px">
        <p style="color:#333;font-size:15px">Hi <strong>{name}</strong>,</p>
        <p style="color:#555;font-size:14px;line-height:1.6">
          Thank you for sharing your harvest experience with us! Your feedback helps our AI model
          get smarter and benefits thousands of farmers in your community.
        </p>

        <div style="background:#e0f2f1;border-left:4px solid #00695c;border-radius:6px;padding:16px;margin:20px 0">
          <h3 style="color:#00695c;margin:0 0 12px">📋 Your Feedback Summary</h3>
          <table style="width:100%;font-size:14px;border-collapse:collapse">
            <tr>
              <td style="padding:6px 0;color:#555;font-weight:bold;width:50%">Crop Grown</td>
              <td style="padding:6px 0;color:#333">{actual_crop}</td>
            </tr>
            <tr>
              <td style="padding:6px 0;color:#555;font-weight:bold">Total Profit</td>
              <td style="padding:6px 0;color:#333">₹{total_profit:,.0f}</td>
            </tr>
            <tr>
              <td style="padding:6px 0;color:#555;font-weight:bold">Total Yield</td>
              <td style="padding:6px 0;color:#333">{total_yield:,.0f} kg</td>
            </tr>
            <tr>
              <td style="padding:6px 0;color:#555;font-weight:bold">Your Rating</td>
              <td style="padding:6px 0">{stars}</td>
            </tr>
          </table>
        </div>

        <p style="color:#555;font-size:14px;line-height:1.6">
          Your data has been recorded and will be used to retrain our AI model,
          making future crop recommendations even more accurate for farmers like you. 🌱
        </p>

        <hr style="border:none;border-top:1px solid #eee;margin:20px 0">
        <p style="color:#888;font-size:12px;text-align:center">AI Crop Advisor — Smart farming, better yields.</p>
      </div>
    </div>"""

def login_email_html(name: str, login_time: str) -> str:
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;border:1px solid #e0e0e0;border-radius:8px;overflow:hidden">
      <div style="background:#1565c0;padding:24px;text-align:center">
        <h1 style="color:#fff;margin:0;font-size:24px">🔐 Login Alert</h1>
      </div>
      <div style="padding:32px">
        <h2 style="color:#1565c0">Hi {name},</h2>
        <p style="color:#333;font-size:15px;line-height:1.6">
          A successful login was recorded on your AI Crop Advisor account.
        </p>
        <table style="width:100%;border-collapse:collapse;margin:20px 0">
          <tr>
            <td style="padding:10px;background:#f5f5f5;font-weight:bold;color:#555;width:40%">Time</td>
            <td style="padding:10px;color:#333">{login_time}</td>
          </tr>
        </table>
        <p style="color:#d32f2f;font-size:14px">
          If this wasn't you, please change your password immediately.
        </p>
        <hr style="border:none;border-top:1px solid #eee;margin:24px 0">
        <p style="color:#888;font-size:12px;text-align:center">
          AI Crop Advisor — Smart farming, better yields.
        </p>
      </div>
    </div>"""

# ══════════════════════════════════════════════════════════════════════════════
#  MONGODB
# ══════════════════════════════════════════════════════════════════════════════
from pymongo import MongoClient
from bson import ObjectId
from bson.errors import InvalidId

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
try:
    _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    _client.server_info()
    db = _client["ai_crop_advisor"]
    print("✅ MongoDB connected →", MONGO_URI)
except Exception as e:
    print(f"❌ MongoDB failed: {e}\n   → Set MONGO_URI env variable")
    db = None

def col(name):
    if db is None:
        raise RuntimeError("MongoDB not connected")
    return db[name]

# ══════════════════════════════════════════════════════════════════════════════
#  ML MODEL
# ══════════════════════════════════════════════════════════════════════════════
try:
    import joblib, numpy as np
    MODEL  = joblib.load("../model/crop_model.pkl")
    SCALER = joblib.load("../model/scaler.pkl")
    USE_ML = True
    print("✅ ML model loaded")
except Exception as e:
    USE_ML = False
    print(f"⚠️  ML fallback rule-based: {e}")

# ══════════════════════════════════════════════════════════════════════════════
#  CROP KNOWLEDGE BASE — 15 CROPS
# ══════════════════════════════════════════════════════════════════════════════
CROP_DATA = {
    "Rice":      {"intercrop":["Azolla","Fish (Aquaculture)"],"fertilizer":"Urea + DAP","base_price":2200,"price_volatility":0.04,"market_trend":"rising","season":"Kharif","sow_month":6,"harvest_month":10,"profit_per_acre":"₹40,000–₹55,000","yield_kg_per_acre":(2500,4000),"market_status":"High Demand","water_need":"high","disease_risk":{"fungal":True,"bacterial":True,"pest":False},"gov_schemes":["PM-Kisan","PMFBY","NFSM"]},
    "Maize":     {"intercrop":["Cowpea","Soybean"],"fertilizer":"NPK 14-35-14","base_price":1800,"price_volatility":0.05,"market_trend":"stable","season":"Kharif/Rabi","sow_month":6,"harvest_month":9,"profit_per_acre":"₹25,000–₹35,000","yield_kg_per_acre":(1800,3000),"market_status":"Normal","water_need":"medium","disease_risk":{"fungal":False,"bacterial":False,"pest":True},"gov_schemes":["PM-Kisan","NFSM"]},
    "Groundnut": {"intercrop":["Pearl Millet","Castor"],"fertilizer":"SSP + Gypsum","base_price":5500,"price_volatility":0.06,"market_trend":"rising","season":"Kharif","sow_month":6,"harvest_month":10,"profit_per_acre":"₹35,000–₹50,000","yield_kg_per_acre":(800,1500),"market_status":"High Demand","water_need":"medium","disease_risk":{"fungal":True,"bacterial":False,"pest":True},"gov_schemes":["PM-Kisan","PMFBY"]},
    "Wheat":     {"intercrop":["Mustard","Chickpea"],"fertilizer":"Urea + DAP","base_price":2100,"price_volatility":0.03,"market_trend":"stable","season":"Rabi","sow_month":11,"harvest_month":3,"profit_per_acre":"₹30,000–₹42,000","yield_kg_per_acre":(1500,2800),"market_status":"Normal","water_need":"medium","disease_risk":{"fungal":True,"bacterial":False,"pest":False},"gov_schemes":["PM-Kisan","NFSM","MSP Scheme"]},
    "Cotton":    {"intercrop":["Moong Bean","Groundnut"],"fertilizer":"NPK 20-20-0","base_price":6500,"price_volatility":0.07,"market_trend":"rising","season":"Kharif","sow_month":5,"harvest_month":11,"profit_per_acre":"₹45,000–₹65,000","yield_kg_per_acre":(400,700),"market_status":"High Demand","water_need":"medium","disease_risk":{"fungal":False,"bacterial":True,"pest":True},"gov_schemes":["PM-Kisan","Cotton Tech Mission","PMFBY"]},
    "Sugarcane": {"intercrop":["Onion","Garlic"],"fertilizer":"NPK + Zinc","base_price":350,"price_volatility":0.02,"market_trend":"stable","season":"Annual","sow_month":2,"harvest_month":12,"profit_per_acre":"₹50,000–₹75,000","yield_kg_per_acre":(30000,50000),"market_status":"Normal","water_need":"high","disease_risk":{"fungal":True,"bacterial":False,"pest":False},"gov_schemes":["PM-Kisan","Sugarcane Dev Scheme"]},
    "Banana":    {"intercrop":["Ginger","Turmeric"],"fertilizer":"FYM + NPK","base_price":1200,"price_volatility":0.08,"market_trend":"rising","season":"Annual","sow_month":3,"harvest_month":12,"profit_per_acre":"₹60,000–₹90,000","yield_kg_per_acre":(8000,15000),"market_status":"High Demand","water_need":"high","disease_risk":{"fungal":True,"bacterial":True,"pest":False},"gov_schemes":["PM-Kisan","NHM","PMFBY"]},
    "Chickpea":  {"intercrop":["Safflower","Linseed"],"fertilizer":"DAP + Rhizobium","base_price":5000,"price_volatility":0.05,"market_trend":"stable","season":"Rabi","sow_month":10,"harvest_month":2,"profit_per_acre":"₹28,000–₹38,000","yield_kg_per_acre":(600,1200),"market_status":"Normal","water_need":"low","disease_risk":{"fungal":False,"bacterial":False,"pest":True},"gov_schemes":["PM-Kisan","NFSM","Pulses Dev"]},
    "Tomato":    {"intercrop":["Basil","Marigold"],"fertilizer":"NPK 19-19-19","base_price":800,"price_volatility":0.15,"market_trend":"rising","season":"Rabi/Kharif","sow_month":7,"harvest_month":11,"profit_per_acre":"₹80,000–₹1,50,000","yield_kg_per_acre":(10000,20000),"market_status":"High Demand","water_need":"medium","disease_risk":{"fungal":True,"bacterial":True,"pest":True},"gov_schemes":["PM-Kisan","NHM","PMFBY"]},
    "Onion":     {"intercrop":["Carrot","Spinach"],"fertilizer":"Urea + SSP + MOP","base_price":1500,"price_volatility":0.12,"market_trend":"rising","season":"Rabi","sow_month":11,"harvest_month":4,"profit_per_acre":"₹60,000–₹1,00,000","yield_kg_per_acre":(8000,15000),"market_status":"High Demand","water_need":"medium","disease_risk":{"fungal":True,"bacterial":False,"pest":True},"gov_schemes":["PM-Kisan","NHM"]},
    "Chilli":    {"intercrop":["Coriander","Fenugreek"],"fertilizer":"NPK 17-17-17","base_price":12000,"price_volatility":0.10,"market_trend":"rising","season":"Kharif","sow_month":6,"harvest_month":12,"profit_per_acre":"₹70,000–₹1,20,000","yield_kg_per_acre":(1500,3000),"market_status":"High Demand","water_need":"medium","disease_risk":{"fungal":True,"bacterial":True,"pest":True},"gov_schemes":["PM-Kisan","NHM"]},
    "Turmeric":  {"intercrop":["Ginger","Taro"],"fertilizer":"FYM + NPK + Boron","base_price":8000,"price_volatility":0.08,"market_trend":"stable","season":"Kharif","sow_month":5,"harvest_month":1,"profit_per_acre":"₹90,000–₹1,40,000","yield_kg_per_acre":(2000,4000),"market_status":"High Demand","water_need":"medium","disease_risk":{"fungal":True,"bacterial":False,"pest":False},"gov_schemes":["PM-Kisan","NHM","Spices Board"]},
    "Soybean":   {"intercrop":["Maize","Sorghum"],"fertilizer":"DAP + Rhizobium","base_price":3800,"price_volatility":0.06,"market_trend":"rising","season":"Kharif","sow_month":6,"harvest_month":10,"profit_per_acre":"₹25,000–₹40,000","yield_kg_per_acre":(800,1500),"market_status":"Normal","water_need":"medium","disease_risk":{"fungal":True,"bacterial":False,"pest":True},"gov_schemes":["PM-Kisan","NFSM"]},
    "Mango":     {"intercrop":["Papaya","Turmeric"],"fertilizer":"FYM + NPK","base_price":3000,"price_volatility":0.09,"market_trend":"rising","season":"Annual","sow_month":7,"harvest_month":5,"profit_per_acre":"₹1,00,000–₹2,00,000","yield_kg_per_acre":(5000,12000),"market_status":"High Demand","water_need":"low","disease_risk":{"fungal":True,"bacterial":False,"pest":True},"gov_schemes":["PM-Kisan","NHM"]},
    "Coconut":   {"intercrop":["Banana","Pepper"],"fertilizer":"NPK + Boron","base_price":25,"price_volatility":0.05,"market_trend":"stable","season":"Annual","sow_month":6,"harvest_month":12,"profit_per_acre":"₹60,000–₹1,00,000","yield_kg_per_acre":(8000,15000),"market_status":"Normal","water_need":"medium","disease_risk":{"fungal":False,"bacterial":True,"pest":True},"gov_schemes":["PM-Kisan","Coconut Dev Board"]},
}
MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

# ══════════════════════════════════════════════════════════════════════════════
#  TRANSLATIONS  (6 languages × 15 crops)
# ══════════════════════════════════════════════════════════════════════════════
TRANSLATIONS = {
    "en": {"app_title":"AI Crop Advisor","step1":"Location","step2":"Soil","step3":"Results","step4":"Feedback","city_label":"City / Village","get_weather":"Get Weather","use_gps":"Use GPS","nitrogen":"Nitrogen (N)","phosphorus":"Phosphorus (P)","potassium":"Potassium (K)","temperature":"Temperature (°C)","humidity":"Humidity (%)","ph":"Soil pH","rainfall":"Rainfall (mm)","recommend":"Get Recommendation","sensor":"Auto Fill Sensor","next":"Next","back":"Back","submit_feedback":"Submit Feedback","actual_crop":"Crop you actually grew","actual_profit":"Actual Profit (₹/acre)","actual_yield":"Actual Yield (kg/acre)","feedback_note":"Your data helps improve predictions","crops":{"Rice":"Rice","Maize":"Maize","Groundnut":"Groundnut","Wheat":"Wheat","Cotton":"Cotton","Sugarcane":"Sugarcane","Banana":"Banana","Chickpea":"Chickpea","Tomato":"Tomato","Onion":"Onion","Chilli":"Chilli","Turmeric":"Turmeric","Soybean":"Soybean","Mango":"Mango","Coconut":"Coconut"}},
    "ta": {"app_title":"AI பயிர் ஆலோசகர்","step1":"இடம்","step2":"மண்","step3":"முடிவுகள்","step4":"கருத்து","city_label":"நகரம் / கிராமம்","get_weather":"வானிலை","use_gps":"GPS","nitrogen":"நைட்ரஜன் (N)","phosphorus":"பாஸ்பரஸ் (P)","potassium":"பொட்டாசியம் (K)","temperature":"வெப்பநிலை (°C)","humidity":"ஈரப்பதம் (%)","ph":"மண் pH","rainfall":"மழை (mm)","recommend":"பரிந்துரை","sensor":"சென்சார்","next":"அடுத்து","back":"பின்","submit_feedback":"சமர்ப்பி","actual_crop":"வளர்த்த பயிர்","actual_profit":"உண்மை லாபம்","actual_yield":"உண்மை விளைச்சல்","feedback_note":"உங்கள் தரவு ML க்கு உதவும்","crops":{"Rice":"நெல்","Maize":"மக்காச்சோளம்","Groundnut":"நிலக்கடலை","Wheat":"கோதுமை","Cotton":"பருத்தி","Sugarcane":"கரும்பு","Banana":"வாழை","Chickpea":"கடலை","Tomato":"தக்காளி","Onion":"வெங்காயம்","Chilli":"மிளகாய்","Turmeric":"மஞ்சள்","Soybean":"சோயாபீன்","Mango":"மாம்பழம்","Coconut":"தேங்காய்"}},
    "te": {"app_title":"AI పంట సలహాదారు","step1":"స్థానం","step2":"నేల","step3":"ఫలితాలు","step4":"అభిప్రాయం","city_label":"నగరం / గ్రామం","get_weather":"వాతావరణం","use_gps":"GPS","nitrogen":"నైట్రోజన్ (N)","phosphorus":"ఫాస్పరస్ (P)","potassium":"పొటాషియం (K)","temperature":"ఉష్ణోగ్రత (°C)","humidity":"తేమ (%)","ph":"నేల pH","rainfall":"వర్షపాతం (mm)","recommend":"సిఫారసు","sensor":"సెన్సార్","next":"తదుపరి","back":"వెనుకకు","submit_feedback":"సమర్పించు","actual_crop":"పండించిన పంట","actual_profit":"వాస్తవ లాభం","actual_yield":"వాస్తవ దిగుబడి","feedback_note":"మీ డేటా ML కి సహాయం","crops":{"Rice":"వరి","Maize":"మొక్కజొన్న","Groundnut":"వేరుశెనగ","Wheat":"గోధుమ","Cotton":"పత్తి","Sugarcane":"చెరకు","Banana":"అరటి","Chickpea":"శనగ","Tomato":"టమాటా","Onion":"ఉల్లిపాయ","Chilli":"మిరప","Turmeric":"పసుపు","Soybean":"సోయాబీన్","Mango":"మామిడి","Coconut":"కొబ్బరి"}},
    "kn": {"app_title":"AI ಬೆಳೆ ಸಲಹೆಗಾರ","step1":"ಸ್ಥಳ","step2":"ಮಣ್ಣು","step3":"ಫಲಿತಾಂಶ","step4":"ಪ್ರತಿಕ್ರಿಯೆ","city_label":"ನಗರ / ಗ್ರಾಮ","get_weather":"ಹವಾಮಾನ","use_gps":"GPS","nitrogen":"ಸಾರಜನಕ (N)","phosphorus":"ರಂಜಕ (P)","potassium":"ಪೊಟ್ಯಾಷಿಯಂ (K)","temperature":"ತಾಪಮಾನ (°C)","humidity":"ತೇವಾಂಶ (%)","ph":"ಮಣ್ಣು pH","rainfall":"ಮಳೆ (mm)","recommend":"ಶಿಫಾರಸು","sensor":"ಸೆನ್ಸಾರ್","next":"ಮುಂದೆ","back":"ಹಿಂದೆ","submit_feedback":"ಸಲ್ಲಿಸಿ","actual_crop":"ಬೆಳೆದ ಬೆಳೆ","actual_profit":"ನಿಜ ಲಾಭ","actual_yield":"ನಿಜ ಇಳುವರಿ","feedback_note":"ನಿಮ್ಮ ಡೇಟಾ ML ಗೆ ಸಹಾಯ","crops":{"Rice":"ಭತ್ತ","Maize":"ಮೆಕ್ಕೆ ಜೋಳ","Groundnut":"ಶೇಂಗಾ","Wheat":"ಗೋಧಿ","Cotton":"ಹತ್ತಿ","Sugarcane":"ಕಬ್ಬು","Banana":"ಬಾಳೆ","Chickpea":"ಕಡಲೆ","Tomato":"ಟೊಮ್ಯಾಟೊ","Onion":"ಈರುಳ್ಳಿ","Chilli":"ಮೆಣಸಿನಕಾಯಿ","Turmeric":"ಅರಿಶಿನ","Soybean":"ಸೋಯಾಬೀನ್","Mango":"ಮಾವು","Coconut":"ತೆಂಗು"}},
    "ml": {"app_title":"AI വിള ഉപദേഷ്ടാവ്","step1":"സ്ഥലം","step2":"മണ്ണ്","step3":"ഫലങ്ങൾ","step4":"പ്രതികരണം","city_label":"നഗരം / ഗ്രാമം","get_weather":"കാലാവസ്ഥ","use_gps":"GPS","nitrogen":"നൈട്രജൻ (N)","phosphorus":"ഫോസ്ഫറസ് (P)","potassium":"പൊട്ടാസ്യം (K)","temperature":"താപനില (°C)","humidity":"ഈർപ്പം (%)","ph":"മണ്ണ് pH","rainfall":"മഴ (mm)","recommend":"ശുപാർശ","sensor":"സെൻസർ","next":"അടുത്തത്","back":"പിന്നോട്ട്","submit_feedback":"സമർപ്പിക്കുക","actual_crop":"വളർത്തിയ വിള","actual_profit":"യഥാർത്ഥ ലാഭം","actual_yield":"യഥാർത്ഥ വിളവ്","feedback_note":"നിങ്ങളുടെ ഡേറ്റ ML ഉം","crops":{"Rice":"നെല്ല്","Maize":"ചോളം","Groundnut":"നിലക്കടല","Wheat":"ഗോതമ്പ്","Cotton":"പരുത്തി","Sugarcane":"കരിമ്പ്","Banana":"വാഴ","Chickpea":"കടല","Tomato":"തക്കാളി","Onion":"ഉള്ളി","Chilli":"മുളക്","Turmeric":"മഞ്ഞൾ","Soybean":"സോയാബീൻ","Mango":"മാങ്ങ","Coconut":"തേങ്ങ"}},
    "hi": {"app_title":"AI फसल सलाहकार","step1":"स्थान","step2":"मिट्टी","step3":"परिणाम","step4":"प्रतिक्रिया","city_label":"शहर / गाँव","get_weather":"मौसम","use_gps":"GPS","nitrogen":"नाइट्रोजन (N)","phosphorus":"फास्फोरस (P)","potassium":"पोटेशियम (K)","temperature":"तापमान (°C)","humidity":"आर्द्रता (%)","ph":"मिट्टी pH","rainfall":"वर्षा (mm)","recommend":"सिफारिश","sensor":"सेंसर","next":"अगला","back":"वापस","submit_feedback":"दर्ज करें","actual_crop":"आपकी फसल","actual_profit":"वास्तविक लाभ","actual_yield":"वास्तविक उपज","feedback_note":"डेटा ML में सहायक","crops":{"Rice":"चावल","Maize":"मक्का","Groundnut":"मूंगफली","Wheat":"गेहूँ","Cotton":"कपास","Sugarcane":"गन्ना","Banana":"केला","Chickpea":"चना","Tomato":"टमाटर","Onion":"प्याज","Chilli":"मिर्च","Turmeric":"हल्दी","Soybean":"सोयाबीन","Mango":"आम","Coconut":"नारियल"}},
}

# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def rule_based_predict(N, P, K, temperature, humidity, ph, rainfall):
    if N > 80 and humidity > 70 and rainfall > 150:     return "Rice"
    if temperature > 25 and humidity > 75 and K > 50:   return "Tomato"
    if N < 50 and ph > 6.5 and temperature > 20:        return "Onion"
    if temperature > 28 and humidity > 60 and ph > 6:   return "Chilli"
    if K > 70 and temperature > 25 and rainfall < 120:  return "Turmeric"
    if N > 60 and temperature > 25 and rainfall < 120:  return "Groundnut"
    if K > 80 and ph > 6.5 and temperature > 27:        return "Cotton"
    if temperature < 22 and rainfall > 80 and ph < 7:   return "Wheat"
    if ph > 7 and N < 50 and rainfall < 100:            return "Chickpea"
    if humidity > 75 and temperature > 28 and K > 60:   return "Banana"
    if N > 100 and K > 100 and rainfall > 200:          return "Sugarcane"
    if N > 40 and ph > 6 and temperature > 25:          return "Soybean"
    if temperature > 30 and rainfall < 80 and ph > 6.5: return "Mango"
    if humidity > 70 and K > 50 and temperature > 25:   return "Coconut"
    return "Maize"

def ml_predict(N, P, K, temperature, humidity, ph, rainfall):
    try:
        features = np.array([[N, P, K, temperature, humidity, ph, rainfall]])
        return MODEL.predict(SCALER.transform(features))[0]
    except:
        return rule_based_predict(N, P, K, temperature, humidity, ph, rainfall)

def normalize_crop(c):
    if c in CROP_DATA: return c
    cl = str(c).lower()
    return next((k for k in CROP_DATA if k.lower() == cl or k.lower() in cl), "Maize")

def soil_health_score(N, P, K, ph):
    s = min(100,N/140*100)*0.30 + min(100,P/145*100)*0.25 + min(100,K/205*100)*0.25 + max(0,100-abs(ph-6.5)*25)*0.20
    return round(s)

def irrigation_schedule(wn, rain, temp):
    if wn=="high":
        if rain<75 and temp>30: return {"frequency":"Every day","amount_per_session":"50–60 mm"}
        if rain<75:             return {"frequency":"Every 2 days","amount_per_session":"40–50 mm"}
        if rain<150:            return {"frequency":"Every 3 days","amount_per_session":"30–40 mm"}
        return {"frequency":"Once a week","amount_per_session":"20–25 mm"}
    elif wn=="medium":
        if rain<75 and temp>30: return {"frequency":"Every 2 days","amount_per_session":"35–45 mm"}
        if rain<75:             return {"frequency":"Every 3 days","amount_per_session":"30–40 mm"}
        if rain<150:            return {"frequency":"Twice a week","amount_per_session":"25–30 mm"}
        return {"frequency":"Once in 10 days","amount_per_session":"15–20 mm"}
    else:
        if rain<75: return {"frequency":"Once a week","amount_per_session":"20–25 mm"}
        return {"frequency":"Rainfall sufficient","amount_per_session":"Monitor only"}

def disease_risk(hum, temp, info):
    dr = info.get("disease_risk",{})
    risks = []
    if dr.get("fungal") and hum>75:  risks.append({"type":"Fungal Disease","level":"High" if hum>85 else "Medium","advice":"Apply Mancozeb or Copper Oxychloride"})
    if dr.get("bacterial") and temp>30: risks.append({"type":"Bacterial Blight","level":"Medium","advice":"Use Streptocycline spray"})
    if dr.get("pest") and temp>28:   risks.append({"type":"Pest Infestation","level":"High" if temp>33 else "Medium","advice":"Use Neem oil or recommended pesticide"})
    if not risks: risks.append({"type":"No Risk Detected","level":"Low","advice":"Maintain good field hygiene"})
    return risks

def yield_est(info, N, P, K, rain):
    lo, hi = info["yield_kg_per_acre"]
    f = min(1.0,(N/100*0.4+P/80*0.3+K/100*0.3)) * min(1.0,rain/150)
    return round(lo + (hi-lo)*f)

def crop_calendar(info):
    s, h = info["sow_month"]-1, info["harvest_month"]-1
    if h<s: h+=12
    return {"sow":MONTHS[s],"grow":MONTHS[(s+h)//2%12],"harvest":MONTHS[h%12],"duration_months":(h-s)%12+1}

def price_history(base, vol, trend, months=12):
    tf = {"rising":1.012,"stable":1.002,"falling":0.990}.get(trend,1.002)
    p, hist = base, []
    for _ in range(months):
        p = p*tf + random.gauss(0, base*vol)
        hist.append(round(max(p, base*0.5), 2))
    return hist

def haversine(la1,lo1,la2,lo2):
    R=6371; dlat=math.radians(la2-la1); dlon=math.radians(lo2-lo1)
    a=math.sin(dlat/2)**2+math.cos(math.radians(la1))*math.cos(math.radians(la2))*math.sin(dlon/2)**2
    return round(R*2*math.asin(math.sqrt(a)),1)

def geocode(city):
    import urllib.request, urllib.parse
    try:
        url="https://nominatim.openstreetmap.org/search?"+urllib.parse.urlencode({"q":city+", India","format":"json","limit":1})
        req=urllib.request.Request(url,headers={"User-Agent":"AICropAdvisor/1.0"})
        with urllib.request.urlopen(req,timeout=6) as r: d=json.loads(r.read())
        if d: return float(d[0]["lat"]),float(d[0]["lon"])
    except: pass
    return None,None

def fallback_mandis(city, lat, lon):
    rng = random.Random(int(hashlib.md5((city or "farm").encode()).hexdigest()[:8],16))
    names=[f"{city} Main Agricultural Market",f"{city} Wholesale Mandi","District Farmers Market","Regional Agri Centre","Uzhavar Santhai"]
    used=[]; res=[]
    for i in range(5):
        a=rng.uniform(0,360)
        while any(abs(a-u)<30 for u in used): a=rng.uniform(0,360)
        used.append(a); d=rng.uniform(3,35)
        r=math.radians(a)
        res.append({"name":names[i],"lat":round(lat+d/111*math.cos(r),5),"lng":round(lon+d/(111*math.cos(math.radians(lat)))*math.sin(r),5),"distance_km":round(d,1)})
    return sorted(res,key=lambda x:x["distance_km"])

def top3(N,P,K,temp,hum,ph,rain):
    import datetime as dt
    m=dt.datetime.now().month
    scores={}
    for crop,info in CROP_DATA.items():
        s=0
        if info["water_need"]=="high" and hum>70: s+=20
        if info["water_need"]=="low" and hum<55:  s+=20
        if info["water_need"]=="medium": s+=10
        if "Kharif" in info["season"] and 5<=m<=9: s+=15
        if "Rabi" in info["season"] and (m>=10 or m<=3): s+=15
        s+=random.randint(0,10); scores[crop]=s
    return sorted(scores,key=scores.get,reverse=True)[:3]

def oid(s):
    try: return ObjectId(s)
    except: return None

# ══════════════════════════════════════════════════════════════════════════════
#  AUTH HELPERS  (JWT + bcrypt)
# ══════════════════════════════════════════════════════════════════════════════
import jwt as pyjwt
import bcrypt

JWT_SECRET = os.environ.get("JWT_SECRET","jwt_secret_aicropadvisor_2026")
JWT_EXP_HOURS = 24

def hash_pw(pw): return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
def check_pw(pw, hashed): return bcrypt.checkpw(pw.encode(), hashed.encode())

def make_token(user_id, role):
    payload = {"sub": str(user_id), "role": role,
               "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_EXP_HOURS)}
    return pyjwt.encode(payload, JWT_SECRET, algorithm="HS256")

def decode_token(token):
    try: return pyjwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except: return None

def get_token_from_request():
    auth = request.headers.get("Authorization","")
    if auth.startswith("Bearer "): return auth[7:]
    return request.cookies.get("token") or request.headers.get("X-Token")

def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = get_token_from_request()
        payload = decode_token(token)
        if not payload: return jsonify({"error":"Unauthorized — please login"}), 401
        request.user_id = payload["sub"]
        request.user_role = payload["role"]
        return f(*args, **kwargs)
    return wrapper

def require_admin(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = get_token_from_request()
        payload = decode_token(token)
        if not payload: return jsonify({"error":"Unauthorized"}), 401
        if payload.get("role") != "admin": return jsonify({"error":"Admin access required"}), 403
        request.user_id = payload["sub"]
        request.user_role = "admin"
        return f(*args, **kwargs)
    return wrapper

def validate_email(email):
    import re
    return bool(re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email))

# ══════════════════════════════════════════════════════════════════════════════
#  PAGE ROUTES
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/")
def page_login():
    return render_template("login.html", T=TRANSLATIONS["en"])

@app.route("/signup")
def page_signup():
    return render_template("signup.html", T=TRANSLATIONS["en"])

@app.route("/app")
def page1():
    return render_template("page1.html", translations=TRANSLATIONS)

@app.route("/soil")
def page2():
    return render_template("page2.html", translations=TRANSLATIONS)

@app.route("/results")
def page3():
    return render_template("page3.html", translations=TRANSLATIONS)

@app.route("/feedback")
def page4():
    return render_template("page4.html", translations=TRANSLATIONS, crops=list(CROP_DATA.keys()))

@app.route("/history")
def page_history():
    return render_template("history.html", translations=TRANSLATIONS)

@app.route("/admin")
def page_admin():
    return render_template("admin.html", T=TRANSLATIONS["en"])

# ══════════════════════════════════════════════════════════════════════════════
#  AUTH API
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/auth/signup", methods=["POST"])
def api_signup():
    d = request.get_json()
    name  = (d.get("name") or "").strip()
    email = (d.get("email") or "").strip().lower()
    pw    = d.get("password","")
    role  = "user"  # users always get "user" role on signup

    if not name:              return jsonify({"error":"Name is required"}), 400
    if not validate_email(email): return jsonify({"error":"Invalid email format"}), 400
    if len(pw) < 6:           return jsonify({"error":"Password must be at least 6 characters"}), 400

    users = col("users")
    if users.find_one({"email": email}):
        return jsonify({"error":"Email already registered"}), 409

    user = {"name":name,"email":email,"password":hash_pw(pw),"role":role,
            "createdAt":datetime.datetime.utcnow().isoformat()}
    result = users.insert_one(user)
    token  = make_token(result.inserted_id, role)

    # Send welcome email in background
    send_email(
        to_email=email,
        subject="🌱 Welcome to AI Crop Advisor!",
        html_body=welcome_email_html(name)
    )

    return jsonify({"token":token,"user":{"id":str(result.inserted_id),"name":name,"email":email,"role":role}}), 201

@app.route("/api/auth/login", methods=["POST"])
def api_login():
    d = request.get_json()
    email = (d.get("email") or "").strip().lower()
    pw    = d.get("password","")
    if not email or not pw:
        return jsonify({"error":"Email and password required"}), 400
    user = col("users").find_one({"email": email})
    if not user or not check_pw(pw, user["password"]):
        return jsonify({"error":"Invalid email or password"}), 401
    token = make_token(user["_id"], user["role"])

    # Send login alert email in background
    login_time = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    send_email(
        to_email=user["email"],
        subject="🔐 New Login to Your AI Crop Advisor Account",
        html_body=login_email_html(user["name"], login_time)
    )

    return jsonify({"token":token,"user":{"id":str(user["_id"]),"name":user["name"],"email":user["email"],"role":user["role"]}})

@app.route("/api/auth/me")
@require_auth
def api_me():
    user = col("users").find_one({"_id": oid(request.user_id)}, {"password":0})
    if not user: return jsonify({"error":"User not found"}), 404
    user["_id"] = str(user["_id"])
    return jsonify(user)

# ══════════════════════════════════════════════════════════════════════════════
#  WEATHER / SENSOR
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/weather")
def api_weather():
    city = request.args.get("city","")
    lat  = request.args.get("lat")
    lon  = request.args.get("lon")
    api_key = os.environ.get("OPENWEATHER_API_KEY","")
    if api_key:
        try:
            import urllib.request
            url = (f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
                   if lat and lon else
                   f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric")
            with urllib.request.urlopen(url, timeout=5) as r: d=json.loads(r.read())
            return jsonify({"temperature":round(d["main"]["temp"]),"humidity":d["main"]["humidity"],"city":d.get("name",city),"lat":d["coord"]["lat"],"lon":d["coord"]["lon"],"source":"live"})
        except: pass
    try:
        import urllib.request
        if not lat or not lon:
            glat,glon=geocode(city); lat,lon=glat or 11.0168,glon or 76.9558
        url=f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m&timezone=auto"
        with urllib.request.urlopen(url,timeout=6) as r: d=json.loads(r.read())
        cur=d.get("current",{})
        return jsonify({"temperature":round(cur.get("temperature_2m",28)),"humidity":cur.get("relative_humidity_2m",70),"city":city,"lat":float(lat),"lon":float(lon),"source":"open-meteo"})
    except: pass
    glat,glon=geocode(city) if city else (None,None)
    return jsonify({"temperature":random.randint(25,35),"humidity":random.randint(60,85),"city":city,"lat":glat,"lon":glon,"source":"simulated"})

@app.route("/api/sensor")
def api_sensor():
    return jsonify({"N":random.randint(40,120),"P":random.randint(20,80),"K":random.randint(30,120),"ph":round(random.uniform(5.5,7.5),1),"rainfall":random.randint(50,250)})

# ══════════════════════════════════════════════════════════════════════════════
#  PREDICTIONS
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/predictions", methods=["POST"])
@require_auth
def api_predict():
    d = request.get_json()
    try:
        N=float(d["N"]); P=float(d["P"]); K=float(d["K"])
        temp=float(d["temperature"]); hum=float(d["humidity"])
        ph=float(d["ph"]); rain=float(d["rainfall"])
    except: return jsonify({"error":"Invalid input"}), 400

    city = d.get("city","your area")
    lat  = d.get("lat"); lon = d.get("lon")
    if lat is None or lon is None:
        glat,glon=geocode(city)
        lat=glat; lon=glon
    try: farm_lat=float(lat) if lat else 11.0168; farm_lon=float(lon) if lon else 76.9558
    except: farm_lat,farm_lon=11.0168,76.9558

    crop_raw = ml_predict(N,P,K,temp,hum,ph,rain) if USE_ML else rule_based_predict(N,P,K,temp,hum,ph,rain)
    crop  = normalize_crop(crop_raw)
    info  = CROP_DATA[crop]
    score = soil_health_score(N,P,K,ph)
    hist  = price_history(info["base_price"],info["price_volatility"],info["market_trend"])
    last3 = sum(hist[-3:])/3
    tbump = {"rising":1.04,"falling":0.96,"stable":1.01}[info["market_trend"]]
    t3k   = top3(N,P,K,temp,hum,ph,rain)
    t3    = [{"crop":c,"season":CROP_DATA[c]["season"],"profit":CROP_DATA[c]["profit_per_acre"],"water":CROP_DATA[c]["water_need"],"yield_est":yield_est(CROP_DATA[c],N,P,K,rain)} for c in t3k if c in CROP_DATA]
    tips  = []
    if N<40: tips.append("Low Nitrogen — apply Urea or green manure")
    if P<25: tips.append("Low Phosphorus — apply DAP or SSP")
    if K<25: tips.append("Low Potassium — apply MOP")
    if ph<5.5: tips.append("Acidic soil — apply lime")
    if ph>8:   tips.append("Alkaline soil — apply gypsum")

    result = {
        "userId":       request.user_id,
        "crop":         crop,
        "model_used":   "ML" if USE_ML else "Rules",
        "intercrop_1":  info["intercrop"][0],
        "intercrop_2":  info["intercrop"][1],
        "fertilizer":   info["fertilizer"],
        "season":       info["season"],
        "market_status":info["market_status"],
        "market_trend": info["market_trend"],
        "profit_per_acre": info["profit_per_acre"],
        "price_history":hist,
        "current_price":hist[-1],
        "next_month_price": round(last3*tbump,2),
        "soil_score":   score,
        "soil_tips":    tips,
        "disease_risks":disease_risk(hum,temp,info),
        "irrigation":   irrigation_schedule(info["water_need"],rain,temp),
        "yield_est":    yield_est(info,N,P,K,rain),
        "calendar":     crop_calendar(info),
        "top3":         t3,
        "gov_schemes":  info["gov_schemes"],
        "nearby_mandis":fallback_mandis(city,farm_lat,farm_lon),
        "farm_lat":     farm_lat,
        "farm_lon":     farm_lon,
        "location":     city,
        "soilData":     {"N":N,"P":P,"K":K,"ph":ph},
        "weatherData":  {"temperature":temp,"humidity":hum,"rainfall":rain},
        "createdAt":    datetime.datetime.utcnow().isoformat(),
    }
    inserted = col("predictions").insert_one(result.copy())
    result["_id"] = str(inserted.inserted_id)
    result["userId"] = str(result["userId"])

    # Send prediction email in background
    user = col("users").find_one({"_id": oid(request.user_id)}, {"name": 1, "email": 1})
    if user:
        send_email(
            to_email=user["email"],
            subject=f"🌾 Your Crop Recommendation: {crop} — AI Crop Advisor",
            html_body=prediction_email_html(user["name"], result)
        )

    return jsonify(result), 201

@app.route("/api/predictions/user")
@require_auth
def api_user_predictions():
    preds = list(col("predictions").find({"userId":request.user_id},{"_id":1,"crop":1,"soil_score":1,"yield_est":1,"profit_per_acre":1,"createdAt":1,"location":1,"model_used":1}).sort("createdAt",-1).limit(20))
    for p in preds: p["_id"]=str(p["_id"])
    return jsonify(preds)

@app.route("/api/predictions/<pred_id>")
@require_auth
def api_prediction_detail(pred_id):
    pred = col("predictions").find_one({"_id":oid(pred_id)})
    if not pred: return jsonify({"error":"Not found"}),404
    if pred.get("userId") != request.user_id and request.user_role != "admin":
        return jsonify({"error":"Forbidden"}),403
    pred["_id"]=str(pred["_id"])
    return jsonify(pred)

# ══════════════════════════════════════════════════════════════════════════════
#  FEEDBACK
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/feedback", methods=["POST"])
@require_auth
def api_feedback():
    d = request.get_json()
    no_acres  = float(d.get("no_of_acres") or 1)
    ppa       = float(d.get("actual_profit_per_acre") or 0)
    ypa       = float(d.get("actual_yield_per_acre") or 0)
    record = {
        "userId":              request.user_id,
        "predictionId":        d.get("predictionId"),
        "actual_crop":         d.get("actual_crop"),
        "no_of_acres":         no_acres,
        "actual_profit_per_acre": ppa,
        "actual_total_profit": round(ppa*no_acres,2),
        "actual_yield_per_acre":  ypa,
        "actual_total_yield":  round(ypa*no_acres,2),
        "rating":              int(d.get("rating") or 0),
        "comments":            d.get("comments",""),
        "createdAt":           datetime.datetime.utcnow().isoformat(),
    }
    col("feedback").insert_one(record)
    count = col("feedback").count_documents({})

    # Send thank-you email in background
    user = col("users").find_one({"_id": oid(request.user_id)}, {"name": 1, "email": 1})
    if user:
        send_email(
            to_email=user["email"],
            subject="🙏 Thank You for Your Feedback — AI Crop Advisor",
            html_body=feedback_thankyou_email_html(
                name=user["name"],
                actual_crop=record.get("actual_crop", "N/A"),
                rating=record.get("rating", 0),
                total_profit=record.get("actual_total_profit", 0),
                total_yield=record.get("actual_total_yield", 0)
            )
        )

    return jsonify({"status":"ok","community_count":count,"total_profit":record["actual_total_profit"],"total_yield":record["actual_total_yield"]})

@app.route("/api/feedback/<pred_id>")
@require_auth
def api_feedback_for_pred(pred_id):
    fb = list(col("feedback").find({"predictionId":pred_id},{"_id":0,"userId":0}))
    return jsonify(fb)

# ══════════════════════════════════════════════════════════════════════════════
#  ADMIN
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/admin/users")
@require_admin
def api_admin_users():
    users = list(col("users").find({},{"password":0}).sort("createdAt",-1))
    for u in users: u["_id"]=str(u["_id"])
    return jsonify(users)

@app.route("/api/admin/predictions")
@require_admin
def api_admin_predictions():
    preds = list(col("predictions").find({},{"_id":1,"userId":1,"crop":1,"soil_score":1,"location":1,"createdAt":1,"model_used":1}).sort("createdAt",-1).limit(100))
    for p in preds: p["_id"]=str(p["_id"])
    return jsonify(preds)

@app.route("/api/admin/feedback")
@require_admin
def api_admin_feedback():
    fbs = list(col("feedback").find({},{"_id":1,"userId":1,"predictionId":1,"actual_crop":1,"rating":1,"createdAt":1}).sort("createdAt",-1).limit(100))
    for f in fbs: f["_id"]=str(f["_id"])
    return jsonify(fbs)

@app.route("/api/admin/stats")
@require_admin
def api_admin_stats():
    return jsonify({
        "users":       col("users").count_documents({}),
        "predictions": col("predictions").count_documents({}),
        "feedback":    col("feedback").count_documents({}),
    })

@app.route("/api/admin/export-training-data")
@require_admin
def api_export_training():
    import io, csv
    rows = list(col("feedback").find({"actual_crop":{"$ne":None}},{"_id":0,"userId":0,"predictionId":0}))
    output = io.StringIO()
    if rows:
        w=csv.DictWriter(output, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
    return app.response_class(output.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition":"attachment; filename=training_data.csv"})

@app.route("/api/community-count")
def api_community_count():
    return jsonify({"count": col("feedback").count_documents({})})

@app.route("/api/translations")
def api_translations():
    return jsonify(TRANSLATIONS)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
