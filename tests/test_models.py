# -*- coding: utf-8 -*-
# tests/test_models.py - models.py 시험 테스트
# PyTest 기반 테스트 코드 (30+ 항목)

from pathlib import Path
from typing import Any
import sys

import pytest

# 프로젝트 루트를 sys.path 에 추가 (src/ 내부에서 실행 시 필요)
_project_root = str(Path(__file__).resolve().parent.parent)
if (_project_root not in sys.path):
    sys.path.insert(0, _project_root)

# Import models
from src.models import (
    ConfigKey,
    ConfigDef,
    FileStatus,
    ResolutionMode,
    ProgressInfo,
    VideoInfo,
    FileInfo,
    path_handler
)


# =========================================================
# Section 1: ConfigKey 테스트 (5 items)
# =========================================================

class TestConfigKey:
    """ConfigKey 상수 및 Enum 관련 테스트."""

    def test_ffmpeg_path_key_exists(self):
        """FFmpeg 경로 키 존재 확인."""
        assert ConfigKey.FFMPEG_PATH == "ffmpeg_path"

    def test_ffprobe_path_key_exists(self):
        """FFProbe 경로 키 존재 확인."""
        assert ConfigKey.FFPROBE_PATH == "ffprobe_path"

    def test_input_dir_key_exists(self):
        """Input 디렉터리 키 존재 확인."""
        assert ConfigKey.INPUT_DIR == "input_dir"

    def test_output_dir_key_exists(self):
        """Output 디렉터리 키 존재 확인."""
        assert ConfigKey.OUTPUT_DIR == "output_dir"

    def test_subtitle_dir_key_exists(self):
        """Subtitle 디렉터리 키 존재 확인."""
        assert ConfigKey.SUBTITLE_DIR == "subtitle_dir"

    def test_log_dir_key_exists(self):
        """Log 디렉터리 키 존재 확인."""
        assert ConfigKey.LOG_DIR == "log_dir"

    def test_crf_key_exists(self):
        """Crf 키 존재 확인."""
        assert ConfigKey.CRF == "crf"

    def test_volume_key_exists(self):
        """Volume 키 존재 확인."""
        assert ConfigKey.VOLUME == "volume"

    def test_audio_bitrate_key_exists(self):
        """Audio Bitrate 키 존재 확인."""
        assert ConfigKey.AUDIO_BITRATE == "audio_bitrate"

    def test_templates_dir_key_exists(self):
        """Templates 디렉터리 키 존재 확인."""
        assert ConfigKey.TEMPLATES_DIR == "templates_dir"

    def test_default_key_exists(self):
        """Default 레졸루션 키 존재 확인."""
        assert ConfigKey.DEFAULT_RESOLUTION == "default_resolution"

# =========================================================
# Section 2: ConfigDef 테스트 (5 items)
# =========================================================

class TestConfigDef:
    """ConfigDef 기본 설정 상수 테스트."""

    def test_config_file_exists(self):
        """설정 파일 이름 확인."""
        assert ConfigDef.CONFIG_FILE == "conf/encode.json"

    def test_default_ffmpeg_exists(self):
        """기본 FFmpeg 값 확인."""
        assert ConfigDef.DEFAULT_FFMPEG == "ffmpeg"

    def test_default_ffprobe_exists(self):
        """기본 FFProbe 값 확인."""
        assert ConfigDef.DEFAULT_FFPROBE == "ffprobe"

    def test_default_input_dir_exists(self):
        """기본 Input 디렉터리 확인."""
        assert ConfigDef.DEFAULT_INPUT_DIR == "/home/secc/tmp/k2"

    def test_default_output_dir_exists(self):
        """기본 Output 디렉터리 확인."""
        assert ConfigDef.DEFAULT_OUTPUT_DIR == "/home/secc/tmp/_encoded"

    def test_default_subtitle_dir_exists(self):
        """기본 Subtitle 디렉터리 확인."""
        assert ConfigDef.DEFAULT_SUBTITLE_DIR == "/home/secc/tmp/subs"

    def test_default_log_dir_exists(self):
        """기본 Log 디렉터리 확인."""
        assert ConfigDef.DEFAULT_LOG_DIR == "logs"

    def test_default_crf_exists(self):
        """기본 CRF 값 확인 (None 이면 코덱별 권장값 사용)."""
        assert ConfigDef.DEFAULT_CRF is None
        assert ConfigDef.DEFAULT_CRF_SVT_AV1 == 30
        assert ConfigDef.DEFAULT_CRF_X265 == 27

    def test_default_volume_exists(self):
        """기본 Volume 값 확인 (float 타입)."""
        assert ConfigDef.DEFAULT_VOLUME == 1.15
        assert isinstance(ConfigDef.DEFAULT_VOLUME, float)

    def test_default_audio_bitrate_exists(self):
        """기본 Audio Bitrate 값 확인."""
        assert ConfigDef.DEFAULT_AUDIO_BITRATE == "128k"

    def test_hd_threshold_exists(self):
        """HD threshold 값 확인."""
        assert ConfigDef.HD_THRESHOLD == 700000

    def test_hd_width_exists(self):
        """HD width 값 확인."""
        assert ConfigDef.HD_WIDTH == 1280

    def test_fhd_width_exists(self):
        """FHD width 값 확인."""
        assert ConfigDef.FHD_WIDTH == 1920

    def test_templates_dir_exists(self):
        """Templates 디렉тория 값 확인."""
        assert ConfigDef.TEMPLATES_DIR == "templates/"

    def test_css_dir_exists(self):
        """CSS 디렉터리 값 확인."""
        assert ConfigDef.CSS_DIR == "templates/css"

    def test_images_dir_exists(self):
        """Images 디렉터리 값 확인."""
        assert ConfigDef.IMAGES_DIR == "templates/images"

    def test_js_dir_exists(self):
        """JS 디렉터리 값 확인."""
        assert ConfigDef.JS_DIR == "templates/js"

# =========================================================
# Section 3: FileStatus Enum 테스트 (6 items)
# =========================================================

class TestFileStatus:
    """FileStatus Enum 테스트."""

    def test_pending_status_exists(self):
        """Pending 상태 존재 확인."""
        assert FileStatus.PENDING in FileStatus
        assert FileStatus.PENDING.name == "PENDING"
        assert FileStatus.PENDING.value == "pending"

    def test_in_progress_status_exists(self):
        """In Progress 상태 존재 확인."""
        assert FileStatus.IN_PROGRESS in FileStatus
        assert FileStatus.IN_PROGRESS.name == "IN_PROGRESS"
        assert FileStatus.IN_PROGRESS.value == "in_progress"

    def test_completed_status_exists(self):
        """Completed 상태 존재 확인."""
        assert FileStatus.COMPLETED in FileStatus
        assert FileStatus.COMPLETED.name == "COMPLETED"
        assert FileStatus.COMPLETED.value == "completed"

    def test_failed_status_exists(self):
        """Failed 상태 존재 확인."""
        assert FileStatus.FAILED in FileStatus
        assert FileStatus.FAILED.name == "FAILED"
        assert FileStatus.FAILED.value == "failed"

    def test_stopped_status_exists(self):
        """Stopped 상태 존재 존재 확인."""
        assert FileStatus.STOPPED in FileStatus
        assert FileStatus.STOPPED.name == "STOPPED"
        assert FileStatus.STOPPED.value == "stopped"

    def test_all_statuses_valid(self):
        """모든 상태값 유효성 확인."""
        statuses = [
            FileStatus.PENDING,
            FileStatus.IN_PROGRESS,
            FileStatus.COMPLETED,
            FileStatus.FAILED,
            FileStatus.STOPPED
        ]
        for status in FileStatus:
            assert status in FileStatus

# =========================================================
# Section 4: ResolutionMode Enum 테스트 (7 items)
# =========================================================

class TestResolutionMode:
    """ResolutionMode Enum 테스트."""

    def test_hd_mode_exists(self):
        """HD 모드 존재 확인."""
        assert ResolutionMode.HD in ResolutionMode
        assert ResolutionMode.HD.name == "HD"
        assert ResolutionMode.HD.value == "HD"

    def test_sd_mode_exists(self):
        """SD 모드 존재 확인."""
        assert ResolutionMode.SD in ResolutionMode
        assert ResolutionMode.SD.name == "SD"
        assert ResolutionMode.SD.value == "SD"

    def test_fhd_mode_exists(self):
        """FHD 모드 존재 확인."""
        assert ResolutionMode.FHD in ResolutionMode
        assert ResolutionMode.FHD.name == "FHD"
        assert ResolutionMode.FHD.value == "FHD"

    def test_uhd_mode_exists(self):
        """4K 모드 존재 확인."""
        assert ResolutionMode.UHD in ResolutionMode
        assert ResolutionMode.UHD.name == "UHD"
        assert ResolutionMode.UHD.value == "4K"

    def test_uhd8k_mode_exists(self):
        assert ResolutionMode.UHD_8K.value == "8K"
        assert ResolutionMode.UHD_8K.name == "UHD_8K"
        
    def test_all_modes_valid(self):
        """모든 모달리티 유효성 확인."""
        expected_values = {"SD", "HD", "FHD", "4K", "8K"}
        assert {mode.value for mode in ResolutionMode} == expected_values
        for mode in ResolutionMode:
            assert isinstance(mode.value, str)

# =========================================================
# Section 5: ProgressInfo 테스트 (4 items)
# =========================================================

class TestProgressInfo:
    """ProgressInfo 데이터 클래스 테스트."""

    def test_initial_frame_is_zero(self):
        """초기 프레임 값 0 확인."""
        info = ProgressInfo()
        assert info.frame == 0
        assert isinstance(info.frame, int)

    def test_initial_fps_is_zero(self):
        """초기 FPS 값 0 확인."""
        info = ProgressInfo()
        assert info.fps == 0.0
        assert isinstance(info.fps, float)

    def test_initial_size_is_empty_string(self):
        """초기 크기 값 공백 확인."""
        info = ProgressInfo()
        assert info.size == ""

    def test_initial_bitrate_is_empty_string(self):
        """초기 비트레이트 값 공백 확인."""
        info = ProgressInfo()
        assert info.bitrate == ""

    def test_initial_progress_percent_is_zero(self):
        """초기 진행률 0.0 확인."""
        info = ProgressInfo()
        assert info.progress_percent == 0.0
        assert isinstance(info.progress_percent, float)

    def test_set_frame_updates_correctly(self):
        """프레임 값 변경 확인."""
        info = ProgressInfo()
        info.frame = 1000
        assert info.frame == 1000

    def test_set_fps_updates_correctly(self):
        """FPS 값 변경 확인."""
        info = ProgressInfo()
        info.fps = 30.5
        assert info.fps == 30.5

# =========================================================
# Section 6: VideoInfo 테스트 (4 items)
# =========================================================

class TestVideoInfo:
    """VideoInfo 데이터 클래스 테스트."""

    def test_initial_duration_is_zero(self):
        """초기 duration 값 0.0 확인."""
        info = VideoInfo()
        assert info.duration_seconds == 0.0
        assert isinstance(info.duration_seconds, float)

    def test_initial_resolution_is_empty(self):
        """초기 resolution 값 공백 확인."""
        info = VideoInfo()
        assert info.resolution == ""

    def test_initial_width_is_zero(self):
        """초기 width 값 0 확인."""
        info = VideoInfo()
        assert info.width == 0
        assert isinstance(info.width, int)

    def test_initial_height_is_zero(self):
        """초기 height 값 0 확인."""
        info = VideoInfo()
        assert info.height == 0
        assert isinstance(info.height, int)

    def test_initial_pixel_count_is_zero(self):
        """초기 pixel count 값 0 확인."""
        info = VideoInfo()
        assert info.pixel_count == 0
        assert isinstance(info.pixel_count, int)

    def test_set_duration_updates_correctly(self):
        """Duration 값 변경 확인."""
        info = VideoInfo()
        info.duration_seconds = 120.5
        assert info.duration_seconds == 120.5

    def test_set_resolution_updates_correctly(self):
        """Resolution 값 변경 확인."""
        info = VideoInfo()
        info.resolution = "1920x1080"
        assert info.resolution == "1920x1080"

# =========================================================
# Section 7: FileInfo 테스트 (8 items)
# =========================================================

class TestFileInfo:
    """FileInfo 데이터 클래스 테스트."""

    def test_initial_filename_empty_string(self):
        """초기 filename 값 공백 확인."""
        info = FileInfo("test_video.mp4")
        assert info.filename == "test_video.mp4"

    def test_initial_output_filename_empty(self):
        """초기 output_filename 값 공백 확인."""
        info = FileInfo("test_video.mp4")
        assert info.output_filename == ""

    def test_initial_status_is_pending(self):
        """초기 상태 PENDING 확인."""
        info = FileInfo("test_video.mp4")
        assert info.status == FileStatus.PENDING

    def test_initial_progress_is_new_progressInfo(self):
        """초기 ProgressInfo 인스턴스 확인."""
        info = FileInfo("test_video.mp4")
        assert isinstance(info.progress, ProgressInfo)

    def test_initial_videoInfo_is_newVideoInfo(self):
        """초기 VideoInfo 인스턴스 확인."""
        info = FileInfo("test_video.mp4")
        assert isinstance(info.video_info, VideoInfo)

    def test_initial_subtitle_file_is_none(self):
        """초기 subtitle file None 확인."""
        info = FileInfo("test_video.mp4")
        assert info.subtitle_file is None

    def test_initial_scale_filter_is_none(self):
        """초기 scale filter None 확인."""
        info = FileInfo("test_video.mp4")
        assert info.scale_filter is None

    def test_initial_resolution_mode_is_hd(self):
        """초기 해상도 모드 HD 확인."""
        info = FileInfo("test_video.mp4")
        assert info.resolution_mode == ResolutionMode.HD
        assert info.resolution_mode.value == "HD"

    def test_update_status_changes_status(self):
        """상태 변경 확인."""
        info = FileInfo("test_video.mp4")
        info.status = FileStatus.IN_PROGRESS
        assert info.status == FileStatus.IN_PROGRESS

    def test_update_subtitle_file_sets_value(self):
        """Subtitle file 설정 확인."""
        info = FileInfo("test_video.mp4")
        info.subtitle_file = "test.vtt"
        assert info.subtitle_file == "test.vtt"

    def test_initial_output_size_and_elapsed_are_zero(self):
        """완료 정보(입력·출력 크기·소요 시간)는 0으로 초기화된다."""
        info = FileInfo("test_video.mp4")
        assert info.input_size == 0
        assert info.output_size == 0
        assert info.elapsed_seconds == 0.0

# =========================================================
# Section 8: FileInfo.to_dict() 테스트 (4 items)
# =========================================================

class TestFileInfoToDict:
    """FileInfo.to_dict() 테스트."""

    def test_to_dict_returns_dict(self):
        """to_dict() 반환값 디CTIONARY 확인."""
        info = FileInfo("test.mp4")
        result = info.to_dict()
        assert isinstance(result, dict)

    def test_to_dict_contains_all_fields(self):
        """to_dict() 모든 필드 포함 확인."""
        info = FileInfo("test.mp4")
        result = info.to_dict()
        assert "filename" in result
        assert "output_filename" in result
        assert "status" in result
        assert "progress" in result
        assert "video_info" in result
        assert "subtitle" in result
        assert "scale" in result
        assert "resolution_mode" in result
        assert "input_size" in result
        assert "output_size" in result
        assert "elapsed_seconds" in result

    def test_to_dict_progress_structure(self):
        """to_dict() progress 구조 확인."""
        info = FileInfo("test.mp4")
        info.progress.frame = 100
        info.progress.fps = 30.0
        result = info.to_dict()
        assert "frame" in result["progress"]
        assert "fps" in result["progress"]
        assert result["progress"]["frame"] == 100
        assert result["progress"]["fps"] == 30.0

    def test_to_dict_video_info_structure(self):
        """to_dict() video_info 구조 확인."""
        info = FileInfo("test.mp4")
        info.video_info.duration_seconds = 120
        result = info.to_dict()
        assert result["video_info"]["duration"] == 120

# =========================================================
# Section 9: path_handler 테스트 (4 items)
# =========================================================

class TestPathHandler:
    """path_handler 함수 테스트."""

    def test_path_handler_returns_string(self):
        """Path 핸들러 문자열 반환 확인."""
        path = Path("test/video.mp4")
        result = path_handler(path)
        assert result == "test\\video.mp4"
        assert isinstance(result, str)

    def test_path_handler_returns_path_as_string(self):
        """Path 객체 변환 확인."""
        path = Path("test/video.mp4")
        result = path_handler(path)
        assert isinstance(result, str)

    def test_path_handler_returns_non_path_as_is(self):
        """Path 만 아니면 원본 반환 확인."""
        value = "test_string"
        result = path_handler(value)
        assert result == "test_string"

    def test_path_handler_returns_int_as_is(self):
        """int 만 아니면 원본 반환 확인."""
        value = 42
        result = path_handler(value)
        assert result == 42

    def test_path_handler_returns_float_as_is(self):
        """float 만 아니면 원본 반환 확인."""
        value = 3.14
        result = path_handler(value)
        assert result == 3.14

    def test_path_handler_returns_none_as_is(self):
        """None 만 아니면 원본 반환 확인."""
        value = None
        result = path_handler(value)
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
