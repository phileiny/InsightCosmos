"""
Unit Tests for Email Sender

測試 EmailSender 類的所有功能，包括 SMTP 發送、錯誤處理、重試機制等。

測試涵蓋範圍:
    - HTML Email 成功發送
    - 純文字 Email 成功發送
    - HTML + Text 混合格式
    - 認證失敗處理
    - 連線錯誤處理
    - 重試機制
    - 無效收件者
    - 缺少內容錯誤
    - 連線測試

執行方式:
    pytest tests/unit/test_email_sender.py -v
    pytest tests/unit/test_email_sender.py::TestEmailSenderSend -v
"""

import pytest
import smtplib
from unittest.mock import Mock, patch, MagicMock
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.tools.email_sender import EmailSender, EmailConfig, send_email


class TestEmailConfig:
    """Test EmailConfig dataclass"""

    def test_email_config_default_values(self):
        """測試 EmailConfig 預設值"""
        config = EmailConfig(
            sender_email="test@example.com",
            sender_password="password123"
        )

        assert config.smtp_host == "smtp.gmail.com"
        assert config.smtp_port == 587
        assert config.use_tls is True
        assert config.sender_email == "test@example.com"
        assert config.sender_password == "password123"

    def test_email_config_custom_values(self):
        """測試 EmailConfig 自定義值"""
        config = EmailConfig(
            smtp_host="smtp.custom.com",
            smtp_port=465,
            sender_email="custom@example.com",
            sender_password="custom_pass",
            use_tls=False
        )

        assert config.smtp_host == "smtp.custom.com"
        assert config.smtp_port == 465
        assert config.use_tls is False

    def test_email_config_missing_sender_email(self):
        """測試缺少 sender_email 時拋出錯誤"""
        with pytest.raises(ValueError, match="sender_email is required"):
            EmailConfig(
                sender_email="",
                sender_password="password"
            )

    def test_email_config_missing_password(self):
        """測試缺少 sender_password 時拋出錯誤"""
        with pytest.raises(ValueError, match="sender_password is required"):
            EmailConfig(
                sender_email="test@example.com",
                sender_password=""
            )


class TestEmailSenderInitialization:
    """Test EmailSender initialization"""

    def test_email_sender_initialization(self):
        """測試 EmailSender 初始化"""
        config = EmailConfig(
            sender_email="test@example.com",
            sender_password="password123"
        )

        sender = EmailSender(config)

        assert sender.config == config
        assert sender.logger is not None


class TestEmailSenderSend:
    """Test EmailSender.send method"""

    @pytest.fixture
    def email_config(self):
        """建立測試用 EmailConfig"""
        return EmailConfig(
            sender_email="test@example.com",
            sender_password="test_password"
        )

    @pytest.fixture
    def email_sender(self, email_config):
        """建立測試用 EmailSender"""
        return EmailSender(email_config)

    def test_send_html_email_success(self, email_sender):
        """測試成功發送 HTML Email"""
        with patch('smtplib.SMTP') as mock_smtp:
            # Mock SMTP instance
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            result = email_sender.send(
                to_email="recipient@example.com",
                subject="Test HTML Email",
                html_body="<html><body><h1>Test</h1></body></html>"
            )

            # 驗證結果
            assert result['status'] == 'success'
            assert 'Email sent to recipient@example.com' in result['message']

            # 驗證 SMTP 調用
            mock_smtp.assert_called_once_with('smtp.gmail.com', 587, timeout=30)
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once_with('test@example.com', 'test_password')
            mock_server.send_message.assert_called_once()

    def test_send_text_email_success(self, email_sender):
        """測試成功發送純文字 Email"""
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            result = email_sender.send(
                to_email="recipient@example.com",
                subject="Test Text Email",
                text_body="This is a plain text email."
            )

            assert result['status'] == 'success'
            mock_server.send_message.assert_called_once()

    def test_send_multipart_email(self, email_sender):
        """測試發送 HTML + Text 混合格式 Email"""
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            result = email_sender.send(
                to_email="recipient@example.com",
                subject="Test Multipart Email",
                html_body="<html><body><p>HTML version</p></body></html>",
                text_body="Plain text version"
            )

            assert result['status'] == 'success'
            mock_server.send_message.assert_called_once()

            # 驗證發送的訊息包含兩個部分
            call_args = mock_server.send_message.call_args
            message = call_args[0][0]
            assert isinstance(message, MIMEMultipart)

    def test_send_email_authentication_failed(self, email_sender):
        """測試 SMTP 認證失敗處理"""
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            # Mock authentication error
            mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, b'Authentication failed')

            result = email_sender.send(
                to_email="recipient@example.com",
                subject="Test Email",
                html_body="<html><body>Test</body></html>"
            )

            # 驗證錯誤處理
            assert result['status'] == 'error'
            assert result['message'] == 'Authentication failed'
            assert 'authentication failed' in result['error'].lower()
            assert 'APP PASSWORD' in result['error'].upper()

    def test_send_email_connection_error(self, email_sender):
        """測試連線錯誤處理"""
        with patch('smtplib.SMTP') as mock_smtp:
            # Mock connection error
            mock_smtp.side_effect = ConnectionError("Failed to connect to SMTP server")

            result = email_sender.send(
                to_email="recipient@example.com",
                subject="Test Email",
                html_body="<html><body>Test</body></html>",
                retry_count=1  # 限制重試次數以加快測試
            )

            # 驗證錯誤處理
            assert result['status'] == 'error'
            assert 'Failed after 1 retries' in result['message']
            assert result['retry_attempts'] == 1

    def test_send_email_retry_mechanism(self, email_sender):
        """測試重試機制（前 2 次失敗，第 3 次成功）"""
        with patch('smtplib.SMTP') as mock_smtp:
            with patch('time.sleep'):  # Mock sleep to speed up test
                mock_server = MagicMock()

                # 前兩次失敗，第三次成功
                call_count = 0

                def smtp_side_effect(*args, **kwargs):
                    nonlocal call_count
                    call_count += 1
                    if call_count <= 2:
                        raise ConnectionError("Connection failed")
                    return MagicMock(__enter__=MagicMock(return_value=mock_server))

                mock_smtp.side_effect = smtp_side_effect

                result = email_sender.send(
                    to_email="recipient@example.com",
                    subject="Test Email",
                    html_body="<html><body>Test</body></html>",
                    retry_count=3
                )

                # 驗證成功（第 3 次重試成功）
                assert result['status'] == 'success'
                assert result['retry_attempts'] == 2  # 第 3 次成功，所以重試了 2 次

    def test_send_email_invalid_recipient(self, email_sender):
        """測試無效收件者 Email 格式"""
        result = email_sender.send(
            to_email="invalid-email-without-at",
            subject="Test Email",
            html_body="<html><body>Test</body></html>"
        )

        # 驗證錯誤處理（在實際發送前檢查）
        assert result['status'] == 'error'
        assert 'Invalid recipient email' in result['message']
        assert 'Invalid email format' in result['error']

    def test_send_email_no_body(self, email_sender):
        """測試缺少 html_body 和 text_body 時拋出錯誤"""
        with pytest.raises(ValueError, match="At least one of html_body or text_body must be provided"):
            email_sender.send(
                to_email="recipient@example.com",
                subject="Test Email",
                html_body=None,
                text_body=None
            )

    def test_send_email_recipient_refused(self, email_sender):
        """測試收件者被拒絕的情況"""
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            # Mock recipient refused error
            mock_server.send_message.side_effect = smtplib.SMTPRecipientsRefused({
                'recipient@example.com': (550, b'User not found')
            })

            result = email_sender.send(
                to_email="recipient@example.com",
                subject="Test Email",
                html_body="<html><body>Test</body></html>"
            )

            # 驗證錯誤處理
            assert result['status'] == 'error'
            assert result['message'] == 'Recipient refused'
            assert 'refused' in result['error'].lower()


class TestEmailSenderConnection:
    """Test EmailSender.test_connection method"""

    @pytest.fixture
    def email_config(self):
        return EmailConfig(
            sender_email="test@example.com",
            sender_password="test_password"
        )

    @pytest.fixture
    def email_sender(self, email_config):
        return EmailSender(email_config)

    def test_test_connection_success(self, email_sender):
        """測試連線測試成功"""
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            result = email_sender.test_connection()

            # 驗證成功
            assert result['status'] == 'success'
            assert 'Successfully connected' in result['message']
            assert 'smtp.gmail.com:587' in result['message']

            # 驗證 SMTP 調用
            mock_smtp.assert_called_once_with('smtp.gmail.com', 587, timeout=10)
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once_with('test@example.com', 'test_password')

    def test_test_connection_failed(self, email_sender):
        """測試連線測試失敗"""
        with patch('smtplib.SMTP') as mock_smtp:
            # Mock connection error
            mock_smtp.side_effect = Exception("Connection timeout")

            result = email_sender.test_connection()

            # 驗證錯誤
            assert result['status'] == 'error'
            assert result['message'] == 'Connection failed'
            assert 'Connection timeout' in result['error']

    def test_test_connection_authentication_failed(self, email_sender):
        """測試連線測試時認證失敗"""
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            # Mock authentication error
            mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, b'Invalid credentials')

            result = email_sender.test_connection()

            # 驗證錯誤
            assert result['status'] == 'error'
            assert result['message'] == 'Authentication failed'
            assert 'authentication failed' in result['error'].lower()
            assert 'App Password' in result['error']


class TestEmailSenderCreateMessage:
    """Test EmailSender._create_message method"""

    @pytest.fixture
    def email_sender(self):
        config = EmailConfig(
            sender_email="test@example.com",
            sender_password="test_password"
        )
        return EmailSender(config)

    def test_create_message_html_only(self, email_sender):
        """測試創建僅 HTML 的訊息"""
        message = email_sender._create_message(
            to_email="recipient@example.com",
            subject="Test Subject",
            html_body="<html><body><h1>Test</h1></body></html>",
            text_body=None
        )

        assert isinstance(message, MIMEMultipart)
        assert message['From'] == "test@example.com"
        assert message['To'] == "recipient@example.com"
        assert message['Subject'] == "Test Subject"

        # 驗證包含 HTML 部分
        payload = message.get_payload()
        assert len(payload) == 1
        assert payload[0].get_content_type() == 'text/html'

    def test_create_message_text_only(self, email_sender):
        """測試創建僅純文字的訊息"""
        message = email_sender._create_message(
            to_email="recipient@example.com",
            subject="Test Subject",
            html_body=None,
            text_body="Plain text content"
        )

        assert isinstance(message, MIMEMultipart)

        # 驗證包含純文字部分
        payload = message.get_payload()
        assert len(payload) == 1
        assert payload[0].get_content_type() == 'text/plain'

    def test_create_message_multipart(self, email_sender):
        """測試創建 HTML + Text 混合訊息"""
        message = email_sender._create_message(
            to_email="recipient@example.com",
            subject="Test Subject",
            html_body="<html><body><p>HTML</p></body></html>",
            text_body="Plain text"
        )

        # 驗證包含兩個部分（先 text 後 html）
        payload = message.get_payload()
        assert len(payload) == 2
        assert payload[0].get_content_type() == 'text/plain'
        assert payload[1].get_content_type() == 'text/html'


class TestConvenienceFunction:
    """Test send_email convenience function"""

    def test_send_email_with_config(self):
        """測試使用自定義 config 的便利函式"""
        config = EmailConfig(
            sender_email="test@example.com",
            sender_password="test_password"
        )

        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            result = send_email(
                to_email="recipient@example.com",
                subject="Test Email",
                html_body="<html><body>Test</body></html>",
                config=config
            )

            assert result['status'] == 'success'

    def test_send_email_from_env(self):
        """測試從環境變數載入 config 的便利函式"""
        with patch('os.getenv') as mock_getenv:
            # Mock environment variables
            mock_getenv.side_effect = lambda key, default='': {
                'SMTP_HOST': 'smtp.test.com',
                'SMTP_PORT': '587',
                'EMAIL_ACCOUNT': 'test@example.com',
                'EMAIL_PASSWORD': 'test_password',
                'SMTP_USE_TLS': 'true'
            }.get(key, default)

            with patch('smtplib.SMTP') as mock_smtp:
                mock_server = MagicMock()
                mock_smtp.return_value.__enter__.return_value = mock_server

                result = send_email(
                    to_email="recipient@example.com",
                    subject="Test Email",
                    html_body="<html><body>Test</body></html>"
                )

                assert result['status'] == 'success'


def test_module_imports():
    """測試模組可以正確匯入"""
    from src.tools.email_sender import EmailSender, EmailConfig, send_email

    assert EmailSender is not None
    assert EmailConfig is not None
    assert send_email is not None
