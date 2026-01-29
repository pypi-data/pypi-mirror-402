import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from jinja2 import Template
from aiosmtplib import SMTP
from firefeed_core.email_service.sender import EmailSender, EmailConfig, EmailTemplate, EmailMessage
from firefeed_core.email_service.templates import (
    VERIFICATION_EMAIL_TEMPLATE,
    REGISTRATION_SUCCESS_EMAIL_TEMPLATE,
    PASSWORD_RESET_EMAIL_TEMPLATE
)


class TestEmailConfig:
    """Test email configuration."""
    
    def test_email_config_creation(self):
        """Test email configuration creation."""
        config = EmailConfig(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_username="test@example.com",
            smtp_password="password",
            smtp_use_tls=True,
            from_email="noreply@example.com",
            from_name="FireFeed"
        )
        
        assert config.smtp_host == "smtp.example.com"
        assert config.smtp_port == 587
        assert config.smtp_username == "test@example.com"
        assert config.smtp_password == "password"
        assert config.smtp_use_tls is True
        assert config.from_email == "noreply@example.com"
        assert config.from_name == "FireFeed"


class TestEmailTemplate:
    """Test email templates."""
    
    def test_email_template_creation(self):
        """Test email template creation."""
        template = EmailTemplate(
            subject="Test Subject",
            html_content="<html><body><h1>Hello {{ name }}</h1></body></html>",
            text_content="Hello {{ name }}"
        )
        
        assert template.subject == "Test Subject"
        assert template.html_content == "<html><body><h1>Hello {{ name }}</h1></body></html>"
        assert template.text_content == "Hello {{ name }}"
    
    def test_email_template_render(self):
        """Test email template rendering."""
        template = EmailTemplate(
            subject="Welcome {{ name }}",
            html_content="<html><body><h1>Hello {{ name }}</h1></body></html>",
            text_content="Hello {{ name }}"
        )
        
        context = {"name": "John"}
        rendered = template.render(context)
        
        assert rendered.subject == "Welcome John"
        assert rendered.html_content == "<html><body><h1>Hello John</h1></body></html>"
        assert rendered.text_content == "Hello John"


class TestEmailMessage:
    """Test email message."""
    
    def test_email_message_creation(self):
        """Test email message creation."""
        message = EmailMessage(
            to_email="test@example.com",
            to_name="Test User",
            subject="Test Subject",
            html_content="<html><body><h1>Test</h1></body></html>",
            text_content="Test"
        )
        
        assert message.to_email == "test@example.com"
        assert message.to_name == "Test User"
        assert message.subject == "Test Subject"
        assert message.html_content == "<html><body><h1>Test</h1></body></html>"
        assert message.text_content == "Test"


class TestEmailSender:
    """Test email sender."""
    
    @pytest.fixture
    def email_config(self):
        """Create email configuration."""
        return EmailConfig(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_username="test@example.com",
            smtp_password="password",
            smtp_use_tls=True,
            from_email="noreply@example.com",
            from_name="FireFeed"
        )
    
    @pytest.fixture
    def email_sender(self, email_config):
        """Create email sender."""
        return EmailSender(config=email_config)
    
    @pytest.fixture
    def verification_template(self):
        """Create verification email template."""
        return EmailTemplate(
            subject="Verify your email",
            html_content=VERIFICATION_EMAIL_TEMPLATE["en"],
            text_content="Please verify your email"
        )
    
    @pytest.fixture
    def registration_template(self):
        """Create registration success email template."""
        return EmailTemplate(
            subject="Registration successful",
            html_content=REGISTRATION_SUCCESS_EMAIL_TEMPLATE["en"],
            text_content="Registration successful"
        )
    
    @pytest.fixture
    def password_reset_template(self):
        """Create password reset email template."""
        return EmailTemplate(
            subject="Reset your password",
            html_content=PASSWORD_RESET_EMAIL_TEMPLATE["en"],
            text_content="Reset your password"
        )
    
    @pytest.mark.asyncio
    async def test_send_email_success(self, email_sender, email_config):
        """Test successful email sending."""
        message = EmailMessage(
            to_email="test@example.com",
            to_name="Test User",
            subject="Test Subject",
            html_content="<html><body><h1>Test</h1></body></html>",
            text_content="Test"
        )
        
        with patch('aiosmtplib.SMTP') as mock_smtp:
            mock_smtp_instance = AsyncMock()
            mock_smtp.return_value.__aenter__.return_value = mock_smtp_instance
            
            await email_sender.send_email(message)
            
            mock_smtp.assert_called_once_with(
                hostname=email_config.smtp_host,
                port=email_config.smtp_port,
                use_tls=email_config.smtp_use_tls
            )
            mock_smtp_instance.login.assert_called_once_with(
                email_config.smtp_username,
                email_config.smtp_password
            )
            mock_smtp_instance.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_email_failure(self, email_sender):
        """Test email sending failure."""
        message = EmailMessage(
            to_email="test@example.com",
            to_name="Test User",
            subject="Test Subject",
            html_content="<html><body><h1>Test</h1></body></html>",
            text_content="Test"
        )
        
        with patch('aiosmtplib.SMTP') as mock_smtp:
            mock_smtp_instance = AsyncMock()
            mock_smtp_instance.login.side_effect = Exception("SMTP Error")
            mock_smtp.return_value.__aenter__.return_value = mock_smtp_instance
            
            with pytest.raises(Exception, match="SMTP Error"):
                await email_sender.send_email(message)
    
    @pytest.mark.asyncio
    async def test_send_verification_email(self, email_sender, verification_template):
        """Test sending verification email."""
        with patch.object(email_sender, 'send_email') as mock_send:
            mock_send.return_value = None
            
            await email_sender.send_verification_email(
                to_email="test@example.com",
                to_name="Test User",
                verification_token="token123"
            )
            
            mock_send.assert_called_once()
            sent_message = mock_send.call_args[0][0]
            
            assert sent_message.to_email == "test@example.com"
            assert sent_message.to_name == "Test User"
            assert sent_message.subject == "Verify your email"
            assert "token123" in sent_message.html_content
    
    @pytest.mark.asyncio
    async def test_send_registration_success_email(self, email_sender, registration_template):
        """Test sending registration success email."""
        with patch.object(email_sender, 'send_email') as mock_send:
            mock_send.return_value = None
            
            await email_sender.send_registration_success_email(
                to_email="test@example.com",
                to_name="Test User"
            )
            
            mock_send.assert_called_once()
            sent_message = mock_send.call_args[0][0]
            
            assert sent_message.to_email == "test@example.com"
            assert sent_message.to_name == "Test User"
            assert sent_message.subject == "Registration successful"
    
    @pytest.mark.asyncio
    async def test_send_password_reset_email(self, email_sender, password_reset_template):
        """Test sending password reset email."""
        with patch.object(email_sender, 'send_email') as mock_send:
            mock_send.return_value = None
            
            await email_sender.send_password_reset_email(
                to_email="test@example.com",
                to_name="Test User",
                reset_token="reset123"
            )
            
            mock_send.assert_called_once()
            sent_message = mock_send.call_args[0][0]
            
            assert sent_message.to_email == "test@example.com"
            assert sent_message.to_name == "Test User"
            assert sent_message.subject == "Reset your password"
            assert "reset123" in sent_message.html_content
    
    @pytest.mark.asyncio
    async def test_send_email_with_attachments(self, email_sender):
        """Test sending email with attachments."""
        message = EmailMessage(
            to_email="test@example.com",
            to_name="Test User",
            subject="Test Subject",
            html_content="<html><body><h1>Test</h1></body></html>",
            text_content="Test"
        )
        
        # Add attachment
        message.attachments = [
            ("test.txt", "text/plain", b"Test content")
        ]
        
        with patch('aiosmtplib.SMTP') as mock_smtp:
            mock_smtp_instance = AsyncMock()
            mock_smtp.return_value.__aenter__.return_value = mock_smtp_instance
            
            await email_sender.send_email(message)
            
            # Verify that the message was sent with attachments
            mock_smtp_instance.send_message.assert_called_once()
            sent_message = mock_smtp_instance.send_message.call_args[0][0]
            
            # Check if attachments were added
            assert len(sent_message.get_payload()) > 1  # Should have body + attachment
    
    @pytest.mark.asyncio
    async def test_send_email_with_multiple_recipients(self, email_sender):
        """Test sending email to multiple recipients."""
        message = EmailMessage(
            to_email="test@example.com",
            to_name="Test User",
            subject="Test Subject",
            html_content="<html><body><h1>Test</h1></body></html>",
            text_content="Test"
        )
        
        # Add CC and BCC
        message.cc_emails = ["cc@example.com"]
        message.bcc_emails = ["bcc@example.com"]
        
        with patch('aiosmtplib.SMTP') as mock_smtp:
            mock_smtp_instance = AsyncMock()
            mock_smtp.return_value.__aenter__.return_value = mock_smtp_instance
            
            await email_sender.send_email(message)
            
            mock_smtp_instance.send_message.assert_called_once()
            sent_message = mock_smtp_instance.send_message.call_args[0][0]
            
            # Check if CC and BCC were added
            assert "cc@example.com" in sent_message.get_all("Cc", [])
            assert "bcc@example.com" in sent_message.get_all("Bcc", [])