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
