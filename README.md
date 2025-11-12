# Iyconsoft Notification API

**Version:** 0.0.1  
**Author:** Iyconsoft  

A lightweight notification service API built with **FastAPI** for sending email notifications and managing subscriptions. This service integrates with ERP systems and provides bulk email functionalities.

---

## Table of Contents
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

## Features

- Send email notifications to individual or multiple recipients
- Subscribe emails to the notification list
- Integration with **ERP** systems (e.g., Odoo)
- Middleware support for:
  - CORS
  - GZip compression
  - Trusted hosts
  - SQLAlchemy async database connections
  - IP blocking
- OTP generation utility
- Configurable via `.conf` file or environment variables

---

## Tech Stack

- **Python 3.11+**
- **FastAPI** – Web framework
- **SQLAlchemy (async)** – Database ORM
- **SQLite** – Default database
- **HTTPX** – Async HTTP requests for ERP integration
- **Pydantic / Pydantic Settings** – Configuration & validation
- **aiosmtplib** – Async email sending
- **Middleware**:
  - CORS
  - GZip
  - HTTPS redirect
  - Trusted host
- **EmailLib** (custom utility for sending emails)
- **Utilities**: OTP generator, IP blocking, random number generation

---

## Installation

1. Clone the repository:

```bash
git clone <REPO_URL>
cd notification-service


Configuration

All configuration settings are stored in .conf or src/core/config.py using Pydantic Settings. Example:

debug: bool
is_demo: bool = True
app_name: str
app_description: str
app_origins: list[str]
app_root: str
port: int
app_version: str
secret_key: str
db_name: str
sqlalchemy_database_uri: str

mail_server: str
mail_port: int
mail_sender: int
mail_username: str
mail_password: str
mail_from_name: str
mail_tls: bool
mail_ssl: bool
use_credentials: bool
validate_certs: bool

odoo_url: str
odoo_headers: dict
odoo_payload: dict


Environment variables are loaded from .conf using python-dotenv.

Usage

Run the FastAPI server:

uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload


Visit the interactive API documentation:

http://localhost:8000/docs

API Endpoints
Email Endpoints

Send Email
POST /emails/send

Subscribe Email
POST /emails/subscribe

Bulk Email Notification
POST /emails/bulk

Request/response schemas use the IMail Pydantic model:

{
  "email": "user@example.com",
  "subject": "Notification",
  "message": "Hello! This is a test notification.",
  "sender": "Iyconsoft Notifications"
}
