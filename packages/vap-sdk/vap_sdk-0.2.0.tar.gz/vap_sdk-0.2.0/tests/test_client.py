"""Tests for VAP SDK Client"""

import pytest
import httpx
import respx
from datetime import datetime, timezone

from vap import (
    VapClient,
    AsyncVapClient,
    VapResult,
    VapError,
    VapAuthError,
    VapInsufficientFundsError,
    VapPresetNotFoundError,
)


# Test fixtures
@pytest.fixture
def api_key():
    return "test-api-key-12345"


@pytest.fixture
def base_url():
    return "https://api.vap.studio/v3"


@pytest.fixture
def mock_execution_response():
    return {
        "execution_id": "exec_123456",
        "status": "completed",
        "preset": "streaming_campaign",
        "cost": 5.90,
        "reserved_amount": 5.90,
        "burned_amount": 5.90,
        "outputs": [
            {
                "type": "video",
                "url": "https://cdn.vap.studio/videos/exec_123456.mp4",
                "duration": 30.5,
                "size": 15000000,
                "format": "mp4",
                "metadata": {}
            },
            {
                "type": "audio",
                "url": "https://cdn.vap.studio/audio/exec_123456.mp3",
                "duration": 30.5,
                "format": "mp3",
                "metadata": {}
            }
        ],
        "created_at": "2024-01-15T10:00:00Z",
        "completed_at": "2024-01-15T10:00:45Z",
        "processing_time": 45.0,
        "metadata": {"source": "test"}
    }


@pytest.fixture
def mock_account_response():
    return {
        "balance": 100.50,
        "currency": "USD",
        "tier": "pro",
        "executions_today": 5,
        "daily_limit": 100
    }


class TestVapClient:
    """Tests for synchronous VapClient"""
    
    @respx.mock
    def test_execute_success(self, api_key, base_url, mock_execution_response):
        """Test successful execution"""
        respx.post(f"{base_url}/execute").mock(
            return_value=httpx.Response(200, json=mock_execution_response)
        )
        
        client = VapClient(api_key=api_key)
        result = client.execute("streaming_campaign", text="Test video")
        
        assert result.execution_id == "exec_123456"
        assert result.status.value == "completed"
        assert result.cost == 5.90
        assert result.video_url == "https://cdn.vap.studio/videos/exec_123456.mp4"
        assert result.is_completed
        
        client.close()
    
    @respx.mock
    def test_execute_with_all_params(self, api_key, base_url, mock_execution_response):
        """Test execution with all parameters"""
        respx.post(f"{base_url}/execute").mock(
            return_value=httpx.Response(200, json=mock_execution_response)
        )
        
        with VapClient(api_key=api_key) as client:
            result = client.execute(
                "streaming_campaign",
                text="Test content",
                image_prompt="A beautiful sunset",
                music_prompt="Upbeat electronic",
                voice="professional_male",
                style="corporate",
                duration=30
            )
            
            assert result.is_completed
    
    @respx.mock
    def test_auth_error(self, api_key, base_url):
        """Test authentication error handling"""
        respx.post(f"{base_url}/execute").mock(
            return_value=httpx.Response(401, json={
                "error": {"message": "Invalid API key", "code": "auth_error"}
            })
        )
        
        client = VapClient(api_key="invalid-key")
        
        with pytest.raises(VapAuthError) as exc_info:
            client.execute("streaming_campaign", text="Test")
        
        assert exc_info.value.status_code == 401
        client.close()
    
    @respx.mock
    def test_insufficient_funds_error(self, api_key, base_url):
        """Test insufficient funds error handling"""
        respx.post(f"{base_url}/execute").mock(
            return_value=httpx.Response(402, json={
                "error": {"message": "Insufficient balance"},
                "required": 5.90,
                "available": 2.50
            })
        )
        
        client = VapClient(api_key=api_key)
        
        with pytest.raises(VapInsufficientFundsError) as exc_info:
            client.execute("streaming_campaign", text="Test")
        
        assert exc_info.value.required == 5.90
        assert exc_info.value.available == 2.50
        client.close()
    
    @respx.mock
    def test_preset_not_found_error(self, api_key, base_url):
        """Test preset not found error handling"""
        respx.post(f"{base_url}/execute").mock(
            return_value=httpx.Response(404, json={
                "error": {"message": "Preset 'invalid_preset' not found"}
            })
        )
        
        client = VapClient(api_key=api_key)
        
        with pytest.raises(VapPresetNotFoundError):
            client.execute("invalid_preset", text="Test")
        
        client.close()
    
    @respx.mock
    def test_get_account(self, api_key, base_url, mock_account_response):
        """Test getting account info"""
        respx.get(f"{base_url}/account").mock(
            return_value=httpx.Response(200, json=mock_account_response)
        )
        
        with VapClient(api_key=api_key) as client:
            account = client.get_account()
            
            assert account.balance == 100.50
            assert account.tier == "pro"
            assert account.executions_today == 5
    
    @respx.mock
    def test_get_execution(self, api_key, base_url, mock_execution_response):
        """Test getting execution status"""
        exec_id = "exec_123456"
        respx.get(f"{base_url}/executions/{exec_id}").mock(
            return_value=httpx.Response(200, json=mock_execution_response)
        )
        
        with VapClient(api_key=api_key) as client:
            result = client.get_execution(exec_id)
            
            assert result.execution_id == exec_id
            assert result.is_completed
    
    @respx.mock
    def test_list_presets(self, api_key, base_url):
        """Test listing presets"""
        respx.get(f"{base_url}/presets").mock(
            return_value=httpx.Response(200, json={
                "presets": [
                    {
                        "name": "streaming_campaign",
                        "description": "Full video campaign",
                        "price": 5.90,
                        "media_type": "video",
                        "features": ["video", "music", "narration"]
                    },
                    {
                        "name": "video.basic",
                        "description": "Basic video",
                        "price": 1.90,
                        "media_type": "video",
                        "features": ["video"]
                    }
                ]
            })
        )
        
        with VapClient(api_key=api_key) as client:
            presets = client.list_presets()
            
            assert len(presets) == 2
            assert presets[0].name == "streaming_campaign"
            assert presets[0].price == 5.90
    
    @respx.mock
    def test_estimate_cost(self, api_key, base_url):
        """Test cost estimation"""
        respx.post(f"{base_url}/estimate").mock(
            return_value=httpx.Response(200, json={"estimated_cost": 5.90})
        )
        
        with VapClient(api_key=api_key) as client:
            cost = client.estimate_cost("streaming_campaign")
            
            assert cost == 5.90
    
    def test_context_manager(self, api_key):
        """Test client as context manager"""
        with VapClient(api_key=api_key) as client:
            assert client.api_key == api_key
        # Client should be closed after context


class TestAsyncVapClient:
    """Tests for asynchronous AsyncVapClient"""
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_async_execute_success(self, api_key, base_url, mock_execution_response):
        """Test successful async execution"""
        respx.post(f"{base_url}/execute").mock(
            return_value=httpx.Response(200, json=mock_execution_response)
        )
        
        async with AsyncVapClient(api_key=api_key) as client:
            result = await client.execute("streaming_campaign", text="Test video")
            
            assert result.execution_id == "exec_123456"
            assert result.is_completed
            assert result.video_url is not None
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_async_get_account(self, api_key, base_url, mock_account_response):
        """Test async account info"""
        respx.get(f"{base_url}/account").mock(
            return_value=httpx.Response(200, json=mock_account_response)
        )
        
        async with AsyncVapClient(api_key=api_key) as client:
            account = await client.get_account()
            
            assert account.balance == 100.50
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_async_auth_error(self, api_key, base_url):
        """Test async auth error handling"""
        respx.post(f"{base_url}/execute").mock(
            return_value=httpx.Response(401, json={
                "error": {"message": "Invalid API key"}
            })
        )
        
        async with AsyncVapClient(api_key="invalid") as client:
            with pytest.raises(VapAuthError):
                await client.execute("streaming_campaign", text="Test")


class TestVapResult:
    """Tests for VapResult model"""
    
    def test_result_properties(self, mock_execution_response):
        """Test VapResult convenience properties"""
        from vap.models import VapResult, MediaOutput, MediaType, ExecutionStatus
        
        result = VapResult(
            execution_id="exec_123",
            status=ExecutionStatus.COMPLETED,
            preset="streaming_campaign",
            cost=5.90,
            outputs=[
                MediaOutput(type=MediaType.VIDEO, url="https://example.com/video.mp4"),
                MediaOutput(type=MediaType.AUDIO, url="https://example.com/audio.mp3"),
                MediaOutput(type=MediaType.IMAGE, url="https://example.com/image.png"),
            ],
            created_at=datetime.now(timezone.utc),
        )
        
        assert result.video_url == "https://example.com/video.mp4"
        assert result.audio_url == "https://example.com/audio.mp3"
        assert result.image_url == "https://example.com/image.png"
        assert result.is_completed
        assert not result.is_failed
    
    def test_result_failed_status(self):
        """Test failed execution status"""
        from vap.models import VapResult, ExecutionStatus
        
        result = VapResult(
            execution_id="exec_fail",
            status=ExecutionStatus.FAILED,
            preset="video.basic",
            cost=0,
            created_at=datetime.now(timezone.utc),
        )
        
        assert result.is_failed
        assert not result.is_completed
        assert result.video_url is None


class TestExceptions:
    """Tests for exception classes"""
    
    def test_vap_error_attributes(self):
        """Test VapError has correct attributes"""
        error = VapError("Test error", status_code=500, response_data={"key": "value"})
        
        assert error.message == "Test error"
        assert error.status_code == 500
        assert error.response_data == {"key": "value"}
        assert str(error) == "Test error"
    
    def test_insufficient_funds_error_attributes(self):
        """Test VapInsufficientFundsError attributes"""
        error = VapInsufficientFundsError(
            "Not enough balance",
            required=10.0,
            available=5.0,
            status_code=402
        )
        
        assert error.required == 10.0
        assert error.available == 5.0
        assert error.status_code == 402