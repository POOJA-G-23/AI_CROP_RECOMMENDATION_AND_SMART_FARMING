# 🌱 AI Crop Recommendation & Smart Farming System

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3+-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-4.6+-47A248?style=for-the-badge&logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![Scikit--Learn](https://img.shields.io/badge/scikit_learn-1.3+-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](LICENSE)

An intelligent agricultural decision-support web application that empowers farmers and agricultural consultants to make data-driven crop selection decisions. The system analyzes local soil chemistry (Nitrogen, Phosphorus, Potassium, pH) and environmental weather metrics (Temperature, Humidity, Rainfall) using an ensemble Machine Learning model to deliver high-accuracy crop recommendations.

---

## 🚀 Key Features

- **🌾 AI-Powered Crop Recommendation**: Multi-crop prediction using a trained Random Forest Classifier considering N-P-K, pH, temperature, humidity, and rainfall.
- **🔐 Secure Authentication & Authorization**:
  - JWT (JSON Web Tokens) with 24-hour expiration.
  - Passwords hashed with `bcrypt` (never stored plain).
  - Role-based access control (`user` vs `admin`).
- **🗺️ Interactive Flow & Dashboards**:
  - **Step 1:** Location & Weather acquisition.
  - **Step 2:** Soil parameter input & validation.
  - **Step 3:** AI prediction results with confidence metrics & visualization.
  - **Step 4:** Farmer feedback loop for continuous model improvement.
- **📊 Admin Portal**:
  - Real-time statistics on users, predictions, and feedback.
  - Export training data as CSV.
  - Retrain ML model dynamically using community feedback.
- **📜 Prediction History**: Farmers can review their past recommendations anytime.

---

## 📁 Repository Structure

```text
ai-crop-recommendation/
├── backend/
│   ├── app.py                     # Main Flask web server & REST APIs
│   ├── templates/                 # Jinja2 HTML templates
│   │   ├── login.html             # User login
│   │   ├── signup.html            # User registration
│   │   ├── page1.html             # Step 1: Location & Weather
│   │   ├── page2.html             # Step 2: Soil Parameters
│   │   ├── page3.html             # Step 3: AI Results & Visualizations
│   │   ├── page4.html             # Step 4: Farmer Feedback
│   │   ├── history.html           # Farmer prediction history
│   │   └── admin.html             # Admin monitoring dashboard
│   ├── static/
│   │   ├── css/
│   │   │   ├── style.css          # Main modern UI styles
│   │   │   └── auth.css           # Authentication & dashboard styling
│   │   └── js/
│   │       └── auth.js            # JWT client helper
│   ├── .env.example               # Template for environment variables
├── model/
│   ├── crop_model.pkl             # Trained Random Forest model
│   └── scaler.pkl                 # Feature standard scaler
├── dataset/
│   └── crop_dataset.csv           # Crop dataset for training
├── train_model.py                 # Initial training script (15 crops)
├── retrain_model.py               # Retraining pipeline with community data
├── create_admin.py                # Admin provisioning utility
├── requirements.txt               # Python package dependencies
└── README.md                      # Project documentation
```

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Backend** | Python 3, Flask, Flask-CORS, PyJWT, bcrypt |
| **Database** | MongoDB (Community / Atlas) via PyMongo |
| **Machine Learning** | Scikit-learn (RandomForestClassifier, StandardScaler), Pandas, NumPy, Joblib |
| **Frontend** | Semantic HTML5, Modern Vanilla CSS3, JavaScript (ES6+), Leaflet/Charts |

---

## ⚙️ Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/POOJA-G-23/AI_CROP_RECOMMENDATION_AND_SMART_FARMING.git
cd AI_CROP_RECOMMENDATION_AND_SMART_FARMING
```

### 2. Set Up a Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `backend/.env.example` to `backend/.env` and update the parameters:
```bash
# In backend/.env
MAIL_SENDER=your_email@gmail.com
MAIL_PASSWORD=your_gmail_app_password
MONGO_URI=mongodb://localhost:27017/
JWT_SECRET=your_super_secret_jwt_key
```

### 5. Setup MongoDB
- **Local MongoDB**: Ensure MongoDB service is running on `mongodb://localhost:27017/`
- **MongoDB Atlas**: Update `MONGO_URI` with your connection string.

### 6. Train the Model & Create Admin Account
```bash
# Train the initial ML model (optional if crop_model.pkl is already present)
python train_model.py

# Create initial admin account
python create_admin.py
```

### 7. Run the Application
```bash
cd backend
python app.py
```
Open your browser and navigate to:
- **Login / Landing:** `http://localhost:5000`
- **Sign Up:** `http://localhost:5000/signup`
- **Admin Dashboard:** `http://localhost:5000/admin`

---

## 📡 API Reference

### 🔐 Authentication
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/signup` | Register a new farmer account |
| `POST` | `/api/auth/login` | Authenticate user and return JWT |
| `GET` | `/api/auth/me` | Fetch currently logged-in user profile |

### 🌾 Predictions & Feedback
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/predictions` | Submit soil & weather parameters to get crop prediction |
| `GET` | `/api/predictions/user` | Fetch prediction history for current user |
| `GET` | `/api/predictions/<id>` | Fetch specific prediction details |
| `POST` | `/api/feedback` | Submit farmer feedback on recommendation |

### 🛡️ Admin Endpoints
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/admin/users` | List all registered users |
| `GET` | `/api/admin/predictions` | List all historical predictions |
| `GET` | `/api/admin/feedback` | List all user feedback |
| `GET` | `/api/admin/stats` | System statistics overview |
| `GET` | `/api/admin/export-training-data` | Export verified community feedback as CSV |

---

## 🔒 Security Practices

- **Zero Plaintext Passwords**: Password hashing via `bcrypt`.
- **Stateless Tokens**: Expiration and signature validation via `PyJWT`.
- **Role Isolation**: Sensitive actions and administrative views protected by `@require_admin`.
- **Data Privacy**: Users can only query and view their own prediction records.

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the issues page or submit a Pull Request.

---

## 📄 License

This project is licensed under the MIT License.
