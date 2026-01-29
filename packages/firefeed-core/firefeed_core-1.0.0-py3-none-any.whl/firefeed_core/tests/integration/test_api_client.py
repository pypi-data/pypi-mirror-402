"""
Tests for FireFeed Core API Client
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from firefeed_core.api_client import APIClient, APIException, AuthenticationException


class TestAPIClient:
    """Test cases for APIClient"""
    
    @pytest.fixture
    def valid_token(self):
        """Generate a valid JWT token for testing"""
        import jwt
        import time
        
        payload = {
            "iss": "firefeed-api",
            "sub": "test-service",
            "aud": ["firefeed-services"],
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,  # 1 hour
            "scope": ["test:read", "test:write"]
        }
        return jwt.encode(payload, "test-secret", algorithm="HS256")
    
    @pytest.fixture
    def expired_token(self):
        """Generate an expired JWT token for testing"""
        import jwt
        import time
        
        payload = {
            "iss": "firefeed-api",
            "sub": "test-service",
            "aud": ["firefeed-services"],
            "iat": int(time.time()) - 7200,  # 2 hours ago
            "exp": int(time.time()) - 3600,  # 1 hour ago
            "scope": ["test:read"]
        }
        return jwt.encode(payload, "test-secret", algorithm="HS256")
    
    @pytest.mark.asyncio
    async def test_client_initialization(self):
        """Test APIClient initialization"""
        client = APIClient(
            base_url="http://test-api:8000",
            token="test-token",
            service_id="test-service"
        )
        
        assert client.base_url == "http://test-api:8000"
        assert client.token == "test-token"
        assert client.service_id == "test-service"
        assert client.timeout == 30
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_client_context_manager(self):
        """Test APIClient as async context manager"""
        async with APIClient(
            base_url="http://test-api:8000",
            token="test-token",
            service_id="test-service"
        ) as client:
            assert client.base_url == "http://test-api:8000"
        # Client should be closed automatically
    
    @pytest.mark.asyncio
    async def test_token_validation(self, valid_token, expired_token):
        """Test token validation"""
        # Test valid token
        client = APIClient(
            base_url="http://test-api:8000",
            token=valid_token,
            service_id="test-service"
        )
        
        # Should not raise exception for valid token
        assert client._validate_token() == valid_token
        
        # Test expired token
        client_expired = APIClient(
            base_url="http://test-api:8000",
            token=expired_token,
            service_id="test-service"
        )
        
        # Should raise AuthenticationException for expired token
        with pytest.raises(AuthenticationException):
            client_expired._validate_token()
    
    @pytest.mark.asyncio
    async def test_headers_generation(self, valid_token):
        """Test header generation"""
        client = APIClient(
            base_url="http://test-api:8000",
            token=valid_token,
            service_id="test-service"
        )
        
        headers = client._get_headers()
        
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Bearer ")
        assert "X-Service-ID" in headers
        assert headers["X-Service-ID"] == "test-service"
        assert "Content-Type" in headers
        assert headers["Content-Type"] == "application/json"
    
    @pytest.mark.asyncio
    async def test_get_request(self, valid_token):
        """Test GET request"""
        client = APIClient(
            base_url="http://test-api:8000",
            token=valid_token,
            service_id="test-service"
        )
        
        # Mock httpx response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_response.content = b'{"data": "test"}'
        
        with patch.object(client.client, 'request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            result = await client.get("/api/v1/test")
            
            assert result == {"data": "test"}
            mock_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_post_request(self, valid_token):
        """Test POST request"""
        client = APIClient(
            base_url="http://test-api:8000",
            token=valid_token,
            service_id="test-service"
        )
        
        # Mock httpx response
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": 123, "message": "created"}
        mock_response.content = b'{"id": 123, "message": "created"}'
        
        with patch.object(client.client, 'request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            result = await client.post("/api/v1/test", json_data={"name": "test"})
            
            assert result == {"id": 123, "message": "created"}
    
    @pytest.mark.asyncio
    async def test_error_response_handling(self, valid_token):
        """Test HTTP error response handling"""
        client = APIClient(
            base_url="http://test-api:8000",
            token=valid_token,
            service_id="test-service"
        )
        
        # Mock 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {
            "error": {"message": "Not found"}
        }
        mock_response.content = b'{"error": {"message": "Not found"}}'
        
        with patch.object(client.client, 'request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            with pytest.raises(APIException) as exc_info:
                await client.get("/api/v1/nonexistent")
            
            assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_integration(self, valid_token):
        """Test circuit breaker integration"""
        client = APIClient(
            base_url="http://test-api:8000",
            token=valid_token,
            service_id="test-service",
            circuit_breaker_failure_threshold=2
        )
        
        # Mock failed responses to trigger circuit breaker
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": "Server error"}
        mock_response.content = b'{"error": "Server error"}'
        
        with patch.object(client.client, 'request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            # First request should fail
            with pytest.raises(APIException):
                await client.get("/api/v1/test")
            
            # Second request should also fail
            with pytest.raises(APIException):
                await client.get("/api/v1/test")
            
            # Third request should be blocked by circuit breaker
            with pytest.raises(APIException) as exc_info:
                await client.get("/api/v1/test")
            
            # Should be circuit breaker open exception
            assert "Circuit breaker is open" in str(exc_info.value)
    
    def test_client_stats(self, valid_token):
        """Test client statistics"""
        client = APIClient(
            base_url="http://test-api:8000",
            token=valid_token,
            service_id="test-service"
        )
        
        stats = client.get_stats()
        
        assert "service_id" in stats
        assert "base_url" in stats
        assert "circuit_breaker" in stats
        assert "rate_limiter" in stats
        assert "retry_policy" in stats
        
        assert stats["service_id"] == "test-service"
        assert stats["base_url"] == "http://test-api:8000"
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, valid_token):
        """Test successful health check"""
        client = APIClient(
            base_url="http://test-api:8000",
            token=valid_token,
            service_id="test-service"
        )
        
        # Mock healthy response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "healthy"}
        mock_response.content = b'{"status": "healthy"}'
        
        with patch.object(client.client, 'request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            result = await client.health_check()
            assert result is True
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, valid_token):
        """Test failed health check"""
        client = APIClient(
            base_url="http://test-api:8000",
            token=valid_token,
            service_id="test-service"
        )
        
        # Mock unhealthy response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "unhealthy"}
        mock_response.content = b'{"status": "unhealthy"}'
        
        with patch.object(client.client, 'request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            result = await client.health_check()
            assert result is False


if __name__ == "__main__":
    pytest.main([__file__])