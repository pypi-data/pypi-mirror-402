"""VAP SDK Data Models"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class ExecutionStatus(str, Enum):
    """Execution status states"""
    PENDING = "pending"
    RESERVED = "reserved"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class MediaType(str, Enum):
    """Supported media types"""
    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"
    MUSIC = "music"


class VapPreset(str, Enum):
    """Available VAP presets with pricing"""
    # Video Presets
    STREAMING_CAMPAIGN = "streaming_campaign"  # $5.90
    FULL_PRODUCTION = "full_production"        # $7.90
    VIDEO_BASIC = "video.basic"                # $1.90
    
    # Audio Presets
    MUSIC_BASIC = "music.basic"                # $0.59
    AUDIO_NARRATION = "audio.narration"        # $0.39
    
    # Image Presets
    IMAGE_BASIC = "image.basic"                # $0.29
    IMAGE_HD = "image.hd"                      # $0.49


class PresetInfo(BaseModel):
    """Preset information"""
    name: str
    description: str
    price: float
    media_type: MediaType
    estimated_duration: Optional[int] = None  # seconds
    features: List[str] = Field(default_factory=list)


class AccountInfo(BaseModel):
    """Account balance and info"""
    balance: float
    currency: str = "USD"
    tier: str = "standard"
    executions_today: int = 0
    daily_limit: Optional[int] = None


class MediaOutput(BaseModel):
    """Single media output"""
    type: MediaType
    url: str
    duration: Optional[float] = None  # seconds for video/audio
    size: Optional[int] = None  # bytes
    format: Optional[str] = None  # mp4, mp3, png, etc.
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VapResult(BaseModel):
    """Execution result from VAP API"""
    execution_id: str
    status: ExecutionStatus
    preset: str
    
    # Financial
    cost: float
    reserved_amount: Optional[float] = None
    burned_amount: Optional[float] = None
    
    # Outputs
    outputs: List[MediaOutput] = Field(default_factory=list)
    
    # Timing
    created_at: datetime
    completed_at: Optional[datetime] = None
    processing_time: Optional[float] = None  # seconds
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @property
    def video_url(self) -> Optional[str]:
        """Get first video URL if available"""
        for output in self.outputs:
            if output.type == MediaType.VIDEO:
                return output.url
        return None
    
    @property
    def audio_url(self) -> Optional[str]:
        """Get first audio URL if available"""
        for output in self.outputs:
            if output.type in (MediaType.AUDIO, MediaType.MUSIC):
                return output.url
        return None
    
    @property
    def image_url(self) -> Optional[str]:
        """Get first image URL if available"""
        for output in self.outputs:
            if output.type == MediaType.IMAGE:
                return output.url
        return None
    
    @property
    def is_completed(self) -> bool:
        """Check if execution is completed"""
        return self.status == ExecutionStatus.COMPLETED
    
    @property
    def is_failed(self) -> bool:
        """Check if execution failed"""
        return self.status == ExecutionStatus.FAILED


class ExecuteRequest(BaseModel):
    """Request model for execute endpoint"""
    preset: str
    text: Optional[str] = None
    script: Optional[str] = None
    image_prompt: Optional[str] = None
    music_prompt: Optional[str] = None
    voice: Optional[str] = None
    style: Optional[str] = None
    duration: Optional[int] = None
    webhook_url: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ReserveResponse(BaseModel):
    """Response from reserve endpoint"""
    execution_id: str
    reserved_amount: float
    expires_at: datetime
    status: ExecutionStatus = ExecutionStatus.RESERVED