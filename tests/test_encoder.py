# -*- coding: utf-8 -*-
# VideoEncoder 영상 코덱 선택 테스트

from pathlib import Path
from typing import Any, Dict, List

import sys

import pytest


# 프로젝트 루트를 sys.path 에 추가 (src/ 내부에서 실행 시 필요)
_project_root = str(Path(__file__).resolve().parent.parent)
if (_project_root not in sys.path):
	sys.path.insert(0, _project_root)

from src.encoder import VideoEncoder
from src.models import ConfigDef, ConfigKey, FileInfo, VideoCodec


class StubConfig:
	"""
	ConfigManager.get 만 흉내 내는 테스트용 설정 객체.
	"""

	def __init__(self, values: Dict[str, Any]):
		"""
		테스트용 설정 값을 보관합니다.

		Args:
			values (Dict[str, Any]): 설정 키와 값
		"""
		self.values = values


	def get(self, key: str, default: Any=None) -> Any:
		"""
		설정 값을 반환합니다.

		Args:
			key (str): 설정 키
			default (Any): 키가 없을 때 반환할 값

		Returns:
			Any: 설정 값 또는 default
		"""
		return self.values.get(key, default)


def make_encoder(tmp_path: Path, **values: Any) -> VideoEncoder:
	"""
	명령줄 파싱·디렉토리 생성 없이 VideoEncoder 를 만듭니다.

	Args:
		tmp_path (Path): 입력·출력·자막 디렉토리로 쓸 임시 경로
		**values (Any): 기본 설정에 덮어쓸 설정 값

	Returns:
		VideoEncoder: 테스트용 인코더
	"""
	config = {
		ConfigKey.FFMPEG_PATH: "ffmpeg",
		ConfigKey.CRF: 27,
		ConfigKey.VOLUME: 1.15,
		ConfigKey.AUDIO_BITRATE: "128k",
	}
	config.update(values)

	encoder = VideoEncoder.__new__(VideoEncoder)
	encoder.config = StubConfig(config)
	encoder.input_dir = tmp_path
	encoder.output_dir = tmp_path
	encoder.subtitle_dir = tmp_path / "subs"
	return encoder


def build_command(encoder: VideoEncoder) -> List[str]:
	"""
	자막·스케일 없는 파일로 FFmpeg 명령을 만듭니다.

	Args:
		encoder (VideoEncoder): 테스트용 인코더

	Returns:
		List[str]: FFmpeg 실행 인자 리스트
	"""
	file_info = FileInfo("sample.mp4")
	file_info.output_filename = "sample_out.mp4"
	return encoder.build_ffmpeg_command(file_info)


def test_default_codec_is_svt_av1(tmp_path: Path):
	"""video_codec 설정이 없으면 SVT-AV1 을 사용한다."""
	encoder = make_encoder(tmp_path)
	assert encoder.get_video_codec() == VideoCodec.SVT_AV1
	assert ConfigDef.DEFAULT_VIDEO_CODEC == VideoCodec.SVT_AV1.value


def test_invalid_codec_falls_back_to_default(tmp_path: Path):
	"""지원하지 않는 코덱 이름이면 기본 코덱으로 대체한다."""
	encoder = make_encoder(tmp_path, **{ConfigKey.VIDEO_CODEC: "libvpx"})
	assert encoder.get_video_codec() == VideoCodec.SVT_AV1


def test_svt_av1_command_options(tmp_path: Path):
	"""SVT-AV1 명령에는 전용 옵션이 들어가고 -tune 은 없다."""
	cmd = build_command(make_encoder(tmp_path, **{ConfigKey.VIDEO_CODEC: "libsvtav1", ConfigKey.CRF: 30}))
	assert cmd[cmd.index("-c:v") + 1] == "libsvtav1"
	assert cmd[cmd.index("-crf:v") + 1] == "30"
	assert cmd[cmd.index("-preset:v") + 1] == "6"
	assert cmd[cmd.index("-pix_fmt") + 1] == "yuv420p10le"
	assert cmd[cmd.index("-svtav1-params") + 1] == "tune=0"
	assert "-tune:v" not in cmd


def test_x265_command_options(tmp_path: Path):
	"""x265 선택 시 기존 옵션(slow, ssim)을 그대로 사용한다."""
	cmd = build_command(make_encoder(tmp_path, **{ConfigKey.VIDEO_CODEC: "libx265"}))
	assert cmd[cmd.index("-c:v") + 1] == "libx265"
	assert cmd[cmd.index("-preset:v") + 1] == "slow"
	assert cmd[cmd.index("-tune:v") + 1] == "ssim"
	assert "-svtav1-params" not in cmd
	assert "-pix_fmt" not in cmd


@pytest.mark.parametrize("codec, expected_crf", [
	("libsvtav1", ConfigDef.DEFAULT_CRF_SVT_AV1),
	("libx265", ConfigDef.DEFAULT_CRF_X265),
])
def test_crf_defaults_to_codec_recommendation(tmp_path: Path, codec: str, expected_crf: int):
	"""crf 가 null 이면 코덱별 권장 CRF 를 사용한다."""
	cmd = build_command(make_encoder(tmp_path, **{ConfigKey.VIDEO_CODEC: codec, ConfigKey.CRF: None}))
	assert cmd[cmd.index("-crf:v") + 1] == str(expected_crf)


def test_explicit_crf_overrides_recommendation(tmp_path: Path):
	"""crf 값이 지정되어 있으면 코덱과 관계없이 그 값을 사용한다."""
	cmd = build_command(make_encoder(tmp_path, **{ConfigKey.VIDEO_CODEC: "libx265", ConfigKey.CRF: 22}))
	assert cmd[cmd.index("-crf:v") + 1] == "22"


if __name__ == "__main__":
	pytest.main([__file__, "-v"])
