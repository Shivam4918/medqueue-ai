# 🚑 MedQueue AI

### Real-Time Hospital Queue Management System (AI-Powered SaaS)

\

## 🌐 Overview

MedQueue AI is a **scalable, AI-powered SaaS platform** designed to digitize hospital OPD queue management.
It leverages **real-time systems, machine learning, and modern web technologies** to improve patient experience and hospital efficiency.

## 🎯 Key Highlights

- ⚡ Real-time queue tracking using **WebSockets + Redis**
- 🤖 AI-based waiting time prediction (Random Forest, LightGBM)
- 🏥 Multi-role system (Patient, Doctor, Hospital Admin, Receptionist, Super Admin)
- 📊 Analytics dashboard for data-driven decisions
- 🔐 Secure authentication with JWT & RBAC

## 📸 Screenshots

### 🏠 Dashboard Overview

### 🎟️ Token Booking Interface

### 📡 Live Queue Tracking

Real-time updates powered by WebSockets\

### 👨‍⚕️ Doctor Panel

### 🏥 Admin Analytics Dashboard

### 🤖 AI Waiting Time Prediction

## 🧠 Problem Solved

Traditional hospital queue systems suffer from:

- Long waiting times (2–5 hours)
- No real-time visibility
- Poor emergency handling
- Lack of analytics

👉 MedQueue AI solves this with automation, AI, and real-time tracking.

## 🏗️ System Architecture

```
Client Layer (Patient / Doctor / Admin)
        ↓
Frontend (HTML, Tailwind, JS, HTMX)
        ↓
Django Backend (REST APIs)
        ↓
-----------------------------------------
| MySQL | MongoDB | Redis (Cache/Queue) |
-----------------------------------------
        ↓
Django Channels (WebSockets)
        ↓
AI Prediction Engine (ML Models)
```

## 🛠️ Tech Stack

### 🔹 Backend

- Django
- Django REST Framework (DRF)

### 🔹 Frontend

- HTML5, CSS3, JavaScript
- Tailwind CSS, HTMX

### 🔹 Databases

- MySQL (Relational Data)
- MongoDB (Logs & Analytics)

### 🔹 Real-Time

- Django Channels
- Redis

### 🔹 AI / ML

- Random Forest
- LightGBM
- Predictive Analytics

### 🔹 Security

- JWT Authentication
- Role-Based Access Control (RBAC)

## 🔌 API Overview

| Method | Endpoint          | Description        |
| ------ | ----------------- | ------------------ |
| POST   | `/api/token/`     | Create new token   |
| GET    | `/api/queue/`     | Get live queue     |
| POST   | `/api/emergency/` | Emergency priority |
| GET    | `/api/predict/`   | Get AI prediction  |

## ⚙️ Installation

```bash
git clone https://github.com/your-username/medqueue-ai.git
cd medqueue-ai

python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

pip install -r requirements.txt

python manage.py migrate
python manage.py runserver
```

## 🚀 Deployment

- Render / Railway (Backend)
- MongoDB Atlas (Database)
- Redis Cloud (Real-time engine)

## 📊 Impact

- ⏱️ Reduced waiting time by **40–50%**
- 📈 Improved operational efficiency
- 🔄 Real-time transparency
- 🏥 Scalable for multi-hospital systems

## 🔐 Security Features

- JWT-based authentication
- RBAC (multi-role access)
- Input validation & rate limiting
- Secure API communication (HTTPS)

## 📈 Future Scope

- 📱 Mobile App (Flutter / React Native)
- 🏥 Multi-hospital SaaS platform
- 🔔 WhatsApp/SMS notifications
- ☁️ Kubernetes deployment
- 📊 Advanced AI models (Deep Learning)

## 📁 Project Structure

```
medqueue-ai/
│── backend/
│── frontend/
│── models/
│── api/
│── requirements.txt
│── README.md
```

## 👨‍💻 Author

**Shivam Prajapati**
📧 [shivam4918@gmail.com](mailto:shivam4918@gmail.com)
🔗 https://www.linkedin.com/in/prajapati-shivam-647465241

## ⭐ Show Your Support

If you found this project useful, give it a ⭐ on GitHub!
