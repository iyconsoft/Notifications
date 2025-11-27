"""
Example usage and testing for the Notification System
"""

# ==================== SMS EXAMPLES ====================

# Example 1: Send Single SMS via Local Provider
single_sms_request = {
    "phone_number": "+1234567890",
    "message": "Hello, this is a test SMS",
    "realm": "local"
}

# Example 2: Send Bulk SMS via PSI Provider
bulk_sms_request = {
    "recipients": [
        "+1234567890",
        "+0987654321",
        "+1111111111"
    ],
    "message": "Important announcement: System maintenance tonight at 10 PM",
    "realm": "psi"
}

# Example 3: Send SMS via Third-party Provider
thirdparty_sms_request = {
    "phone_number": "+1234567890",
    "message": "Verification code: 123456",
    "realm": "thirdparty"
}


# ==================== EMAIL EXAMPLES ====================

# Example 4: Send Single Email via SMTP
single_email_request = {
    "to_email": "user@example.com",
    "subject": "Welcome to Our Platform",
    "body": "Hello,\n\nWelcome to our platform. We're excited to have you on board.",
    "html_body": "<h1>Welcome</h1><p>Hello,</p><p>Welcome to our platform.</p>",
    "provider": "smtp"
}

# Example 5: Send Bulk Emails via ERP
bulk_email_request = {
    "recipients": [
        "user1@example.com",
        "user2@example.com",
        "user3@example.com"
    ],
    "subject": "Monthly Newsletter - January 2024",
    "body": "Dear Subscribers,\n\nHere's this month's newsletter...",
    "html_body": """
    <h1>Monthly Newsletter - January 2024</h1>
    <p>Dear Subscribers,</p>
    <p>Here's this month's newsletter...</p>
    """,
    "provider": "erp"
}

# Example 6: Send Bulk Emails via SMTP with HTML
bulk_email_html_request = {
    "recipients": [
        "admin@company.com",
        "manager@company.com"
    ],
    "subject": "Weekly Report",
    "body": "Weekly report details",
    "html_body": """
    <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>Weekly Report</h2>
            <p>Report for week of Jan 15-21, 2024</p>
            <table border="1">
                <tr><th>Metric</th><th>Value</th></tr>
                <tr><td>Users</td><td>1,234</td></tr>
                <tr><td>Revenue</td><td>$5,678</td></tr>
            </table>
        </body>
    </html>
    """,
    "provider": "smtp"
}


# ==================== PUSH NOTIFICATION EXAMPLES ====================

# Example 7: Send Single Push Notification
single_push_request = {
    "device_token": "fPZ6y1qW9sL0k3mN5oP8rQ1tU4vW7xY9z",
    "title": "New Message",
    "body": "You have a new message from John",
    "data": {
        "message_id": "msg_123",
        "sender": "john",
        "action": "open_chat"
    }
}

# Example 8: Send Bulk Push Notifications
bulk_push_request = {
    "device_tokens": [
        "token_1_abc123xyz",
        "token_2_def456uvw",
        "token_3_ghi789rst",
        "token_4_jkl012pqr"
    ],
    "title": "System Update",
    "body": "A new version is available. Please update your app.",
    "data": {
        "update_required": True,
        "version": "2.0.0",
        "action": "update_app"
    }
}

# Example 9: Send Push Notification with Promotional Data
promotional_push_request = {
    "device_tokens": [
        "user_token_1",
        "user_token_2",
        "user_token_3"
    ],
    "title": "Special Offer!",
    "body": "Get 50% off on all items today",
    "data": {
        "offer_id": "PROMO_50",
        "discount": "50",
        "action": "open_store",
        "expires_at": "2024-01-15T23:59:59Z"
    }
}


# ==================== CURL COMMANDS FOR TESTING ====================

"""
# Send Single SMS
curl -X POST "http://localhost:8000/api/notifications/sms/send" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+1234567890",
    "message": "Hello, this is a test message",
    "realm": "local"
  }'

# Send Bulk SMS
curl -X POST "http://localhost:8000/api/notifications/sms/send-bulk" \
  -H "Content-Type: application/json" \
  -d '{
    "recipients": ["+1234567890", "+0987654321"],
    "message": "Important update",
    "realm": "psi"
  }'

# Send Single Email
curl -X POST "http://localhost:8000/api/notifications/email/send" \
  -H "Content-Type: application/json" \
  -d '{
    "to_email": "user@example.com",
    "subject": "Welcome",
    "body": "Hello user",
    "provider": "smtp"
  }'

# Send Bulk Emails
curl -X POST "http://localhost:8000/api/notifications/email/send-bulk" \
  -H "Content-Type: application/json" \
  -d '{
    "recipients": ["user1@example.com", "user2@example.com"],
    "subject": "Newsletter",
    "body": "Newsletter content",
    "provider": "erp"
  }'

# Send Single Push Notification
curl -X POST "http://localhost:8000/api/notifications/push/send" \
  -H "Content-Type: application/json" \
  -d '{
    "device_token": "device_token_123",
    "title": "New Message",
    "body": "You have a new message",
    "data": {"message_id": "123"}
  }'

# Send Bulk Push Notifications
curl -X POST "http://localhost:8000/api/notifications/push/send-bulk" \
  -H "Content-Type: application/json" \
  -d '{
    "device_tokens": ["token1", "token2", "token3"],
    "title": "Announcement",
    "body": "Important announcement",
    "data": {"announcement_id": "001"}
  }'
"""


# ==================== PYTHON CLIENT EXAMPLE ====================

"""
import httpx
import asyncio

async def send_notification():
    async with httpx.AsyncClient() as client:
        # Send SMS
        response = await client.post(
            "http://localhost:8000/api/notifications/sms/send",
            json={
                "phone_number": "+1234567890",
                "message": "Hello",
                "realm": "local"
            }
        )
        print("SMS Response:", response.json())
        
        # Send Email
        response = await client.post(
            "http://localhost:8000/api/notifications/email/send",
            json={
                "to_email": "user@example.com",
                "subject": "Test",
                "body": "Test email",
                "provider": "smtp"
            }
        )
        print("Email Response:", response.json())
        
        # Send Push
        response = await client.post(
            "http://localhost:8000/api/notifications/push/send",
            json={
                "device_token": "token123",
                "title": "Test",
                "body": "Test notification"
            }
        )
        print("Push Response:", response.json())

# Run it
asyncio.run(send_notification())
"""


# ==================== RESPONSE EXAMPLES ====================

# Success Response - Single SMS
success_sms_response = {
    "success": True,
    "message": "SMS sent successfully",
    "status_code": 200,
    "data": {
        "phone_number": "+1234567890",
        "message_id": "550e8400-e29b-41d4-a716-446655440000",
        "status": "sent",
        "provider": "LOCAL",
        "timestamp": "2024-01-15T10:30:45.123456"
    }
}

# Success Response - Bulk SMS
success_bulk_sms_response = {
    "success": True,
    "message": "Bulk SMS sent successfully",
    "status_code": 200,
    "data": {
        "total": 3,
        "successful": 3,
        "failed": 0,
        "results": [
            {
                "phone_number": "+1234567890",
                "message_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "sent",
                "provider": "PSI",
                "timestamp": "2024-01-15T10:30:45.123456"
            },
            {
                "phone_number": "+0987654321",
                "message_id": "660e8400-e29b-41d4-a716-446655440001",
                "status": "sent",
                "provider": "PSI",
                "timestamp": "2024-01-15T10:30:46.123456"
            },
            {
                "phone_number": "+1111111111",
                "message_id": "770e8400-e29b-41d4-a716-446655440002",
                "status": "sent",
                "provider": "PSI",
                "timestamp": "2024-01-15T10:30:47.123456"
            }
        ],
        "timestamp": "2024-01-15T10:30:48.123456"
    }
}

# Error Response - Invalid SMS Provider
error_response = {
    "success": False,
    "error_message": "Invalid SMS provider: invalid_provider",
    "status_code": 400,
    "data": {
        "error_type": "BAD_REQUEST",
        "verbose_message": "Unknown SMS provider: invalid_provider"
    }
}

# Error Response - Empty Recipients
error_empty_recipients = {
    "success": False,
    "error_message": "At least one recipient email is required",
    "status_code": 400,
    "data": {
        "error_type": "BAD_REQUEST",
        "verbose_message": "Recipients list cannot be empty"
    }
}

# Error Response - Invalid Email Format
error_invalid_email = {
    "success": False,
    "error_message": "Invalid email addresses detected",
    "status_code": 400,
    "data": {
        "error_type": "BAD_REQUEST",
        "verbose_message": "Invalid emails: invalid-email, notanemail.com"
    }
}
