# 🎓 CampusOne

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?style=flat-square&logo=react)](https://reactjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql)](https://www.postgresql.org/)
[![Brevo](https://img.shields.io/badge/Brevo-HTTP_API-0092FF?style=flat-square)](https://brevo.com)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker)](https://www.docker.com/)
[![Render Ready](https://img.shields.io/badge/Render-Deployed-46E3B7?style=flat-square&logo=render)](https://render.com)

**CampusOne** is a full-stack, campus-exclusive web application engineered specifically for **MANIT (Maulana Azad National Institute of Technology)** students and alumni. Built with a high-performance **FastAPI + PostgreSQL** backend and a responsive **React + Vite** frontend, CampusOne unifies essential campus utilities into a modern ecosystem.

---

## ✨ Key Features

- 🔒 **Campus-Exclusive Authentication**: Access restricted strictly to `@stu.manit.ac.in` domain emails. Accounts are verified via 6-digit OTP delivery powered by **Brevo HTTP REST API** and authenticated with **JWT tokens**.
- 🛍️ **Campus Marketplace**: Buy, sell, and trade student items (textbooks, hostel gear, electronics, cycles) with privacy-aware seller cards and negotiable price tags.
- 🔍 **Private Lost & Found Tracker**: Report lost/found items privately with automated similarity scoring and physical desk OTP handoff verification.
- 💬 **Anonymous Community Chat**: Real-time campus discussion rooms (`#general`, `#marketplace`, `#academics`, `#hostels`) powered by **WebSockets** with REST fallback.
- ⚡ **Glassmorphic UI**: Production-grade responsive dark design system with dynamic HSL color tokens, micro-animations, and mobile optimization.

---

## 🛠️ Tech Stack & Architecture

### Backend
* **Framework**: FastAPI (Python 3.11+)
* **Database**: PostgreSQL with SQLAlchemy 2.0 ORM & Alembic migrations
* **Security & Auth**: Native `bcrypt` password hashing & `pyjwt` session management
* **Email Delivery**: Brevo HTTP REST API (`httpx` HTTP client over Port 443)
* **Real-time Engine**: FastAPI WebSockets

### Frontend
* **Framework**: React 18 with Vite
* **Styling**: Glassmorphism design system, CSS custom properties, responsive grid math
* **Typography**: Google Fonts (`Outfit`, `Space Grotesk`, `Inter`)

### Infrastructure & Deployment
* **Containerization**: Docker & Docker Compose
* **Cloud Platform**: Production-ready for Render, Railway, or VPS hosting

---

## 📂 Project Structure

```text
CampusOne/
├── backend/
│   ├── app/
│   │   ├── core/           # Security (bcrypt, PyJWT) & app configuration
│   │   ├── db/             # SQLAlchemy DB session & base models
│   │   ├── modules/        # Domain-driven feature modules
│   │   │   ├── auth/       # Registration, login, OTP via Brevo REST API
│   │   │   ├── chat/       # REST endpoints & WebSockets router
│   │   │   ├── lost_found/ # Lost & found reporting, matching & desk OTP
│   │   │   └── product/    # Marketplace listings & categories
│   │   ├── dependencies.py # Shared FastAPI dependencies (OAuth2/DB)
│   │   ├── main.py         # Application entrypoint & CORS config
│   │   └── seed.py         # Database initial seeding script
│   ├── alembic/            # Database schema migration scripts
│   ├── Dockerfile          # Backend container definition
│   └── requirements.txt    # Python dependencies (fastapi, httpx, bcrypt, pyjwt)
├── frontend/
│   ├── src/
│   │   ├── components/     # Reusable UI components (AdminDashboard)
│   │   ├── App.jsx         # Main application dashboard & router
│   │   ├── api.js          # Centralized API client service
│   │   └── styles.css      # Core theme tokens & glassmorphic styling
│   ├── Dockerfile          # Frontend container definition
│   ├── nginx.conf          # Nginx web server config for production
│   └── package.json        # Node.js dependencies
└── docker-compose.yml      # Orchestrates Postgres, Backend, & Frontend
```

---

## ⚙️ Environment Configuration

Create a `.env` file in the `backend/` directory (or configure environment variables in your Render Dashboard):

```env
# Database Connection URL
DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/campusone

# Application Security
SECRET_KEY=change-this-to-a-secure-random-secret-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Environment Mode ("development" logs OTPs to terminal; "production" sends live emails)
ENVIRONMENT=development

# Brevo HTTP REST API Configuration (Bypasses SMTP block on Render)
BREVO_API_KEY=xkeysib-your_brevo_api_key_here
BREVO_SENDER_EMAIL=your-verified-personal-email@gmail.com

# Campus Domain Restriction
CAMPUS_EMAIL_DOMAIN=@stu.manit.ac.in
```

---

## 📧 Brevo API Setup (For Render Deployment)

Render blocks traditional SMTP ports (`25`, `465`, `587`). CampusOne uses **Brevo's HTTP REST API (`https://api.brevo.com/v3/smtp/email`)** over standard HTTPS (Port 443), which allows sending emails to any recipient without requiring a paid custom domain.

1. **Create a Free Account**: Sign up at [brevo.com](https://brevo.com).
2. **Verify Sender Email**: Go to **Senders & IPs** in the Brevo dashboard and verify your personal email address (`yourname@gmail.com`).
3. **Generate API Key**: Go to **SMTP & API** → **API Keys** and generate a v3 API key.
4. **Set Variables on Render**:
   - `BREVO_API_KEY`: `xkeysib-...`
   - `BREVO_SENDER_EMAIL`: `yourname@gmail.com`

> [!TIP]
> **Local Development Mode**: When `ENVIRONMENT=development`, the backend prints the 6-digit OTP directly to your terminal logs (`[DEV MODE OTP LOG] 🔑 Verification code for user: 123456`), allowing instant testing even before API keys are configured!

---

## 🚀 Quick Start (Local Development)

### Option 1: Running with Docker Compose (Recommended)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/CampusOne.git
   cd CampusOne
   ```

2. **Configure environment file**:
   ```bash
   cp backend/.env.example backend/.env
   ```

3. **Build and launch containers**:
   ```bash
   docker compose up -d --build
   ```

4. **Apply database migrations and seed initial data**:
   ```bash
   docker compose exec backend alembic upgrade head
   docker compose exec backend python -m app.seed
   ```

5. **Access Application**:
   * 🌐 **Frontend UI**: [http://localhost:5173](http://localhost:5173)
   * 📜 **Swagger API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
   * 📖 **ReDoc OpenAPI Specs**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

### Option 2: Running Backend Locally (Python)

1. **Initialize virtual environment & install dependencies**:
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Run dev server**:
   ```bash
   alembic upgrade head
   python -m app.seed
   uvicorn app.main:app --reload --port 8000
   ```

---

## 🔑 Seeded Test Accounts

Running `python -m app.seed` populates the database with sample accounts for testing:

| Role | Campus Email | Access Level |
| :--- | :--- | :--- |
| **Admin** | `admin@stu.manit.ac.in` | Desk operations, match review, OTP verification console |
| **Student** | `ananya@stu.manit.ac.in` | Marketplace, private lost-and-found, community chat |

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for details.
