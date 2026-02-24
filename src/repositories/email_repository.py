from datetime import datetime
from typing import List, Dict, Any, Optional
from src.services import (EmailServiceFactory)
from src.core import (logging,settings)
from src.utils.helpers.errors import BadRequestError, ServiceUnavailableError


class EmailRepository:
    def __init__(self):
        self.factory = EmailServiceFactory()
    
    async def grafana_alert(self, data):
        try:          
            alerts = data.get("alerts", [])
            response = []
            for alert in alerts:
                server = alert['labels'].get('alertname')
                status = alert["annotations"].get("Status", "Down")

                if server == "DatasourceNoData":
                    server = alert['labels'].get('rulename')
                    status = alert['labels'].get('severity')

                subject = f"Monitoring Alert: {server} {status}"
                desc = alert["annotations"].get("summary_resolved", "summary")

                response.append(
                    await self.send_bulk_emails(
                        recipients=settings.grafana_emails,
                        subject=subject,
                        body=desc,
                        provider="erp"
                    )
                )
            return True
        except Exception as e:
            raise e
    
    async def subscribe_email(info: dict):
        try:            
            return {
                "success": "subscribers",
                "data": {}
            }
        except Exception as e:
            return JSONResponse( status_code = 500, content = { "error": str(e) })

    
    async def send_single_email(self, to_email: str, subject: str, body: str, 
                               html_body: Optional[str] = None, provider: str = "smtp", template_id:str = None) -> Dict[str, Any]:
        """
        Send a single email
        
        Args:
            to_email: Recipient's email address
            subject: Email subject
            body: Email body (plain text)
            html_body: Email body (HTML format, optional)
            provider: Email provider type (smtp, erp)
        
        Returns:
            Dictionary with send status
        """
        try:
            # Validate inputs
            if not to_email or not subject or not body:
                raise BadRequestError(
                    message="Email, subject, and body are required",
                    verboseMessage="to_email, subject, and body fields must all be provided"
                )
            
            if not provider:
                raise BadRequestError(
                    message="Email provider is required",
                    verboseMessage="Provider field must be one of: smtp, erp"
                )
            
            # Validate email format
            if not self._is_valid_email(to_email):
                raise BadRequestError(
                    message="Invalid email format",
                    verboseMessage=f"Email '{to_email}' is not in valid format"
                )
            
            email_provider = self.factory.get_provider(provider)
            result = await email_provider.send(to_email, subject, body, html_body, template_id)
            
            logging.info(f"Sending single email to {to_email} via {provider} was sent successfully")
            return {
                "success": result.get("status") == "sent",
                "data": result
            }
            
        except BadRequestError:
            raise
        except ValueError as ve:
            raise BadRequestError(
                message=f"Invalid email provider: {provider}",
                verboseMessage=str(ve)
            )
        except Exception as e:
            logging.error(f"Email send failed: {str(e)}")
            raise ServiceUnavailableError(
                message="Failed to send email",
                verboseMessage=str(e)
            )
    
    async def send_bulk_emails(self, recipients: List[str], subject: str, body: str,
                              html_body: Optional[str] = None, provider: str = "smtp") -> Dict[str, Any]:
        """
        Send bulk emails
        
        Args:
            recipients: List of recipient email addresses
            subject: Email subject
            body: Email body (plain text)
            html_body: Email body (HTML format, optional)
            provider: Email provider type (smtp, erp)
        
        Returns:
            Dictionary with bulk send status and results
        """
        try:
            # Validate inputs
            if not recipients or len(recipients) == 0:
                raise BadRequestError(
                    message="At least one recipient email is required",
                    verboseMessage="Recipients list cannot be empty"
                )
            
            if not subject or not body:
                raise BadRequestError(
                    message="Subject and body are required",
                    verboseMessage="Subject and body fields must be provided"
                )
            
            if not provider:
                raise BadRequestError(
                    message="Email provider is required",
                    verboseMessage="Provider field must be one of: smtp, erp"
                )
            
            # Validate all email addresses
            invalid_emails = [email for email in recipients if not self._is_valid_email(email)]
            if invalid_emails:
                raise BadRequestError(
                    message="Invalid email addresses detected",
                    verboseMessage=f"Invalid emails: {', '.join(invalid_emails)}"
                )
            
            email_provider = self.factory.get_provider(provider)
            results = await email_provider.send_bulk(recipients, subject, body, html_body)
            
            # Calculate statistics
            successful = sum(1 for r in results if r.get("status") == "sent")
            failed = len(results) - successful
            
            logging.info(f"Sending bulk emails to {len(recipients)} recipients via {provider} has successfully sent {successful} email of {len(results)}")
            return {
                "success": failed == 0,
                "data": {
                    "total": len(results),
                    "successful": successful,
                    "failed": failed,
                    "results": results,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
        except BadRequestError:
            raise
        except ValueError as ve:
            raise BadRequestError(
                message=f"Invalid email provider: {provider}",
                verboseMessage=str(ve)
            )
        except Exception as e:
            logging.error(f"Bulk email send failed: {str(e)}")
            raise ServiceUnavailableError(
                message="Failed to send bulk emails",
                verboseMessage=str(e)
            )
    
    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """Basic email validation"""
        if not email or '@' not in email or '.' not in email.split('@')[-1]:
            return False
        return True
