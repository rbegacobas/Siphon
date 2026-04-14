from pydantic import BaseModel, field_validator
from typing import Optional
from enum import Enum
import re


class JobStatus(str, Enum):
    PENDING = "pending"
    EXTRACTING = "extracting"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DownloadType(str, Enum):
    VIDEO = "video"
    AUDIO = "audio"


class ExtractRequest(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def validate_youtube_url(cls, v: str) -> str:
        patterns = [
            r"^https?://(www\.)?youtube\.com/watch\?v=[\w-]{11}",
            r"^https?://youtu\.be/[\w-]{11}",
            r"^https?://(www\.)?youtube\.com/shorts/[\w-]{11}",
        ]
        if not any(re.match(p, v) for p in patterns):
            raise ValueError("URL de YouTube no válida")
        return v


class FormatInfo(BaseModel):
    format_id: str
    ext: str
    resolution: Optional[str] = None
    filesize: Optional[int] = None
    fps: Optional[float] = None
    vcodec: Optional[str] = None
    acodec: Optional[str] = None
    abr: Optional[float] = None
    label: str


class VideoMetadata(BaseModel):
    id: str
    title: str
    duration: int
    thumbnail: str
    channel: str
    upload_date: Optional[str] = None
    view_count: Optional[int] = None
    video_formats: list[FormatInfo]
    audio_formats: list[FormatInfo]


class DownloadRequest(BaseModel):
    url: str
    format_id: str
    download_type: DownloadType
    audio_format_id: Optional[str] = None  # Para muxear video+audio
    output_format: Optional[str] = None  # mp3, m4a, mp4, mkv

    @field_validator("url")
    @classmethod
    def validate_youtube_url(cls, v: str) -> str:
        patterns = [
            r"^https?://(www\.)?youtube\.com/watch\?v=[\w-]{11}",
            r"^https?://youtu\.be/[\w-]{11}",
            r"^https?://(www\.)?youtube\.com/shorts/[\w-]{11}",
        ]
        if not any(re.match(p, v) for p in patterns):
            raise ValueError("URL de YouTube no válida")
        return v


class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress: float = 0.0
    message: Optional[str] = None
    filename: Optional[str] = None
    filesize: Optional[int] = None


class JobProgress(BaseModel):
    job_id: str
    status: JobStatus
    progress: float
    speed: Optional[str] = None
    eta: Optional[str] = None
    message: Optional[str] = None
