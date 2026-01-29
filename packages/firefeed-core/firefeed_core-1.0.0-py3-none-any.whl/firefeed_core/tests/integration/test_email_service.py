import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from firefeed_core.email_service.sender import EmailSender, EmailConfig, EmailMessage


class TestEmailServiceIntegration:
    """Integration tests for email service."""
    
    @pytest.fixture
    def email_config(self):
        """Create email configuration for testing."""
        return EmailConfig(
            smtp_host="localhost",
            smtp_port=1025,  # MailHog default port
            smtp_username="",
            smtp_password="",
            smtp_use_tls=False,
            from_email="noreply@example.com",
            from_name="FireFeed"
        )
    
    @pytest.fixture
    def email_sender(self, email_config):
        """Create email sender for testing."""
        return EmailSender(config=email_config)
    
    @pytest.mark.asyncio
    async def test_email_sender_initialization(self, email_config):
        """Test email sender initialization."""
        sender = EmailSender(config=email_config)
        
        assert sender.config == email_config
        assert sender.smtp_host == email_config.smtp_host
        assert sender.smtp_port == email_config.smtp_port
        assert sender.smtp_username == email_config.smtp_username
        assert sender.smtp_password == email_config.smtp_password
        assert sender.smtp_use_tls == email_config.smtp_use_tls
        assert sender.from_email == email_config.from_email
        assert sender.from_name == email_config.from_name
    
    @pytest.mark.asyncio
    async def test_send_simple_email(self, email_sender):
        """Test sending a simple email."""
        message = EmailMessage(
            to_email="test@example.com",
            to_name="Test User",
            subject="Test Email",
            html_content="<html><body><h1>Hello World!</h1></body></html>",
            text_content="Hello World!"
        )
        
        # Mock SMTP to avoid actual email sending
        with patch('aiosmtplib.SMTP') as mock_smtp:
            mock_smtp_instance = AsyncMock()
            mock_smtp.return_value.__aenter__.return_value = mock_smtp_instance
            
            # Send email
            await email_sender.send_email(message)
            
            # Verify SMTP was called correctly
            mock_smtp.assert_called_once_with(
                hostname=email_sender.smtp_host,
                port=email_sender.smtp_port,
                use_tls=email_sender.smtp_use_tls
            )
            mock_smtp_instance.login.assert_called_once_with(
                email_sender.smtp_username,
                email_sender.smtp_password
            )
            mock_smtp_instance.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_email_with_attachments(self, email_sender):
        """Test sending email with attachments."""
        message = EmailMessage(
            to_email="test@example.com",
            to_name="Test User",
            subject="Email with Attachment",
            html_content="<html><body><h1>Check attachment</h1></body></html>",
            text_content="Check attachment"
        )
        
        # Add attachment
        message.attachments = [
            ("test.txt", "text/plain", b"This is test content")
        ]
        
        with patch('aiosmtplib.SMTP') as mock_smtp:
            mock_smtp_instance = AsyncMock()
            mock_smtp.return_value.__aenter__.return_value = mock_smtp_instance
            
            await email_sender.send_email(message)
            
            # Verify message was sent
            mock_smtp_instance.send_message.assert_called_once()
            sent_message = mock_smtp_instance.send_message.call_args[0][0]
            
            # Check if attachment was added
            assert len(sent_message.get_payload()) > 1
    
    @pytest.mark.asyncio
    async def test_send_email_with_multiple_recipients(self, email_sender):
        """Test sending email to multiple recipients."""
        message = EmailMessage(
            to_email="test@example.com",
            to_name="Test User",
            subject="Multiple Recipients",
            html_content="<html><body><h1>Multiple recipients test</h1></body></html>",
            text_content="Multiple recipients test"
        )
        
        # Add CC and BCC
        message.cc_emails = ["cc1@example.com", "cc2@example.com"]
        message.bcc_emails = ["bcc1@example.com", "bcc2@example.com"]
        
        with patch('aiosmtplib.SMTP') as mock_smtp:
            mock_smtp_instance = AsyncMock()
            mock_smtp.return_value.__aenter__.return_value = mock_smtp_instance
            
            await email_sender.send_email(message)
            
            # Verify message was sent
            mock_smtp_instance.send_message.assert_called_once()
            sent_message = mock_smtp_instance.send_message.call_args[0][0]
            
            # Check recipients
            assert sent_message["To"] == "test@example.com"
            assert sent_message["Cc"] == "cc1@example.com, cc2@example.com"
    
    @pytest.mark.asyncio
    async def test_send_verification_email_integration(self, email_sender):
        """Test sending verification email."""
        with patch.object(email_sender, 'send_email') as mock_send:
            mock_send.return_value = None
            
            # Send verification email
            await email_sender.send_verification_email(
                to_email="user@example.com",
                to_name="John Doe",
                verification_token="abc123"
            )
            
            # Verify send_email was called
            mock_send.assert_called_once()
            sent_message = mock_send.call_args[0][0]
            
            # Verify message content
            assert sent_message.to_email == "user@example.com"
            assert sent_message.to_name == "John Doe"
            assert sent_message.subject == "Verify your email"
            assert "abc123" in sent_message.html_content
    
    @pytest.mark.asyncio
    async def test_send_registration_success_email_integration(self, email_sender):
        """Test sending registration success email."""
        with patch.object(email_sender, 'send_email') as mock_send:
            mock_send.return_value = None
            
            # Send registration success email
            await email_sender.send_registration_success_email(
                to_email="user@example.com",
                to_name="John Doe"
            )
            
            # Verify send_email was called
            mock_send.assert_called_once()
            sent_message = mock_send.call_args[0][0]
            
            # Verify message content
            assert sent_message.to_email == "user@example.com"
            assert sent_message.to_name == "John Doe"
            assert sent_message.subject == "Registration successful"
    
    @pytest.mark.asyncio
    async def test_send_password_reset_email_integration(self, email_sender):
        """Test sending password reset email."""
        with patch.object(email_sender, 'send_email') as mock_send:
            mock_send.return_value = None
            
            # Send password reset email
            await email_sender.send_password_reset_email(
                to_email="user@example.com",
                to_name="John Doe",
                reset_token="reset123"
            )
            
            # Verify send_email was called
            mock_send.assert_called_once()
            sent_message = mock_send.call_args[0][0]
            
            # Verify message content
            assert sent_message.to_email == "user@example.com"
            assert sent_message.to_name == "John Doe"
            assert sent_message.subject == "Reset your password"
            assert "reset123" in sent_message.html_content
    
    @pytest.mark.asyncio
    async def test_email_sender_error_handling(self, email_sender):
        """Test email sender error handling."""
        message = EmailMessage(
            to_email="test@example.com",
            to_name="Test User",
            subject="Test Email",
            html_content="<html><body><h1>Hello World!</h1></body></html>",
            text_content="Hello World!"
        )
        
        # Test SMTP connection error
        with patch('aiosmtplib.SMTP') as mock_smtp:
            mock_smtp.side_effect = Exception("Connection failed")
            
            with pytest.raises(Exception, match="Connection failed"):
                await email_sender.send_email(message)
        
        # Test authentication error
        with patch('aiosmtplib.SMTP') as mock_smtp:
            mock_smtp_instance = AsyncMock()
            mock_smtp_instance.login.side_effect = Exception("Authentication failed")
            mock_smtp.return_value.__aenter__.return_value = mock_smtp_instance
            
            with pytest.raises(Exception, match="Authentication failed"):
                await email_sender.send_email(message)
    
    @pytest.mark.asyncio
    async def test_email_sender_concurrent_sending(self, email_sender):
        """Test sending multiple emails concurrently."""
        messages = []
        for i in range(3):
            message = EmailMessage(
                to_email=f"user{i}@example.com",
                to_name=f"User {i}",
                subject=f"Test Email {i}",
                html_content=f"<html><body><h1>Hello User {i}!</h1></body></html>",
                text_content=f"Hello User {i}!"
            )
            messages.append(message)
        
        with patch('aiosmtplib.SMTP') as mock_smtp:
            mock_smtp_instance = AsyncMock()
            mock_smtp.return_value.__aenter__.return_value = mock_smtp_instance
            
            # Send emails concurrently
            await asyncio.gather(*[
                email_sender.send_email(message) for message in messages
            ])
            
            # Verify SMTP was called for each email
            assert mock_smtp.call_count == 3
            assert mock_smtp_instance.send_message.call_count == 3
    
    @pytest.mark.asyncio
    async def test_email_sender_with_real_smtp_config(self):
        """Test email sender with real SMTP configuration."""
        # This test would require a real SMTP server
        # For now, we'll just test the configuration loading
        config = EmailConfig(
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_username="test@gmail.com",
            smtp_password="test_password",
            smtp_use_tls=True,
            from_email="noreply@gmail.com",
            from_name="FireFeed"
        )
        
        sender = EmailSender(config=config)
        
        assert sender.smtp_host == "smtp.gmail.com"
        assert sender.smtp_port == 587
        assert sender.smtp_username == "test@gmail.com"
        assert sender.smtp_password == "test_password"
        assert sender.smtp_use_tls is True
        assert sender.from_email == "noreply@gmail.com"
        assert sender.from_name == "FireFeed"