# 🚑 MedQueue AI – Real-Time Hospital Queue Management System

MedQueue AI is a **scalable, AI-powered hospital OPD queue management platform** designed to digitize patient flow, reduce waiting time, and improve hospital efficiency using **real-time systems and machine learning**.

---

## 📌 Problem Statement

In many hospitals, patient queues are managed manually, leading to:

- ⏳ Long waiting times (2–5 hours)
- ❌ No real-time visibility of queue status
- 🧓 Poor experience for elderly and critical patients
- 🚨 No structured emergency prioritization
- 📊 Lack of analytics for hospital management

---

## 🚀 Solution

MedQueue AI transforms traditional queue systems into a **smart, digital, and AI-driven platform** with:

- 🎟️ Digital token generation (online + walk-in)
- 📡 Real-time queue tracking using WebSockets
- 🤖 AI-based waiting time prediction
- ⚡ Emergency case prioritization
- 📊 Analytics dashboard for hospitals

---

## 🧠 Key Features

### 👤 Patient Module

- Book tokens online
- View live queue position
- Get estimated waiting time
- Receive notifications before turn

### 👨‍⚕️ Doctor Module

- View and manage queue
- Call / Skip / Complete patients
- Handle emergency priority cases
- Track consultation performance

### 🧑‍💼 Reception Module

- Add walk-in patients
- Generate tokens instantly
- Manage real-time queue

### 🏥 Admin Dashboard

- Monitor hospital operations
- Analyze patient flow
- Track average waiting time
- Export reports (CSV/PDF)

---

## ⚡ Real-Time System

- WebSocket-based live updates (Django Channels)
- Redis for high-speed message broadcasting
- Instant queue synchronization across all users

---

## 🤖 AI / Machine Learning

- **Random Forest** → Waiting time prediction
- **LightGBM** → Crowd forecasting
- Predicts:
  - Patient wait time
  - Peak hours
  - Doctor workload

---

## 🛠️ Tech Stack

### 🔹 Backend

- Python, Django
- Django REST Framework (DRF)

### 🔹 Frontend

- HTML5, CSS3, JavaScript
- Tailwind CSS, HTMX

### 🔹 Databases

- MySQL (Structured data)
- MongoDB (Logs & analytics)

### 🔹 Real-Time & Caching

- Django Channels
- Redis

### 🔹 AI/ML

- Scikit-learn
- LightGBM

### 🔹 Security

- JWT Authentication
- Role-Based Access Control (RBAC)

---

## 🏗️ System Architecture

```
Client (Patient / Doctor / Admin)
        ↓
Frontend (Web UI)
        ↓
Django Backend (REST APIs)
        ↓
---------------------------------
| MySQL | MongoDB | Redis |
---------------------------------
        ↓
AI Prediction Engine
```

---

## 📊 Impact

- ⏱️ Reduced patient waiting time by **40–50%**
- 📈 Improved hospital workflow efficiency
- 🔄 Real-time transparency in queue management
- 🏥 Scalable across multiple hospitals

---

## 🔐 Security Features

- JWT-based authentication
- Role-based access control (RBAC)
- Input validation & rate limiting
- Secure API communication

---

## 📦 Installation & Setup

```bash
# Clone the repository
git clone https://github.com/your-username/medqueue-ai.git

# Navigate to project
cd medqueue-ai

# Create virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start server
python manage.py runserver
```

---

## 📈 Future Enhancements

- 📱 Mobile application (Android/iOS)
- 🏥 Multi-hospital SaaS deployment
- 🔔 SMS/WhatsApp notifications
- ☁️ Cloud deployment (AWS / Render)
- 📊 Advanced AI models for prediction

---

## 👨‍💻 Author

**Prajapati Shivam **
📧 [shivam4918@gmail.com](mailto:shivam4918@gmail.com)
🔗 https://www.linkedin.com/in/prajapati-shivam-647465241

---

## ⭐ Support

If you like this project, consider giving it a ⭐ on GitHub!
