# -*- coding: utf-8 -*-
# VideoEncoder 영상 코덱 선택 테스트

from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import AsyncMock

import asyncio
import sys

import pytest


# 프로젝트 루트를 sys.path 에 추가 (src/ 내부에서 실행 시 필요)
_project_root = str(Path(__file__).resolve().parent.parent)
if (_project_root not in sys.path):
	sys.path.insert(0, _project_root)

from src.encoder import VideoEncoder
from src.models import ConfigDef, ConfigKey, FileInfo, FileStatus, MoveDirection, VideoCodec


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
	assert cmd[cmd.index("-preset:v") + 1] == "4"
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


def test_svt_av1_preset_from_config(tmp_path: Path):
	"""svtav1_preset 설정 값이 -preset:v 로 전달된다."""
	cmd = build_command(make_encoder(tmp_path, **{ConfigKey.SVTAV1_PRESET: 8}))
	assert cmd[cmd.index("-preset:v") + 1] == "8"


@pytest.mark.parametrize("bit_depth, expected_pix_fmt", [
	(8, "yuv420p"),
	(10, "yuv420p10le"),
	(12, "yuv420p10le"),	# 지원하지 않는 값은 기본 10비트로 대체
])
def test_svt_av1_bit_depth_from_config(tmp_path: Path, bit_depth: int, expected_pix_fmt: str):
	"""svtav1_bit_depth 설정에 따라 픽셀 포맷이 결정된다."""
	cmd = build_command(make_encoder(tmp_path, **{ConfigKey.SVTAV1_BIT_DEPTH: bit_depth}))
	assert cmd[cmd.index("-pix_fmt") + 1] == expected_pix_fmt


@pytest.mark.parametrize("codec, expected", [
	("libsvtav1", {"codec": "libsvtav1", "preset": "4", "crf": ConfigDef.DEFAULT_CRF_SVT_AV1}),
	("libx265", {"codec": "libx265", "preset": "slow", "crf": ConfigDef.DEFAULT_CRF_X265}),
])
def test_encode_settings(tmp_path: Path, codec: str, expected: Dict[str, Any]):
	"""웹 UI 표시용 인코딩 설정은 실제 명령과 같은 코덱·preset·CRF 를 반환한다."""
	encoder = make_encoder(tmp_path, **{ConfigKey.VIDEO_CODEC: codec, ConfigKey.CRF: None})
	assert encoder.get_encode_settings() == expected


def make_list_encoder(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, names: List[str]) -> VideoEncoder:
	"""
	입력 디렉토리에 names 파일이 있는 인코더를 만듭니다. (ffprobe 대신 빈 FileInfo 생성)

	Args:
		tmp_path (Path): 입력 디렉토리로 쓸 임시 경로
		monkeypatch (pytest.MonkeyPatch): create_file_info 대체용
		names (List[str]): 입력 디렉토리에 만들 파일명

	Returns:
		VideoEncoder: 테스트용 인코더
	"""
	for name in names:
		(tmp_path / name).write_bytes(b"")

	encoder = make_encoder(tmp_path)
	encoder.files = []
	encoder.current_file_index = -1
	encoder.refreshing = False
	encoder.stop_all = False

	async def fake_create_file_info(video_file: Path) -> FileInfo:
		return FileInfo(video_file.name)

	monkeypatch.setattr(encoder, "create_file_info", fake_create_file_info)
	return encoder


def filenames(encoder: VideoEncoder) -> List[str]:
	"""
	인코더 파일 목록의 파일명 리스트를 반환합니다.

	Args:
		encoder (VideoEncoder): 테스트용 인코더

	Returns:
		List[str]: 목록 순서대로의 파일명
	"""
	return [f.filename for f in encoder.files]


def test_refresh_removes_deleted_and_appends_new(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
	"""새로고침 시 삭제된 파일은 제거하고, 신규 파일은 기존 순서 뒤에 하나씩 추가한다."""
	encoder = make_list_encoder(tmp_path, monkeypatch, ["b.mp4", "c.mp4"])
	encoder.files = [FileInfo("c.mp4"), FileInfo("a.mp4"), FileInfo("b.mp4")]	# a.mp4 는 삭제된 상태
	(tmp_path / "d.mp4").write_bytes(b"")
	(tmp_path / "e.mp4").write_bytes(b"")
	ws = AsyncMock()

	result = asyncio.run(encoder.refresh_files(ws))

	assert result == {"removed": 1, "added": 2}
	assert filenames(encoder) == ["c.mp4", "b.mp4", "d.mp4", "e.mp4"]
	assert ws.broadcast_all_status.await_count == 3	# 제거 1회 + 추가 파일마다 1회


def test_refresh_keeps_encoding_file_and_index(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
	"""인코딩 중인 파일은 삭제되어도 유지하고, current_file_index 를 새 위치로 맞춘다."""
	encoder = make_list_encoder(tmp_path, monkeypatch, ["b.mp4"])
	encoder.files = [FileInfo("a.mp4"), FileInfo("x.mp4"), FileInfo("b.mp4")]
	encoder.current_file_index = 1	# x.mp4 인코딩 중 (디렉토리에서 삭제됨)

	asyncio.run(encoder.refresh_files(AsyncMock()))

	assert filenames(encoder) == ["x.mp4", "b.mp4"]
	assert encoder.current_file_index == 0


def test_refresh_rejected_while_refreshing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
	"""이미 새로고침 중이면 None 을 반환하고 목록을 바꾸지 않는다."""
	encoder = make_list_encoder(tmp_path, monkeypatch, ["a.mp4"])
	encoder.refreshing = True

	assert asyncio.run(encoder.refresh_files(AsyncMock())) is None
	assert encoder.files == []


def test_encode_all_follows_list_changes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
	"""인코딩 중 목록 끝에 추가된 파일도 이어서 인코딩하고, 완료 파일은 건너뛰며 중단 파일은 재시도한다."""
	encoder = make_list_encoder(tmp_path, monkeypatch, ["a.mp4", "b.mp4", "c.mp4"])
	encoder.config.reload = lambda: None
	encoder.parse_arguments = lambda: None
	encoder.print_config = lambda: None
	encoder.files = [FileInfo("a.mp4", FileStatus.COMPLETED), FileInfo("b.mp4", FileStatus.STOPPED)]
	encoded: List[str] = []

	async def fake_encode_file(file_info: FileInfo, websocket_manager: Any) -> bool:
		encoded.append(file_info.filename)
		assert encoder.files[encoder.current_file_index] is file_info
		if (file_info.filename == "b.mp4"):
			encoder.files.append(FileInfo("late.mp4"))	# 인코딩 중 새로고침으로 추가된 파일
		file_info.status = FileStatus.COMPLETED
		return True

	monkeypatch.setattr(encoder, "encode_file", fake_encode_file)
	asyncio.run(encoder.encode_all(AsyncMock()))

	assert encoded == ["b.mp4", "c.mp4", "late.mp4"]
	assert encoder.current_file_index == -1


@pytest.mark.parametrize("direction, expected", [
	(MoveDirection.FIRST, ["c.mp4", "a.mp4", "b.mp4", "d.mp4"]),
	(MoveDirection.UP, ["a.mp4", "c.mp4", "b.mp4", "d.mp4"]),
	(MoveDirection.DOWN, ["a.mp4", "b.mp4", "d.mp4", "c.mp4"]),
	(MoveDirection.LAST, ["a.mp4", "b.mp4", "d.mp4", "c.mp4"]),
])
def test_move_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, direction: MoveDirection, expected: List[str]):
	"""대기 파일을 방향에 따라 이동하고, 인코딩 중인 파일의 인덱스를 맞춘다."""
	encoder = make_list_encoder(tmp_path, monkeypatch, [])
	encoder.files = [FileInfo("a.mp4", FileStatus.IN_PROGRESS), FileInfo("b.mp4"), FileInfo("c.mp4"), FileInfo("d.mp4")]
	encoder.current_file_index = 0

	assert encoder.move_file("c.mp4", direction) is True
	assert filenames(encoder) == expected
	assert encoder.files[encoder.current_file_index].filename == "a.mp4"


def test_move_file_at_edge_keeps_order(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
	"""맨 끝 파일을 한칸아래로 옮겨도 순서가 유지된다."""
	encoder = make_list_encoder(tmp_path, monkeypatch, [])
	encoder.files = [FileInfo("a.mp4"), FileInfo("b.mp4")]

	assert encoder.move_file("b.mp4", MoveDirection.DOWN) is True
	assert filenames(encoder) == ["a.mp4", "b.mp4"]


@pytest.mark.parametrize("filename", ["a.mp4", "none.mp4"])
def test_move_file_rejects_non_pending(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, filename: str):
	"""대기 상태가 아니거나 없는 파일은 이동하지 않는다."""
	encoder = make_list_encoder(tmp_path, monkeypatch, [])
	encoder.files = [FileInfo("a.mp4", FileStatus.COMPLETED), FileInfo("b.mp4")]

	assert encoder.move_file(filename, MoveDirection.LAST) is False
	assert filenames(encoder) == ["a.mp4", "b.mp4"]


if __name__ == "__main__":
	pytest.main([__file__, "-v"])
