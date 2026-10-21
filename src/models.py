# -*- coding: utf-8 -*-
# 영상 정보 관리 시스템 - 데이터 모델
# from : main.py (리팩토링 분리)

from enum import Enum
from pathlib import Path
from typing import Any, Dict, Final, Optional


class ConfigKey:
    """설정 파일 키 상수 정의."""
    FFMPEG_PATH: Final[str] = "ffmpeg_path"
    FFPROBE_PATH: Final[str] = "ffprobe_path"
    INPUT_DIR: Final[str] = "input_dir"
    OUTPUT_DIR: Final[str] = "output_dir"
    SUBTITLE_DIR: Final[str] = "subtitle_dir"
    LOG_DIR: Final[str] = "log_dir"
    VIDEO_CODEC: Final[str] = "video_codec"
    SVTAV1_PRESET: Final[str] = "svtav1_preset"
    SVTAV1_BIT_DEPTH: Final[str] = "svtav1_bit_depth"
    CRF: Final[str] = "crf"
    VOLUME: Final[str] = "volume"
    AUDIO_BITRATE: Final[str] = "audio_bitrate"
    TEMPLATES_DIR: Final[str] = "templates_dir"
    DEFAULT_RESOLUTION: Final[str] = "default_resolution"


class ConfigDef:
    """기본 설정 상수 정의."""
    CONFIG_FILE: Final[str] = "conf/encode.json"
    DEFAULT_FFMPEG: Final[str] = "ffmpeg"
    DEFAULT_FFPROBE: Final[str] = "ffprobe"
    DEFAULT_INPUT_DIR: Final[str] = "/home/secc/tmp/k2"
    DEFAULT_OUTPUT_DIR: Final[str] = "/home/secc/tmp/_encoded"
    DEFAULT_SUBTITLE_DIR: Final[str] = "/home/secc/tmp/subs"
    DEFAULT_LOG_DIR: Final[str] = "logs"
    DEFAULT_VIDEO_CODEC: Final[str] = "libsvtav1"
    DEFAULT_SVTAV1_PRESET: Final[int] = 4
    DEFAULT_SVTAV1_BIT_DEPTH: Final[int] = 10
    DEFAULT_CRF: Final[Optional[int]] = None    # None 이면 코덱별 권장 CRF 사용
    DEFAULT_CRF_SVT_AV1: Final[int] = 30
    DEFAULT_CRF_X265: Final[int] = 27
    DEFAULT_VOLUME: Final[float] = 1.15
    DEFAULT_AUDIO_BITRATE: Final[str] = "128k"
    MAX_CONFIG_BACKUPS: Final[int] = 5
    HD_THRESHOLD: Final[int] = 700000
    HD_WIDTH: Final[int] = 1280
    FHD_WIDTH: Final[int] = 1920

    TEMPLATES_DIR: Final[str] = "templates/"
    CSS_DIR: Final[str] = "templates/css"
    IMAGES_DIR: Final[str] = "templates/images"
    JS_DIR: Final[str] = "templates/js"


class FileStatus(Enum):
    """파일 인코딩 상태를 나타내는 열거형."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class VideoCodec(Enum):
    """
    영상 인코딩에 사용할 FFmpeg 코덱(인코더 이름)을 나타내는 열거형.
    """
    SVT_AV1 = "libsvtav1"
    X265 = "libx265"


class ResolutionMode(Enum):
    """해상도 모드를 나타내는 열거형."""
    SD = "SD"
    HD = "HD"
    FHD = "FHD"
    UHD = "4K"
    UHD_8K = "8K"


class ProgressInfo:
    """인코딩 진행 정보를 저장하는 데이터 클래스."""

    def __init__(self):
        """ProgressInfo 의 새 인스턴스를 초기화합니다."""
        self.frame: int = 0
        self.fps: float = 0.0
        self.size: str = ""
        self.time: str = ""
        self.bitrate: str = ""
        self.speed: str = ""
        self.progress_percent: float = 0.0


class VideoInfo:
    """ffprobe 로 추출한 동영상 정보를 저장하는 데이터 클래스."""

    def __init__(self):
        """VideoInfo 의 새 인스턴스를 초기화합니다."""
        self.duration_seconds: float = 0.0
        self.resolution: str = ""
        self.width: int = 0
        self.height: int = 0
        self.codec: str = ""
        self.bitrate: str = ""
        self.fps: float = 0.0
        self.pixel_count: int = 0


class FileInfo:
    """개별 비디오 파일의 인코딩 정보를 저장하는 데이터 클래스."""

    def __init__(self, filename: str, status: FileStatus = FileStatus.PENDING):
        """FileInfo 의 새 인스턴스를 초기화합니다.

        Args:
            filename (str): 파일명
            status (FileStatus, optional): 초기 파일 상태 (기본값: PENDING)
        """
        self.filename: str = filename
        self.output_filename: str = ""
        self.status: FileStatus = status
        self.progress: ProgressInfo = ProgressInfo()
        self.video_info: VideoInfo = VideoInfo()
        self.subtitle_file: Optional[str] = None
        self.scale_filter: Optional[str] = None
        self.resolution_mode: ResolutionMode = ResolutionMode.HD

    def to_dict(self) -> Dict[str, Any]:
        """파일 정보를 JSON 직렬화 가능한 딕셔너리로 변환합니다.

        Returns:
            Dict[str, Any]: 파일 인코딩 상태, 진행률, 비디오 정보 등을 포함한 딕셔너리
        """
        return {
            "filename": str(self.filename) if (self.filename) else None,
            "output_filename": str(self.output_filename) if (self.output_filename) else None,
            "status": self.status.value,
            "progress": {
                "frame": self.progress.frame,
                "fps": self.progress.fps,
                "size": self.progress.size,
                "time": self.progress.time,
                "bitrate": self.progress.bitrate,
                "speed": self.progress.speed,
                "percent": round(self.progress.progress_percent, 1)
            },
            "video_info": {
                "duration": self.video_info.duration_seconds,
                "resolution": self.video_info.resolution,
                "codec": self.video_info.codec,
                "bitrate": self.video_info.bitrate,
                "fps": self.video_info.fps
            },
            "subtitle": str(self.subtitle_file) if (self.subtitle_file) else None,
            "scale": self.scale_filter,
            "resolution_mode": self.resolution_mode.value
        }


def path_handler(obj: Any) -> Any:
    """json.dumps 의 default 핸들러로, Path 객체를 문자열로 변환합니다.

    Args:
        obj (Any): 직렬화할 객체

    Returns:
        str | Any: Path 객체는 str, 그 외는 원본 값
    """
    if (isinstance(obj, Path)):
        return str(obj)
    return obj

