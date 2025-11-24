"""
InsightCosmos Email Sender

Provides email sending functionality with support for HTML and plain text formats.

Classes:
    EmailConfig: Email configuration dataclass
    EmailSender: Email sending utility with SMTP support

Usage:
    from src.tools.email_sender import EmailSender, EmailConfig

    config = EmailConfig(
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        sender_email="your@gmail.com",
        sender_password="your_app_password"
    )

    sender = EmailSender(config)

    # Send HTML email
    result = sender.send(
        to_email="recipient@example.com",
        subject="Daily Digest - 2025-11-24",
        html_body="<html><body>...</body></html>",
        text_body="Plain text version..."
    )
"""

from typing import Optional, Dict, Any
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from dataclasses import dataclass
import time
import logging

from src.utils.logger import Logger


@dataclass
class EmailConfig:
    """
    Email configuration

    Attributes:
        smtp_host: SMTP server hostname (default: smtp.gmail.com)
        smtp_port: SMTP server port (default: 587 for TLS)
        sender_email: Sender email address
        sender_password: Sender email password (App Password for Gmail)
        use_tls: Whether to use TLS encryption (default: True)
    """
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    sender_email: str = ""
    sender_password: str = ""
    use_tls: bool = True

    def __post_init__(self):
        """Validate configuration"""
        if not self.sender_email:
            raise ValueError("sender_email is required")
        if not self.sender_password:
            raise ValueError("sender_password is required")


class EmailSender:
    """
    Email sending utility

    Supports:
    - HTML email (primary)
    - Plain text email (fallback)
    - Multipart email (HTML + Text)
    - SMTP with TLS
    - Retry mechanism

    Example:
        >>> config = EmailConfig(
        ...     sender_email="your@gmail.com",
        ...     sender_password="your_app_password"
        ... )
        >>> sender = EmailSender(config)
        >>> result = sender.send(
        ...     to_email="ray@example.com",
        ...     subject="Daily Digest - 2025-11-24",
        ...     html_body="<html>...</html>",
        ...     text_body="Plain text..."
        ... )
        >>> print(result['status'])
        success
    """

    def __init__(self, config: EmailConfig):
        """
        Initialize EmailSender

        Args:
            config: Email configuration

        Raises:
            ValueError: If configuration is invalid
        """
        self.config = config
        self.logger = Logger.get_logger(__name__)
        self.logger.info(f"EmailSender initialized for {config.sender_email}")

    def send(
        self,
        to_email: str,
        subject: str,
        html_body: Optional[str] = None,
        text_body: Optional[str] = None,
        retry_count: int = 3
    ) -> Dict[str, Any]:
        """
        Send email with retry mechanism

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML body (optional)
            text_body: Plain text body (optional)
            retry_count: Number of retries on failure (default: 3)

        Returns:
            dict: {
                "status": "success" | "error",
                "message": str,
                "error": str (if error),
                "retry_attempts": int (if retried)
            }

        Raises:
            ValueError: If both html_body and text_body are None

        Example:
            >>> result = sender.send(
            ...     to_email="ray@example.com",
            ...     subject="Daily Digest",
            ...     html_body="<html><body>...</body></html>",
            ...     text_body="Plain text version..."
            ... )
            >>> if result['status'] == 'success':
            ...     print("Email sent successfully")
        """
        # Validate input
        if html_body is None and text_body is None:
            raise ValueError("At least one of html_body or text_body must be provided")

        # Validate email address (basic check)
        if '@' not in to_email:
            return {
                "status": "error",
                "message": f"Invalid recipient email: {to_email}",
                "error": "Invalid email format"
            }

        # Retry loop
        last_error = None
        for attempt in range(retry_count):
            try:
                # Create message
                message = self._create_message(to_email, subject, html_body, text_body)

                # Send via SMTP
                self._send_via_smtp(message, to_email)

                self.logger.info(f"Email sent successfully to {to_email}")

                result = {
                    "status": "success",
                    "message": f"Email sent to {to_email}"
                }

                if attempt > 0:
                    result["retry_attempts"] = attempt

                return result

            except smtplib.SMTPAuthenticationError as e:
                # Authentication error - no retry
                error_msg = (
                    "❌ Email authentication failed!\n\n"
                    "Please verify your email configuration:\n"
                    "1. EMAIL_ACCOUNT: Your Gmail address\n"
                    "2. EMAIL_PASSWORD: App-specific password (NOT your account password)\n\n"
                    "How to get an App Password:\n"
                    "https://support.google.com/accounts/answer/185833\n\n"
                    f"Error details: {str(e)}"
                )
                self.logger.error(error_msg)
                return {
                    "status": "error",
                    "message": "Authentication failed",
                    "error": error_msg
                }

            except smtplib.SMTPRecipientsRefused as e:
                # Recipient refused - no retry
                error_msg = f"Recipient {to_email} was refused by the server: {str(e)}"
                self.logger.error(error_msg)
                return {
                    "status": "error",
                    "message": "Recipient refused",
                    "error": error_msg
                }

            except (smtplib.SMTPException, ConnectionError, TimeoutError) as e:
                # Network/SMTP errors - retry
                last_error = e
                self.logger.warning(
                    f"Email send attempt {attempt + 1}/{retry_count} failed: {str(e)}"
                )

                if attempt < retry_count - 1:
                    # Exponential backoff: 1s, 2s, 4s
                    sleep_time = 2 ** attempt
                    self.logger.info(f"Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
                else:
                    # Final attempt failed
                    error_msg = (
                        f"Failed to send email after {retry_count} attempts.\n"
                        f"Last error: {str(last_error)}\n\n"
                        "Possible causes:\n"
                        "1. Network connection issues\n"
                        "2. SMTP server is down\n"
                        "3. Firewall blocking SMTP port {self.config.smtp_port}\n"
                    )
                    self.logger.error(error_msg)
                    return {
                        "status": "error",
                        "message": f"Failed after {retry_count} retries",
                        "error": error_msg,
                        "retry_attempts": retry_count
                    }

            except Exception as e:
                # Unexpected error
                error_msg = f"Unexpected error sending email: {str(e)}"
                self.logger.error(error_msg)
                return {
                    "status": "error",
                    "message": "Unexpected error",
                    "error": error_msg
                }

        # Should not reach here
        return {
            "status": "error",
            "message": "Unknown error",
            "error": "Email sending failed for unknown reason"
        }

    def _create_message(
        self,
        to_email: str,
        subject: str,
        html_body: Optional[str],
        text_body: Optional[str]
    ) -> MIMEMultipart:
        """
        Create MIME multipart message

        Args:
            to_email: Recipient email
            subject: Email subject
            html_body: HTML body (optional)
            text_body: Plain text body (optional)

        Returns:
            MIMEMultipart: Email message

        Note:
            If both html_body and text_body are provided, creates a multipart/alternative
            message with both formats. Email clients will display HTML if supported,
            otherwise fall back to plain text.
        """
        # Create multipart message
        message = MIMEMultipart('alternative')
        message['From'] = self.config.sender_email
        message['To'] = to_email
        message['Subject'] = subject

        # Add plain text part (if provided)
        if text_body:
            text_part = MIMEText(text_body, 'plain', 'utf-8')
            message.attach(text_part)

        # Add HTML part (if provided)
        if html_body:
            html_part = MIMEText(html_body, 'html', 'utf-8')
            message.attach(html_part)

        return message

    def _send_via_smtp(
        self,
        message: MIMEMultipart,
        to_email: str
    ) -> None:
        """
        Send message via SMTP

        Args:
            message: MIME message to send
            to_email: Recipient email address

        Raises:
            SMTPException: If SMTP operation fails
            ConnectionError: If connection fails
        """
        try:
            # Create SMTP connection
            with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port, timeout=30) as server:
                # Enable debug output (optional)
                # server.set_debuglevel(1)

                # Start TLS encryption (if enabled)
                if self.config.use_tls:
                    server.starttls()

                # Login
                server.login(self.config.sender_email, self.config.sender_password)

                # Send email
                server.send_message(message)

        except smtplib.SMTPException as e:
            # Re-raise SMTP errors
            raise

        except Exception as e:
            # Wrap other errors as ConnectionError
            raise ConnectionError(f"Failed to connect to SMTP server: {str(e)}")

    def test_connection(self) -> Dict[str, Any]:
        """
        Test SMTP connection and authentication

        Returns:
            dict: {
                "status": "success" | "error",
                "message": str,
                "error": str (if error)
            }

        Example:
            >>> result = sender.test_connection()
            >>> if result['status'] == 'success':
            ...     print("SMTP connection successful")
            ... else:
            ...     print(result['error'])
        """
        try:
            self.logger.info("Testing SMTP connection...")

            with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port, timeout=10) as server:
                # Start TLS
                if self.config.use_tls:
                    server.starttls()

                # Test login
                server.login(self.config.sender_email, self.config.sender_password)

            self.logger.info("✅ SMTP connection test successful")

            return {
                "status": "success",
                "message": f"Successfully connected to {self.config.smtp_host}:{self.config.smtp_port}"
            }

        except smtplib.SMTPAuthenticationError as e:
            error_msg = (
                "❌ SMTP authentication failed!\n\n"
                "Please verify your configuration:\n"
                f"1. SMTP Host: {self.config.smtp_host}\n"
                f"2. SMTP Port: {self.config.smtp_port}\n"
                f"3. Email: {self.config.sender_email}\n"
                f"4. Password: {'*' * len(self.config.sender_password)}\n\n"
                "For Gmail, ensure you're using an App Password:\n"
                "https://support.google.com/accounts/answer/185833\n\n"
                f"Error: {str(e)}"
            )
            self.logger.error(error_msg)
            return {
                "status": "error",
                "message": "Authentication failed",
                "error": error_msg
            }

        except Exception as e:
            error_msg = f"Connection test failed: {str(e)}"
            self.logger.error(error_msg)
            return {
                "status": "error",
                "message": "Connection failed",
                "error": error_msg
            }


# Convenience function
def send_email(
    to_email: str,
    subject: str,
    html_body: Optional[str] = None,
    text_body: Optional[str] = None,
    config: Optional[EmailConfig] = None
) -> Dict[str, Any]:
    """
    Convenience function to send email

    Args:
        to_email: Recipient email address
        subject: Email subject
        html_body: HTML body (optional)
        text_body: Plain text body (optional)
        config: Email configuration (optional, will use environment variables if not provided)

    Returns:
        dict: Send result

    Example:
        >>> result = send_email(
        ...     to_email="ray@example.com",
        ...     subject="Test Email",
        ...     html_body="<h1>Hello</h1>"
        ... )
    """
    if config is None:
        # Load from environment variables
        import os
        from dotenv import load_dotenv
        load_dotenv()

        config = EmailConfig(
            smtp_host=os.getenv('SMTP_HOST', 'smtp.gmail.com'),
            smtp_port=int(os.getenv('SMTP_PORT', '587')),
            sender_email=os.getenv('EMAIL_ACCOUNT', ''),
            sender_password=os.getenv('EMAIL_PASSWORD', ''),
            use_tls=os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
        )

    sender = EmailSender(config)
    return sender.send(to_email, subject, html_body, text_body)
