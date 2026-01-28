# Iyconsoft Notification API

**Version:** 0.0.1  
**Author:** Iyconsoft  

A lightweight **Notification Service API** built with **FastAPI** for sending email notifications, managing subscriptions, and integrating with ERP systems. Supports bulk email and asynchronous operations for high performance.

---

## 📌 Table of Contents

- [Features](#-features)  
- [Tech Stack](#-tech-stack)  
- [Installation](#-installation)  
- [Configuration](#-configuration)  
- [Usage](#-usage)  
- [API Endpoints](#-api-endpoints)  
- [Middleware](#-middleware)  
- [ERP Integration](#-erp-integration)  
- [Utilities](#-utilities)  
- [Example Output](#-example-output)  

---

## 🚀 Features

- Send email notifications to individual or multiple recipients  
- Subscribe emails to a notification list  
- Integrates with ERP systems (e.g., Odoo)  
- Middleware support for:
  - CORS  
  - GZip compression  
  - Trusted hosts  
  - IP blocking  
- Async SQLAlchemy database connections  
- OTP generation utility  
- Configurable via `.conf` file or environment variables  

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

Clone the repository:

```bash
git clone <REPO_URL>
cd notification-service
Create and activate a virtual environment:

# Linux / macOS
python -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
Install dependencies:

pip install -r requirements.txt
🔧 Configuration
All settings are stored in .conf or src/core/config.py using Pydantic Settings.

Example .conf configuration:

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
Note: Environment variables are loaded automatically using python-dotenv.

⚡ Usage
Start the FastAPI server:

uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
📝 API Endpoints
Endpoint	Method	Description
/notifications/send	POST	Send email notification(s)
/notifications/subscribe	POST	Subscribe an email to a list
/erp/integrate	POST	Send data to ERP system
All endpoints support JSON payloads and asynchronous operations.

🛡 Middleware
CORS – Allow cross-origin requests

GZip compression – Reduce payload size

HTTPS redirect – Force HTTPS requests

Trusted host – Restrict allowed hosts

IP blocking – Block unwanted IPs

🔗 ERP Integration
Integrates with ERP systems (like Odoo) via HTTPX async client

Supports JSON-RPC for sending/receiving data

Example ERP payload:

{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "model": "res.partner",
    "method": "create",
    "args": [{"name": "John Doe"}]
  }
}
🛠 Utilities
OTP generator for secure verification

IP blocking for restricted access

Random number generator for transactional needs

📂 Example Output
Send Email Request

POST /notifications/send
Content-Type: application/json

{
  "recipients": ["user@example.com", "admin@example.com"],
  "subject": "Welcome to Iyconsoft",
  "message": "Your registration was successful!"
}
Response

{
  "status": "success",
  "message": "Emails sent successfully",
  "recipients": ["user@example.com", "admin@example.com"]
}
Subscribe Email Request

POST /notifications/subscribe
Content-Type: application/json

{
  "email": "user@example.com",
  "list_name": "newsletter"
}
Response

{
  "status": "success",
  "message": "Email subscribed successfully",
  "email": "user@example.com"
}
🔎 Notes
Open the email → click on the email → find Realtor CID number

If it’s a BRD, follow the full BRD process (ask @Adedeji if unsure)

Verify CID and name match on the portal

Once confirmed, register client here:
https://portal.zylusgroup.com/client-register/{cid}

