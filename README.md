# Iyconsoft Notification API

**Version:** 0.0.1  

A lightweight Notification Service API built with FastAPI for sending email notifications, managing subscriptions, and integrating with ERP systems. Supports bulk email and asynchronous operations for high performance.

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
- [Docker Support](#-docker-support)
- [Testing](#-testing)

## 🚀 Features

- ✉️ Send email notifications to individual or multiple recipients
- 📧 Subscribe emails to a notification list
- 🔗 Integrates with ERP systems (e.g., Odoo)
- 🛡️ Middleware support for:
  - CORS
  - GZip compression
  - Trusted hosts
  - IP blocking
- 🗄️ Async SQLAlchemy database connections
- 🔐 OTP generation utility
- ⚙️ Configurable via `.conf` file or environment variables

## 🛠 Tech Stack

- **Python 3.11+**
- **FastAPI** – Web framework
- **SQLAlchemy (async)** – Database ORM
- **SQLite** – Default database
- **HTTPX** – Async HTTP client for ERP integration
- **Pydantic / Pydantic Settings** – Configuration & validation
- **aiosmtplib** – Async email sending
- **Middleware & Utilities:**
  - CORS, GZip, HTTPS redirect, Trusted hosts
  - EmailLib (custom email utility)
  - OTP generator, IP blocking, random number generator

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone <REPO_URL>
cd notification-service
```

### 2. Create and activate a virtual environment

**Linux / macOS:**
```bash
python -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

## 🔧 Configuration

All settings are stored in `.conf` or `src/core/config.py` using Pydantic Settings.

### Example `.conf` configuration:

```ini
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
mail_username = ""
mail_password = ""
mail_from_name = ""
mail_tls = True
mail_ssl = False
use_credentials = True
validate_certs = True

# ERP
odoo_url = "https://devapi.iyconsoft.com/api/erp/"
odoo_headers = {"Content-Type": "application/json"}
odoo_payload = {
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        # ... your ERP parameters
    }
}
```

### Environment Variables Setup

Create a `.env` file:

```env
DEBUG=True
APP_NAME=Iyconsoft Notification API
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
SECRET_KEY=your-secret-key-here
```

**Note:** Environment variables are loaded automatically using `python-dotenv`.

## ⚡ Usage

### Start the FastAPI server:

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### Access the API:

- **API Documentation:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **Health Check:** `http://localhost:8000/health`

## 📝 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/notifications/send` | POST | Send email notification(s) |
| `/notifications/subscribe` | POST | Subscribe an email to a list |
| `/erp/integrate` | POST | Send data to ERP system |
| `/health` | GET | Health check endpoint |

All endpoints support JSON payloads and asynchronous operations.

### Send Single Email

```bash
curl -X POST "http://localhost:8000/notifications/send" \
  -H "Content-Type: application/json" \
  -d '{
    "recipient": "user@example.com",
    "subject": "Welcome to Iyconsoft",
    "message": "Your registration was successful!"
  }'
```

### Send Bulk Emails

```bash
curl -X POST "http://localhost:8000/notifications/send" \
  -H "Content-Type: application/json" \
  -d '{
    "recipients": ["user1@example.com", "user2@example.com"],
    "subject": "Bulk Notification",
    "message": "This is a bulk email notification."
  }'
```

### Subscribe to Newsletter

```bash
curl -X POST "http://localhost:8000/notifications/subscribe" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "list_name": "newsletter"
  }'
```

## 🛡 Middleware

The API includes several middleware components for security and performance:

### CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### GZip Compression

```python
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### Trusted Host Middleware

```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["example.com", "*.example.com"]
)
```

### IP Blocking

```python
# Custom IP blocking middleware
@app.middleware("http")
async def block_ips(request: Request, call_next):
    client_ip = request.client.host
    if client_ip in BLOCKED_IPS:
        raise HTTPException(status_code=403, detail="Access forbidden")
    response = await call_next(request)
    return response
```

## 🔗 ERP Integration

Integrates with ERP systems (like Odoo) via HTTPX async client. Supports JSON-RPC for sending/receiving data.

### Example ERP Integration

```python
import httpx
from src.core.config import settings

async def send_to_erp(data: dict):
    async with httpx.AsyncClient() as client:
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "model": "res.partner",
                "method": "create",
                "args": [data]
            }
        }
        
        response = await client.post(
            settings.odoo_url,
            json=payload,
            headers=settings.odoo_headers
        )
        
        return response.json()
```

### ERP Endpoint Usage

```bash
curl -X POST "http://localhost:8000/erp/integrate" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "res.partner",
    "method": "create",
    "data": {
      "name": "John Doe",
      "email": "john@example.com",
      "phone": "+1234567890"
    }
  }'
```

## 🛠 Utilities

### OTP Generator

```python
from src.utils.otp import generate_otp

# Generate 6-digit OTP
otp = generate_otp(length=6)
print(otp)  # Output: 123456

# Generate alphanumeric OTP
otp = generate_otp(length=8, alphanumeric=True)
print(otp)  # Output: A1B2C3D4
```

### IP Blocking Utility

```python
from src.utils.ip_blocking import is_ip_blocked, block_ip

# Check if IP is blocked
if is_ip_blocked("192.168.1.100"):
    print("IP is blocked")

# Block an IP
block_ip("192.168.1.100")
```

### Random Number Generator

```python
from src.utils.random_gen import generate_random_number

# Generate random number between 1000-9999
random_num = generate_random_number(min_val=1000, max_val=9999)
print(random_num)  # Output: 7542
```

## 📂 Example Output

### Send Email Request

**Request:**
```json
POST /notifications/send
Content-Type: application/json

{
  "recipients": ["user@example.com", "admin@example.com"],
  "subject": "Welcome to Iyconsoft",
  "message": "Your registration was successful!"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Emails sent successfully",
  "recipients": ["user@example.com", "admin@example.com"],
  "sent_count": 2,
  "timestamp": "2026-01-28T10:30:00Z"
}
```

### Subscribe Email Request

**Request:**
```json
POST /notifications/subscribe
Content-Type: application/json

{
  "email": "user@example.com",
  "list_name": "newsletter"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Email subscribed successfully",
  "email": "user@example.com",
  "list_name": "newsletter",
  "subscription_id": "sub_123456789"
}
```

### ERP Integration Response

**Response:**
```json
{
  "status": "success",
  "message": "Data sent to ERP successfully",
  "erp_response": {
    "jsonrpc": "2.0",
    "result": {
      "id": 42,
      "name": "John Doe"
    }
  }
}
```

## 🐳 Docker Support

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  notification-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=False
      - MAIL_SERVER=smtp.gmail.com
      - MAIL_PORT=587
    volumes:
      - ./data:/app/data
    restart: unless-stopped

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    restart: unless-stopped
```

### Build and Run

```bash
# Build the image
docker build -t iyconsoft-notification-api .

# Run the container
docker run -d -p 8000:8000 --name notification-api iyconsoft-notification-api

# Using docker-compose
docker-compose up -d
```

## 🧪 Testing

### Run Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_notifications.py
```

### Test Email Sending

```python
import pytest
from httpx import AsyncClient
from src.main import app

@pytest.mark.asyncio
async def test_send_email():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/notifications/send", json={
            "recipient": "test@example.com",
            "subject": "Test Email",
            "message": "This is a test email"
        })
    assert response.status_code == 200
    assert response.json()["status"] == "success"
```

## 📊 Monitoring & Logging

### Health Check

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-28T10:30:00Z",
  "version": "0.0.1",
  "database": "connected",
  "email_service": "available"
}
```

### Logging Configuration

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Log email sending
logger.info(f"Email sent to {recipient}")
logger.error(f"Failed to send email: {error}")
```

## 🔎 Business Process Notes

### Email Processing Workflow

1. **Open the email** → click on the email → find Realtor CID number
2. **If it's a BRD**, follow the full BRD process (ask @Adedeji if unsure)
3. **Verify CID and name match** on the portal
4. **Once confirmed**, register client here: `https://portal.zylusgroup.com/client-register/{cid}`

### Integration Checklist

- [ ] Configure SMTP settings
- [ ] Set up ERP connection
- [ ] Test email delivery
- [ ] Verify subscription functionality
- [ ] Configure middleware settings
- [ ] Set up monitoring and logging

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make your changes
4. Add tests for new functionality
5. Run tests: `pytest`
6. Commit changes: `git commit -am 'Add new feature'`
7. Push to branch: `git push origin feature/new-feature`
8. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the API documentation at `/docs`
- Contact: support@iyconsoft.com

---

**Built with FastAPI and modern Python async patterns for reliable email notifications and ERP integration.**
