# Iyconsoft Notification API

**Version:** 0.0.1  
**Author:** Iyconsoft  

A lightweight **Notification Service API** built with **FastAPI** for sending email notifications, managing subscriptions, and integrating with ERP systems. Supports bulk email functionalities and asynchronous operations for performance.

---

## 📌 Table of Contents

- [Features](#features)  
- [Tech Stack](#tech-stack)  
- [Installation](#installation)  
- [Configuration](#configuration)  
- [Usage](#usage)  
- [API Endpoints](#api-endpoints)  
- [Middleware](#middleware)  
- [ERP Integration](#erp-integration)  
- [Utilities](#utilities)  

---

## 🚀 Features

- Send **email notifications** to individual or multiple recipients  
- Subscribe emails to a **notification list**  
- Integrates with **ERP systems** (e.g., Odoo)  
- **Middleware support** for:  
  - CORS  
  - GZip compression  
  - Trusted hosts  
  - SQLAlchemy async database connections  
  - IP blocking  
- **OTP generation** utility  
- Configurable via **.conf** file or environment variables  

---

## 🛠 Tech Stack

- **Python 3.11+**  
- **FastAPI** – Web framework  
- **SQLAlchemy (async)** – Database ORM  
- **SQLite** – Default database  
- **HTTPX** – Async HTTP client for ERP integration  
- **Pydantic / Pydantic Settings** – Configuration & validation  
- **aiosmtplib** – Async email sending  

**Middleware & Utilities:**

- CORS, GZip, HTTPS redirect, Trusted host  
- EmailLib (custom email utility)  
- OTP generator, IP blocking, random number generator  

---

## ⚙️ Installation

1. Clone the repository:

```bash
git clone <REPO_URL>
cd notification-service
Create and activate a virtual environment:

bash
Copy code
python -m venv venv
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate      # Windows
Install dependencies:

bash
Copy code
pip install -r requirements.txt
🔧 Configuration
All settings are stored in .conf or src/core/config.py using Pydantic Settings.

Example configuration:

ini
Copy code
# App settings
debug = True
is_demo = True
app_name = "Iyconsoft Notification API"
app_root = "/notifications"
app_version = "0.0.1"
app_origins = ["*"]
port = 8000
secret_key = "your_secret_key"

# Email
mail_server = "smtp.example.com"
mail_port = 587
mail_sender = "notifications@example.com"
mail_username = "username"
mail_password = "password"
mail_from_name = "Iyconsoft Notifications"
mail_tls = True
mail_ssl = False
use_credentials = True
validate_certs = True

# ERP
odoo_url = "https://devapi.iyconsoft.com/api/erp/"
odoo_headers = {"Content-Type": "application/json"}
odoo_payload = { "jsonrpc": "2.0", "method": "call", "params": { ... } }
Environment variables are loaded automatically using python-dotenv.

⚡ Usage
Start the FastAPI server:

bash
Copy code
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload




* open email
* click on an email
* find realtor cid number
* NB: if its a brd it would be specified if not sure ask @Adedeji
* NB: there is a full process for BRD
* check on the portal if the cid and name is same on email
* ifconfirmed pass the cid number to the client register portal  - https://portal.zylusgroup.com/client-register/{cid} 