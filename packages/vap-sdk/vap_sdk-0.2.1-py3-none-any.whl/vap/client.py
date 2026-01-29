"""VAP SDK Client - Sync and Async implementations"""

from typing import Optional, Dict, Any, List, Union
import httpx

from vap.models import (
    VapResult,
    AccountInfo,
    PresetInfo,
    ExecuteRequest,
    ExecutionStatus,
    MediaOutput,
    MediaType,
)
from vap.exceptions import (
    VapError,
    VapAuthError,
    VapInsufficientFundsError,
    VapPresetNotFoundError,
    VapExecutionError,
    VapTimeoutError,
    VapRateLimitError,
)


DEFAULT_BASE_URL = "https://api.vap.studio/v3"
DEFAULT_TIMEOUT = 300.0  # 5 minutes for media generation


class BaseVapClient:
    """Base client with shared configuration"""
    
    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "vap-sdk-python/0.1.0",
        }
    
    def _handle_error(self, response: httpx.Response) -> None:
        """Handle API error responses"""
        status = response.status_code
        
        try:
            data = response.json()
            message = data.get("error", {}).get("message", response.text)
            error_code = data.get("error", {}).get("code", "")
        except Exception:
            message = response.text
            error_code = ""
        
        if status == 401:
            raise VapAuthError(message, status_code=status)
        elif status == 402:
            raise VapInsufficientFundsError(
                message,
                status_code=status,
                required=data.get("required"),
                available=data.get("available"),
            )
        elif status == 404:
            if "preset" in message.lower():
                raise VapPresetNotFoundError(message, status_code=status)
            raise VapError(message, status_code=status)
        elif status == 429:
            raise VapRateLimitError(
                message,
                status_code=status,
                retry_after=int(response.headers.get("Retry-After", 60)),
            )
        elif status >= 500:
            raise VapExecutionError(message, status_code=status)
        else:
            raise VapError(message, status_code=status)
    
    def _parse_result(self, data: Dict[str, Any]) -> VapResult:
        """Parse API response into VapResult"""
        from datetime import datetime
        
        outputs = []
        for out in data.get("outputs", []):
            outputs.append(MediaOutput(
                type=MediaType(out["type"]),
                url=out["url"],
                duration=out.get("duration"),
                size=out.get("size"),
                format=out.get("format"),
                metadata=out.get("metadata", {}),
            ))
        
        return VapResult(
            execution_id=data["execution_id"],
            status=ExecutionStatus(data["status"]),
            preset=data["preset"],
            cost=data.get("cost", 0),
            reserved_amount=data.get("reserved_amount"),
            burned_amount=data.get("burned_amount"),
            outputs=outputs,
            created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
            completed_at=datetime.fromisoformat(data["completed_at"].replace("Z", "+00:00")) if data.get("completed_at") else None,
            processing_time=data.get("processing_time"),
            metadata=data.get("metadata", {}),
        )


class VapClient(BaseVapClient):
    """
    Synchronous VAP Client
    
    Usage:
        client = VapClient(api_key="your-key")
        result = client.execute("streaming_campaign", text="Hello world")
        print(result.video_url)
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        super().__init__(api_key, base_url, timeout)
        self._client = httpx.Client(
            headers=self._get_headers(),
            timeout=timeout,
        )
    
    def __enter__(self) -> "VapClient":
        return self
    
    def __exit__(self, *args: Any) -> None:
        self.close()
    
    def close(self) -> None:
        """Close the HTTP client"""
        self._client.close()
    
    def execute(
        self,
        preset: str,
        *,
        text: Optional[str] = None,
        script: Optional[str] = None,
        image_prompt: Optional[str] = None,
        music_prompt: Optional[str] = None,
        voice: Optional[str] = None,
        style: Optional[str] = None,
        duration: Optional[int] = None,
        webhook_url: Optional[str] = None,
        wait: bool = True,
        **metadata: Any,
    ) -> VapResult:
        """
        Execute a media generation preset
        
        Args:
            preset: Preset name (e.g., "streaming_campaign", "video.basic")
            text: Text content for narration/script
            script: Full script (alternative to text)
            image_prompt: Prompt for image generation
            music_prompt: Prompt for music generation
            voice: Voice ID for narration
            style: Visual style preset
            duration: Target duration in seconds
            webhook_url: URL for completion callback
            wait: Wait for completion (default True)
            **metadata: Additional metadata
        
        Returns:
            VapResult with execution details and output URLs
        
        Raises:
            VapAuthError: Invalid API key
            VapInsufficientFundsError: Not enough balance
            VapPresetNotFoundError: Invalid preset name
            VapExecutionError: Generation failed
        """
        request = ExecuteRequest(
            preset=preset,
            text=text,
            script=script,
            image_prompt=image_prompt,
            music_prompt=music_prompt,
            voice=voice,
            style=style,
            duration=duration,
            webhook_url=webhook_url,
            metadata=metadata,
        )
        
        response = self._client.post(
            f"{self.base_url}/execute",
            json=request.model_dump(exclude_none=True),
        )
        
        if response.status_code >= 400:
            self._handle_error(response)
        
        data = response.json()
        result = self._parse_result(data)
        
        # If wait=True and not completed, poll for completion
        if wait and not result.is_completed and not result.is_failed:
            result = self.wait_for_completion(result.execution_id)
        
        return result
    
    def wait_for_completion(
        self,
        execution_id: str,
        poll_interval: float = 2.0,
        max_wait: float = 300.0,
    ) -> VapResult:
        """
        Poll for execution completion
        
        Args:
            execution_id: Execution ID to poll
            poll_interval: Seconds between polls
            max_wait: Maximum seconds to wait
        
        Returns:
            Completed VapResult
        
        Raises:
            VapTimeoutError: If max_wait exceeded
        """
        import time
        
        start = time.time()
        while time.time() - start < max_wait:
            result = self.get_execution(execution_id)
            if result.is_completed or result.is_failed:
                return result
            time.sleep(poll_interval)
        
        raise VapTimeoutError(
            f"Execution {execution_id} did not complete within {max_wait}s"
        )
    
    def get_execution(self, execution_id: str) -> VapResult:
        """Get execution status and result"""
        response = self._client.get(f"{self.base_url}/executions/{execution_id}")
        
        if response.status_code >= 400:
            self._handle_error(response)
        
        return self._parse_result(response.json())
    
    def get_account(self) -> AccountInfo:
        """Get account balance and info"""
        response = self._client.get(f"{self.base_url}/account")
        
        if response.status_code >= 400:
            self._handle_error(response)
        
        data = response.json()
        return AccountInfo(**data)
    
    def list_presets(self) -> List[PresetInfo]:
        """List available presets with pricing"""
        response = self._client.get(f"{self.base_url}/presets")
        
        if response.status_code >= 400:
            self._handle_error(response)
        
        return [PresetInfo(**p) for p in response.json()["presets"]]
    
    def estimate_cost(self, preset: str, **params: Any) -> float:
        """Estimate cost for an execution"""
        response = self._client.post(
            f"{self.base_url}/estimate",
            json={"preset": preset, **params},
        )
        
        if response.status_code >= 400:
            self._handle_error(response)
        
        return response.json()["estimated_cost"]


class AsyncVapClient(BaseVapClient):
    """
    Asynchronous VAP Client
    
    Usage:
        async with AsyncVapClient(api_key="your-key") as client:
            result = await client.execute("streaming_campaign", text="Hello world")
            print(result.video_url)
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        super().__init__(api_key, base_url, timeout)
        self._client = httpx.AsyncClient(
            headers=self._get_headers(),
            timeout=timeout,
        )
    
    async def __aenter__(self) -> "AsyncVapClient":
        return self
    
    async def __aexit__(self, *args: Any) -> None:
        await self.close()
    
    async def close(self) -> None:
        """Close the HTTP client"""
        await self._client.aclose()
    
    async def execute(
        self,
        preset: str,
        *,
        text: Optional[str] = None,
        script: Optional[str] = None,
        image_prompt: Optional[str] = None,
        music_prompt: Optional[str] = None,
        voice: Optional[str] = None,
        style: Optional[str] = None,
        duration: Optional[int] = None,
        webhook_url: Optional[str] = None,
        wait: bool = True,
        **metadata: Any,
    ) -> VapResult:
        """
        Execute a media generation preset (async)
        
        Args:
            preset: Preset name (e.g., "streaming_campaign", "video.basic")
            text: Text content for narration/script
            script: Full script (alternative to text)
            image_prompt: Prompt for image generation
            music_prompt: Prompt for music generation
            voice: Voice ID for narration
            style: Visual style preset
            duration: Target duration in seconds
            webhook_url: URL for completion callback
            wait: Wait for completion (default True)
            **metadata: Additional metadata
        
        Returns:
            VapResult with execution details and output URLs
        """
        request = ExecuteRequest(
            preset=preset,
            text=text,
            script=script,
            image_prompt=image_prompt,
            music_prompt=music_prompt,
            voice=voice,
            style=style,
            duration=duration,
            webhook_url=webhook_url,
            metadata=metadata,
        )
        
        response = await self._client.post(
            f"{self.base_url}/execute",
            json=request.model_dump(exclude_none=True),
        )
        
        if response.status_code >= 400:
            self._handle_error(response)
        
        data = response.json()
        result = self._parse_result(data)
        
        if wait and not result.is_completed and not result.is_failed:
            result = await self.wait_for_completion(result.execution_id)
        
        return result
    
    async def wait_for_completion(
        self,
        execution_id: str,
        poll_interval: float = 2.0,
        max_wait: float = 300.0,
    ) -> VapResult:
        """Poll for execution completion (async)"""
        import asyncio
        import time
        
        start = time.time()
        while time.time() - start < max_wait:
            result = await self.get_execution(execution_id)
            if result.is_completed or result.is_failed:
                return result
            await asyncio.sleep(poll_interval)
        
        raise VapTimeoutError(
            f"Execution {execution_id} did not complete within {max_wait}s"
        )
    
    async def get_execution(self, execution_id: str) -> VapResult:
        """Get execution status and result (async)"""
        response = await self._client.get(f"{self.base_url}/executions/{execution_id}")
        
        if response.status_code >= 400:
            self._handle_error(response)
        
        return self._parse_result(response.json())
    
    async def get_account(self) -> AccountInfo:
        """Get account balance and info (async)"""
        response = await self._client.get(f"{self.base_url}/account")
        
        if response.status_code >= 400:
            self._handle_error(response)
        
        data = response.json()
        return AccountInfo(**data)
    
    async def list_presets(self) -> List[PresetInfo]:
        """List available presets with pricing (async)"""
        response = await self._client.get(f"{self.base_url}/presets")
        
        if response.status_code >= 400:
            self._handle_error(response)
        
        return [PresetInfo(**p) for p in response.json()["presets"]]
    
    async def estimate_cost(self, preset: str, **params: Any) -> float:
        """Estimate cost for an execution (async)"""
        response = await self._client.post(
            f"{self.base_url}/estimate",
            json={"preset": preset, **params},
        )
        
        if response.status_code >= 400:
            self._handle_error(response)
        
        return response.json()["estimated_cost"]