# -*- coding: utf-8 -*-
# 영상 정보 관리 시스템 - FFmpeg 동영상 인코더
# made : hbesthee@naver.com
# date : 2026-06-02

from datetime import datetime
from os import path
from pathlib import Path
from shutil import copy2
from typing import Any, Dict, List, Optional

import asyncio
import json
import platform
import re
import subprocess
import traceback
import argparse

from src.models import (
	ConfigDef, ConfigKey, FileInfo, FileStatus, MoveDirection,
	ProgressInfo, ResolutionMode, VideoCodec, VideoInfo
)
from src.config import ConfigManager
from src.ws_manager import WebSocketManager



class VideoEncoder:
	"""FFmpeg를 사용한 동영상 인코딩을 관리하는 클래스."""

	def __init__(self, config: ConfigManager=None):
		"""VideoEncoder를 초기화하고 설정을 로드한 후 디렉토리를 준비합니다.

		Args:
			config (ConfigManager, optional): 설정 관리자 인스턴스. None일 경우 기본 설정으로 생성합니다.
		"""
		if (config is None):
			config = ConfigManager()
		self.config = config
		self.parse_arguments()

		self.files: List[FileInfo] = []
		self.current_file_index: int = -1
		self.current_process: Optional[asyncio.subprocess.Process] = None
		self.stop_current: bool = False
		self.stop_all: bool = False
		self.resolution_mode: ResolutionMode = ResolutionMode.HD
		self.refreshing: bool = False
		self._ensure_directories()


	def _ensure_directories(self) -> None:
		"""출력 디렉토리와 로그 디렉토리가 존재하지 않으면 생성합니다."""
		self.output_dir.mkdir(parents=True, exist_ok=True)
		self.log_dir.mkdir(parents=True, exist_ok=True)


	def _set_low_priority(self) -> Dict[str, Any]:
		"""FFmpeg 프로세스에 낮은 우선순위를 설정하기 위한 subprocess 옵션을 반환합니다.

		Returns:
			Dict[str, Any]: 플랫폼에 맞는 subprocess 생성 인자 딕셔너리

		Note:
			Windows: BELOW_NORMAL_PRIORITY_CLASS 플래그 사용
			Linux/Unix: preexec_fn으로 nice(19) 설정
		"""
		system = platform.system()

		if (system == "Windows"):
			import subprocess
			return {
				"creationflags": subprocess.BELOW_NORMAL_PRIORITY_CLASS
			}
		else:
			import os
			def set_priority():
				os.nice(19)
			return {
				"preexec_fn": set_priority
			}


	async def get_video_info_with_ffprobe(self, video_file: Path) -> VideoInfo:
		"""ffprobe를 사용하여 비디오 파일의 메타데이터를 추출합니다.

		Args:
			video_file (Path): 분석할 비디오 파일 경로

		Returns:
			VideoInfo: 추출된 비디오 정보 (실패 시 빈 VideoInfo 인스턴스)
		"""
		info = VideoInfo()

		try:
			cmd = [
				self.config.get(ConfigKey.FFPROBE_PATH),
				"-v", "quiet",
				"-print_format", "json",
				"-show_format",
				"-show_streams",
				str(video_file)
			]

			priority_kwargs = self._set_low_priority()

			process = await asyncio.create_subprocess_exec(
				*cmd,
				stdout=subprocess.PIPE,
				stderr=subprocess.PIPE,
				**priority_kwargs
			)

			stdout, _ = await process.communicate()
			data = json.loads(stdout.decode('utf-8'))

			if ('format' in data):
				if ('duration' in data['format']):
					info.duration_seconds = float(data['format']['duration'])
				if ('bit_rate' in data['format']):
					bitrate_bps = int(data['format']['bit_rate'])
					info.bitrate = f"{bitrate_bps // 1000} kb/s"

			for stream in data.get('streams', []):
				if (stream.get('codec_type') == 'video'):
					info.width = stream.get('width', 0)
					info.height = stream.get('height', 0)
					info.resolution = f"{info.width}x{info.height}"
					info.pixel_count = info.width * info.height
					info.codec = stream.get('codec_name', '')

					fps_str = stream.get('r_frame_rate', '0/1')
					if ('/' in fps_str):
						num, den = fps_str.split('/')
						if (int(den) != 0):
							info.fps = float(num) / float(den)
					break

		except Exception as e:
			print(f"ffprobe 오류: {e}")

		return info


	def check_uncensored_pattern(self, filename: str) -> bool:
		"""파일명에 무수정(uncensored) 패턴이 포함되어 있는지 확인합니다.

		Args:
			filename (str): 검사할 파일명

		Returns:
			bool: 무수정 패턴 존재 시 True, 그렇지 않으면 False
		"""
		uncensored_patterns = ['-HU', '-FHU', '-hu', '-fhu']
		for pattern in uncensored_patterns:
			if (pattern in filename):
				return True
		return False


	def find_subtitle(self, video_file: Path) -> Optional[Path]:
		"""비디오 파일명과 일치하는 자막 파일(.srt)을 자막 디렉토리에서 찾습니다.

		파일명에서 시리즈 코드(예: ABC-12345)를 추출하여 같은 코드로 시작하는
		srt 파일을 검색합니다.

		Args:
			video_file (Path): 비디오 파일 경로

		Returns:
			Optional[Path]: 일치하는 자막 파일 경로 또는 None
		"""
		pattern = re.compile(r'^([A-Z]{3,5}-\d{2,5})')
		match = pattern.match(video_file.stem)

		if (not match):
			return None

		if (not self.subtitle_dir.exists()):
			return None

		base_name = match.group(1)

		for srt_file in self.subtitle_dir.glob(f"{base_name}*.srt"):
			return srt_file

		return None


	def generate_output_filename(self, input_file: Path, video_info: VideoInfo
							, subtitle_file: Optional[Path]
							, resolution_mode: ResolutionMode
							, use_uncensored: bool=False) -> str:
		"""출력 파일명을 생성합니다.

		파일명 규칙:
			- {시리즈코드}-{화질접미사}{자막접미사}.mp4
			- 화질접미사: FHD-U / HD-U / SD-U (무수정), FHD-D / HD-D / SD-D (일반)
			- 자막접미사: 자막 존재 시 -S 추가

		Args:
			input_file (Path): 입력 파일 경로
			video_info (VideoInfo): 비디오 정보
			subtitle_file (Optional[Path]): 자막 파일 경로 (없으면 None)
			resolution_mode (ResolutionMode): 해상도 모드 (HD/FHD)
			use_uncensored (bool): 무수정 패턴 사용 여부

		Returns:
			str: 생성된 출력 파일명
		"""
		pattern = re.compile(r'^([A-Z]{3,5}-\d{2,5})')
		match = pattern.match(input_file.stem)

		if (not match):
			return input_file.name

		base_name = match.group(1)
		quality_char = "U" if (use_uncensored) else "D"

		if (video_info.pixel_count >= ConfigDef.HD_THRESHOLD):
			if (resolution_mode == ResolutionMode.FHD):
				quality_suffix = f"-FH{quality_char}"
			else:
				quality_suffix = f"-H{quality_char}"
		else:
			quality_suffix = f"-S{quality_char}"

		subtitle_suffix = "-S" if subtitle_file else ""

		return f"{base_name}{quality_suffix}{subtitle_suffix}.mp4"


	def calculate_scale_filter(self, video_info: VideoInfo, resolution_mode: ResolutionMode) -> Optional[str]:
		"""해상도 모드에 따라 FFmpeg scale 필터를 계산합니다.

		Args:
			video_info (VideoInfo): 비디오 정보 (픽셀 수, 너비, 높이)
			resolution_mode (ResolutionMode): 목표 해상도 모드 (HD: 1280, FHD: 1920, 4K: 3840, 8K: 7680)

		Returns:
			Optional[str]: scale 필터 문자열 (예: "scale=1280:720") 또는 조정 불필요 시 None
		"""
		if (video_info.pixel_count < ConfigDef.HD_THRESHOLD):
			return None

		resolution_widths = {
			ResolutionMode.SD: 640,
			ResolutionMode.HD: ConfigDef.HD_WIDTH,
			ResolutionMode.FHD: ConfigDef.FHD_WIDTH,
			ResolutionMode.UHD: 3840,
			ResolutionMode.UHD_8K: 7680
		}

		if (resolution_mode == ResolutionMode.UHD):
			target_width = resolution_widths[ResolutionMode.UHD]
		elif (resolution_mode == ResolutionMode.UHD_8K):
			target_width = resolution_widths[ResolutionMode.UHD_8K]
		elif (resolution_mode == ResolutionMode.FHD):
			target_width = ConfigDef.FHD_WIDTH
		else:
			target_width = ConfigDef.HD_WIDTH

		if (video_info.width <= target_width):
			return None

		target_height = int(video_info.height * target_width / video_info.width)
		target_height = target_height - (target_height % 2)
		return f"scale={target_width}:{target_height}"


	async def get_video_files(self) -> List[Path]:
		"""입력 디렉토리에서 MP4 파일 목록을 정렬하여 반환합니다.

		Returns:
			List[Path]: 정렬된 MP4 파일 경로 리스트 (디렉토리 없을 시 빈 리스트)
		"""
		if (not self.input_dir.exists()):
			return []

		return sorted(self.input_dir.glob("*.mp4"))


	async def create_file_info(self, video_file: Path) -> FileInfo:
		"""
		비디오 파일의 메타데이터를 수집하여 FileInfo 를 생성합니다.

		Args:
			video_file (Path): 비디오 파일 경로

		Returns:
			FileInfo: 메타데이터·자막·출력 파일명이 채워진 파일 정보
		"""
		file_info = FileInfo(str(video_file.name))
		subtitle_file = self.find_subtitle(video_file)
		file_info.video_info = await self.get_video_info_with_ffprobe(video_file)
		file_info.subtitle_file = str(subtitle_file) if (subtitle_file is not None) else None
		file_info.resolution_mode = self.resolution_mode
		file_info.scale_filter = self.calculate_scale_filter(file_info.video_info, file_info.resolution_mode)
		file_info.output_filename = self.generate_output_filename(
			video_file,
			file_info.video_info,
			file_info.subtitle_file,
			file_info.resolution_mode,
			use_uncensored=self.check_uncensored_pattern(video_file.name)
		)
		return file_info


	def _get_current_file(self) -> Optional[FileInfo]:
		"""
		현재 인코딩 중인 파일 정보를 반환합니다.

		Returns:
			Optional[FileInfo]: 인코딩 중인 파일 정보, 없으면 None
		"""
		if (0 <= self.current_file_index < len(self.files)):
			return self.files[self.current_file_index]
		return None


	def _sync_current_index(self, current: Optional[FileInfo]) -> None:
		"""
		목록 변경(삭제·이동) 후 인코딩 중인 파일의 새 위치로 current_file_index 를 맞춥니다.

		Args:
			current (Optional[FileInfo]): 목록 변경 전에 인코딩 중이던 파일 정보
		"""
		if (current is not None):
			self.current_file_index = self.files.index(current)


	async def refresh_files(self, websocket_manager: WebSocketManager) -> Optional[Dict[str, int]]:
		"""
		입력 디렉토리를 다시 읽어 파일 목록을 갱신합니다.
		삭제된 파일은 목록에서 제거하고(인코딩 중인 파일 제외), 신규 파일은 목록 끝에
		하나씩 추가하며 추가할 때마다 전체 상태를 브로드캐스트합니다.

		Args:
			websocket_manager (WebSocketManager): 상태 브로드캐스트에 사용할 WebSocket 관리자

		Returns:
			Optional[Dict[str, int]]: {"removed": 제거 수, "added": 추가 수}, 이미 새로고침 중이면 None
		"""
		if (self.refreshing):
			return None

		self.refreshing = True
		try:
			video_files = await self.get_video_files()
			video_names = {video_file.name for video_file in video_files}

			current = self._get_current_file()
			count_before = len(self.files)
			self.files = [f for f in self.files if ((f.filename in video_names) or (f is current))]
			removed = count_before - len(self.files)
			self._sync_current_index(current)
			if (0 < removed):
				await websocket_manager.broadcast_all_status(self.get_all_status())

			added = 0
			for video_file in video_files:
				if (any(f.filename == video_file.name for f in self.files)):
					continue
				self.files.append(await self.create_file_info(video_file))
				added += 1
				await websocket_manager.broadcast_all_status(self.get_all_status())

			return {"removed": removed, "added": added}
		finally:
			self.refreshing = False


	def move_file(self, filename: str, direction: MoveDirection) -> bool:
		"""
		대기 중인 파일의 목록 내 위치를 이동합니다. (인코딩 순서도 함께 바뀜)
		위쪽으로는 인코딩 완료·진행 중인 파일보다 위로 올라갈 수 없습니다.

		Args:
			filename (str): 이동할 파일명
			direction (MoveDirection): 이동 방향 (처음으로 / 한칸위 / 한칸아래 / 마지막으로)

		Returns:
			bool: 이동했으면 True, 파일이 없거나 대기 상태가 아니면 False
		"""
		file_info = next((f for f in self.files if (f.filename == filename)), None)
		if ((file_info is None) or (file_info.status != FileStatus.PENDING)):
			return False

		current = self._get_current_file()
		index = self.files.index(file_info)
		targets = {
			MoveDirection.FIRST: 0,
			MoveDirection.UP: index - 1,
			MoveDirection.DOWN: index + 1,
			MoveDirection.LAST: len(self.files) - 1
		}
		# 위쪽 한계: 이 파일 위에 있는 마지막 완료·진행 중 파일의 바로 아래
		top_limit = 0
		for i in range(index):
			if (self.files[i].status in (FileStatus.COMPLETED, FileStatus.IN_PROGRESS)):
				top_limit = i + 1
		target = min(max(targets[direction], top_limit), len(self.files) - 1)

		self.files.insert(target, self.files.pop(index))
		self._sync_current_index(current)
		return True


	def set_resolution_mode(self, filename: str, resolution_mode: str) -> bool:
		"""특정 파일의 해상도 모드를 변경하고 출력 파일명과 scale 필터를 재계산합니다.

		Args:
			filename (str): 대상 파일명
			resolution_mode (str): 변경할 해상도 모드 ('sd', 'hd', 'fhd', '4k', '8k')

		Returns:
			bool: 설정 성공 시 True, 파일을 찾지 못하면 False
		"""
		mode_map = {
			'sd': ResolutionMode.SD,
			'hd': ResolutionMode.HD,
			'fhd': ResolutionMode.FHD,
			'4k': ResolutionMode.UHD,
			'8k': ResolutionMode.UHD_8K
		}

		for file_info in self.files:
			if (file_info.filename == filename):
				if (resolution_mode.lower() in mode_map):
					file_info.resolution_mode = mode_map[resolution_mode.lower()]
				else:
					file_info.resolution_mode = ResolutionMode.HD

				input_file = self.input_dir / file_info.filename
				file_info.scale_filter = self.calculate_scale_filter(file_info.video_info, file_info.resolution_mode)
				file_info.output_filename = self.generate_output_filename(
					input_file,
					file_info.video_info,
					file_info.subtitle_file,
					file_info.resolution_mode,
					use_uncensored=self.check_uncensored_pattern(file_info.filename)
				)
				return True
		return False


	def get_video_codec(self) -> VideoCodec:
		"""
		설정의 video_codec 값을 VideoCodec 으로 변환합니다.
		값이 없거나 지원하지 않는 코덱이면 기본 코덱(SVT-AV1)을 사용합니다.

		Returns:
			VideoCodec: 인코딩에 사용할 영상 코덱
		"""
		codec_name = self.config.get(ConfigKey.VIDEO_CODEC, ConfigDef.DEFAULT_VIDEO_CODEC)
		try:
			return VideoCodec(codec_name)
		except ValueError:
			print(f"지원하지 않는 video_codec '{codec_name}', 기본값 {ConfigDef.DEFAULT_VIDEO_CODEC} 사용")
			return VideoCodec(ConfigDef.DEFAULT_VIDEO_CODEC)


	def get_crf(self, video_codec: VideoCodec) -> int:
		"""
		인코딩에 사용할 CRF 값을 반환합니다.
		설정(또는 --crf 인자)에 값이 있으면 그 값을, 없으면(null) 코덱별 권장값을 사용합니다.

		Args:
			video_codec (VideoCodec): 인코딩에 사용할 영상 코덱

		Returns:
			int: CRF 값
		"""
		crf = self.config.get(ConfigKey.CRF)
		if (crf is not None):
			return crf
		if (video_codec == VideoCodec.X265):
			return ConfigDef.DEFAULT_CRF_X265
		return ConfigDef.DEFAULT_CRF_SVT_AV1


	def get_svtav1_pix_fmt(self) -> str:
		"""
		설정의 SVT-AV1 비트 깊이(8 또는 10)에 맞는 픽셀 포맷을 반환합니다.
		지원하지 않는 값이면 기본 비트 깊이(10)를 사용합니다.

		Returns:
			str: FFmpeg 픽셀 포맷 (yuv420p 또는 yuv420p10le)
		"""
		pix_fmts = {8: "yuv420p", 10: "yuv420p10le"}
		bit_depth = self.config.get(ConfigKey.SVTAV1_BIT_DEPTH, ConfigDef.DEFAULT_SVTAV1_BIT_DEPTH)
		if (bit_depth not in pix_fmts):
			print(f"지원하지 않는 svtav1_bit_depth '{bit_depth}', 기본값 {ConfigDef.DEFAULT_SVTAV1_BIT_DEPTH} 사용")
			bit_depth = ConfigDef.DEFAULT_SVTAV1_BIT_DEPTH
		return pix_fmts[bit_depth]


	def get_preset(self, video_codec: VideoCodec) -> str:
		"""
		코덱별 인코딩 preset 값을 반환합니다. (x265: slow 고정, SVT-AV1: 설정 값)

		Args:
			video_codec (VideoCodec): 인코딩에 사용할 영상 코덱

		Returns:
			str: preset 값
		"""
		if (video_codec == VideoCodec.X265):
			return "slow"
		return str(self.config.get(ConfigKey.SVTAV1_PRESET, ConfigDef.DEFAULT_SVTAV1_PRESET))


	def get_encode_settings(self) -> Dict[str, Any]:
		"""
		웹 UI 표시용 인코딩 설정(코덱, preset, CRF)을 반환합니다.

		Returns:
			Dict[str, Any]: {"codec": 코덱명, "preset": preset, "crf": CRF} 딕셔너리
		"""
		video_codec = self.get_video_codec()
		return {
			"codec": video_codec.value,
			"preset": self.get_preset(video_codec),
			"crf": self.get_crf(video_codec)
		}


	def build_ffmpeg_command(self, file_info: FileInfo) -> List[str]:
		"""FileInfo를 기반으로 FFmpeg 인코딩 명령어 리스트를 생성합니다.

		Args:
			file_info (FileInfo): 인코딩할 파일의 정보

		Returns:
			List[str]: FFmpeg 실행 인자 리스트
		"""
		input_file = self.input_dir / file_info.filename
		output_file = self.output_dir / file_info.output_filename

		subtitle_file = self.find_subtitle(input_file)

		cmd = [
			self.config.get(ConfigKey.FFMPEG_PATH),
			"-err_detect", "ignore_err",
			"-fflags", "+igndts+genpts+discardcorrupt",
			"-i", str(input_file)
		]

		if (subtitle_file is not None):
			subtitle_path = self.subtitle_dir / subtitle_file.name
			cmd.extend(["-i", str(subtitle_path)])

		video_codec = self.get_video_codec()
		cmd.extend([
			"-f", "mp4",
			"-c:v", video_codec.value,
			"-crf:v", str(self.get_crf(video_codec))
		])

		# 코덱별 전용 옵션 (libsvtav1 은 -tune 옵션이 없어 svtav1-params 로 전달)
		if (video_codec == VideoCodec.X265):
			cmd.extend(["-preset:v", self.get_preset(video_codec), "-tune:v", "ssim"])
		else:
			cmd.extend([
				"-preset:v", self.get_preset(video_codec),
				"-pix_fmt", self.get_svtav1_pix_fmt(),
				"-svtav1-params", "tune=0"
			])

		cmd.extend([
			"-avoid_negative_ts", "make_zero",
			"-fps_mode", "cfr",
			"-movflags", "+faststart"
		])

		if (file_info.scale_filter is not None):
			cmd.extend(["-vf", file_info.scale_filter])
		cmd.extend(["-af", f"volume={self.config.get(ConfigKey.VOLUME)}"])

		cmd.extend([
			"-c:a", "aac",
			"-b:a", self.config.get(ConfigKey.AUDIO_BITRATE)
		])

		if (subtitle_file is not None):
			cmd.extend(["-c:s", "mov_text"])

		cmd.extend(["-y", str(output_file)])

		return cmd


	def parse_time_to_seconds(self, time_str: str) -> float:
		"""HH:MM:SS.MS 형식의 시간 문자열을 초 단위로 변환합니다.

		Args:
			time_str (str): 시간 문자열 (예: "01:23:45.678")

		Returns:
			float: 초 단위 시간 값, 변환 실패 시 0.0
		"""
		try:
			parts = time_str.split(':')
			if (len(parts) == 3):
				hours = int(parts[0])
				minutes = int(parts[1])
				seconds = float(parts[2])
				return hours * 3600 + minutes * 60 + seconds
		except Exception:
			pass
		return 0.0


	def parse_progress(self, line: str, file_info: FileInfo) -> bool:
		"""FFmpeg 출력 라인에서 진행률 정보를 파싱하여 file_info에 반영합니다.

		Args:
			line (str): FFmpeg의 stderr 출력 라인
			file_info (FileInfo): 업데이트할 파일 정보 객체

		Returns:
			bool: 진행률 정보가 파싱되었으면 True, 관련 없는 라인이면 False
		"""
		if ("frame=" not in line):
			return False

		frame_match = re.search(r'frame=\s*(\d+)', line)
		fps_match = re.search(r'fps=\s*([\d.]+)', line)
		size_match = re.search(r'size=\s*(\S+)', line)
		time_match = re.search(r'time=\s*(\S+)', line)
		bitrate_match = re.search(r'bitrate=\s*(\S+)', line)
		speed_match = re.search(r'speed=\s*(\S+)', line)

		if (frame_match):
			file_info.progress.frame = int(frame_match.group(1))
		if (fps_match):
			file_info.progress.fps = float(fps_match.group(1))
		if (size_match):
			file_info.progress.size = size_match.group(1)
		if (time_match):
			file_info.progress.time = time_match.group(1)
			if (file_info.video_info.duration_seconds > 0):
				current_seconds = self.parse_time_to_seconds(time_match.group(1))
				file_info.progress.progress_percent = (current_seconds / file_info.video_info.duration_seconds) * 100
		if (bitrate_match):
			file_info.progress.bitrate = bitrate_match.group(1)
		if (speed_match):
			file_info.progress.speed = speed_match.group(1)

		return True


	async def encode_file(self, file_info: FileInfo, websocket_manager: WebSocketManager) -> bool:
		"""단일 비디오 파일을 FFmpeg로 인코딩합니다.
		진행률을 파싱하여 WebSocket으로 실시간 브로드캐스트하고 로그 파일에 기록합니다.

		Args:
			file_info (FileInfo): 인코딩할 파일 정보
			websocket_manager (WebSocketManager): 진행률 브로드캐스트에 사용할 WebSocket 관리자

		Returns:
			bool: 인코딩 성공 시 True, 중단/실패 시 False
		"""
		if (self.stop_all):
			return False

		file_info.status = FileStatus.IN_PROGRESS
		self.stop_current = False
		await websocket_manager.broadcast_current_status(self.get_current_status())

		cmd = self.build_ffmpeg_command(file_info)

		input_file = self.input_dir / file_info.filename
		log_file = self.log_dir / f"{input_file.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

		try:
			priority_kwargs = self._set_low_priority()

			with open(log_file, 'wb') as log:
				log.write(" ".join(cmd).encode())
				self.current_process = await asyncio.create_subprocess_exec(
					*cmd,
					stdout=subprocess.PIPE,
					stderr=subprocess.STDOUT,
					**priority_kwargs
				)

				buffer = b''
				while True:
					if (self.stop_current or self.stop_all):
						self.current_process.terminate()
						await self.current_process.wait()
						file_info.status = FileStatus.STOPPED
						return False

					chunk = await self.current_process.stdout.read(1024)
					if (not chunk):
						break

					buffer += chunk

					while b'\r' in buffer or b'\n' in buffer:
						r_pos = buffer.find(b'\r')
						n_pos = buffer.find(b'\n')

						if (r_pos == -1):
							pos = n_pos
						elif (n_pos == -1):
							pos = r_pos
						else:
							pos = min(r_pos, n_pos)

						line_bytes = buffer[:pos]
						buffer = buffer[pos + 1:]

						if (not line_bytes):
							continue

						line_str = line_bytes.decode('utf-8', errors='ignore')

						if (self.parse_progress(line_str, file_info)):
							await websocket_manager.broadcast_current_status(self.get_current_status())
						else:
							log.write(line_bytes + b'\n')
							log.flush()

				if (buffer):
					line_str = buffer.decode('utf-8', errors='ignore')
					if (not self.parse_progress(line_str, file_info)):
						log.write(buffer + b'\n')

				await self.current_process.wait()

				if (self.current_process.returncode == 0):
					file_info.status = FileStatus.COMPLETED
					file_info.progress.progress_percent = 100.0
					if ((file_info.subtitle_file) and path.exists(file_info.subtitle_file)):
						copy2(str(file_info.subtitle_file), str(self.output_dir / (file_info.output_filename).replace('.mp4', '.srt')))
					return True
				else:
					file_info.status = FileStatus.FAILED
					return False

		except Exception as e:
			print(f"인코딩 오류: {e}")
			file_info.status = FileStatus.FAILED
			return False
		finally:
			self.current_process = None
			await websocket_manager.broadcast_current_status(self.get_current_status())


	def get_all_status(self) -> Dict[str, Any]:
		"""모든 파일의 전체 상태 정보를 반환합니다.

		Returns:
			Dict[str, Any]: 전체 파일 목록, 진행률, 완료/전체 개수를 포함한 딕셔너리
		"""
		total_files = len(self.files)
		completed = sum(1 for f in self.files if f.status == FileStatus.COMPLETED)

		overall_progress = 0.0
		if (total_files > 0):
			for idx, file_info in enumerate(self.files):
				if (file_info.status == FileStatus.COMPLETED):
					overall_progress += 100.0
				elif (file_info.status == FileStatus.IN_PROGRESS):
					overall_progress += file_info.progress.progress_percent
			overall_progress = overall_progress / total_files

		all_status = {
			"type": "full",
			"files": [f.to_dict() for f in self.files],
			"encode_settings": self.get_encode_settings(),
			"current_index": self.current_file_index,
			"overall_progress": round(overall_progress, 1),
			"completed_count": completed,
			"total_count": total_files
		}

		return all_status


	def get_current_status(self) -> Dict[str, Any]:
		"""현재 인코딩 중인 파일과 전체 진행률 정보를 반환합니다.

		Returns:
			Dict[str, Any]: 현재 파일 정보, 전체 진행률, 완료/전체 개수를 포함한 딕셔너리
		"""
		total_files = len(self.files)
		completed = sum(1 for f in self.files if f.status == FileStatus.COMPLETED)

		overall_progress = 0.0
		if (total_files > 0):
			for idx, file_info in enumerate(self.files):
				if (file_info.status == FileStatus.COMPLETED):
					overall_progress += 100.0
				elif (file_info.status == FileStatus.IN_PROGRESS):
					overall_progress += file_info.progress.progress_percent
			overall_progress = overall_progress / total_files

		current_file = None
		if (0 <= self.current_file_index < len(self.files)):
			current_file = self.files[self.current_file_index].to_dict()

		return {
			"type": "current",
			"current_index": self.current_file_index,
			"current_file": current_file,
			"overall_progress": round(overall_progress, 1),
			"completed_count": completed,
			"total_count": total_files
		}


	async def encode_all(self, websocket_manager: WebSocketManager) -> None:
		"""모든 대기 중인 파일을 순차적으로 인코딩합니다.
		설정을 다시 로드하고 파일 목록을 새로고침한 후 WebSocket으로 상태를 전송합니다.
		중단·실패한 파일은 다시 대기 상태로 돌리고, 완료된 파일은 건너뜁니다.
		인코딩 중 새로고침·순서 변경이 반영되도록 매번 목록의 첫 번째 대기 파일을 선택합니다.

		Args:
			websocket_manager (WebSocketManager): 상태 브로드캐스트에 사용할 WebSocket 관리자
		"""
		self.stop_all = False

		try:
			self.config.reload()
			self.parse_arguments()
			self.print_config()
		except Exception as e:
			print(f"config error: {e}")

		await self.refresh_files(websocket_manager)
		for file_info in self.files:
			if (file_info.status in (FileStatus.STOPPED, FileStatus.FAILED)):
				file_info.status = FileStatus.PENDING
				file_info.progress = ProgressInfo()
		await websocket_manager.broadcast_all_status(self.get_all_status())

		while (not self.stop_all):
			file_info = next((f for f in self.files if (f.status == FileStatus.PENDING)), None)
			if (file_info is None):
				break

			self.current_file_index = self.files.index(file_info)
			await self.encode_file(file_info, websocket_manager)

		self.current_file_index = -1
		await websocket_manager.broadcast_current_status(self.get_current_status())


	def parse_arguments(self) -> argparse.Namespace:
		"""명령줄 인자를 파싱하고 설정에 반영한 후 디렉토리 경로와 해상도 모드를 설정합니다.

		Returns:
			argparse.Namespace: 파싱된 명령줄 인자
		"""
		parser = argparse.ArgumentParser(description="FFmpeg 웹 기반 동영상 인코딩 시스템")
		parser.add_argument("--ffmpeg", type=str, help="FFmpeg 실행 파일 경로")
		parser.add_argument("--ffprobe", type=str, help="FFprobe 실행 파일 경로")
		parser.add_argument("--input", type=str, help="입력 디렉토리")
		parser.add_argument("--output", type=str, help="출력 디렉토리")
		parser.add_argument("--sub", type=str, help="자막 디렉토리")
		parser.add_argument("--crf", type=int, help="CRF 값")
		parser.add_argument("--volume", type=float, help="볼륨 값")
		parser.add_argument("--port", type=int, default=8000, help="웹 서버 포트")
		args = parser.parse_args()

		self.config.update_from_args(args)

		self.input_dir = Path(self.config.get(ConfigKey.INPUT_DIR))
		self.output_dir = Path(self.config.get(ConfigKey.OUTPUT_DIR))
		self.subtitle_dir = Path(self.config.get(ConfigKey.SUBTITLE_DIR))
		self.log_dir = Path(self.config.get(ConfigKey.LOG_DIR))
		self.resolution_mode = ResolutionMode(self.config.get(ConfigKey.DEFAULT_RESOLUTION, ResolutionMode.HD.value))

		return args


	def print_config(self) -> None:
		"""현재 설정 값을 콘솔에 출력합니다."""
		config = self.config
		print(f"FFmpeg 경로: {config.get(ConfigKey.FFMPEG_PATH)}")
		print(f"FFprobe 경로: {config.get(ConfigKey.FFPROBE_PATH)}")
		print(f"입력 디렉토리: {config.get(ConfigKey.INPUT_DIR)}")
		print(f"출력 디렉토리: {config.get(ConfigKey.OUTPUT_DIR)}")
		print(f"자막 디렉토리: {config.get(ConfigKey.SUBTITLE_DIR)}")
		print(f"로그 디렉토리: {config.get(ConfigKey.LOG_DIR)}")
		print(f"기본 해상도: {config.get(ConfigKey.DEFAULT_RESOLUTION)}")
		video_codec = self.get_video_codec()
		print(f"영상 코덱: {video_codec.value}")
		if (video_codec == VideoCodec.SVT_AV1):
			print(f"SVT-AV1 preset: {config.get(ConfigKey.SVTAV1_PRESET, ConfigDef.DEFAULT_SVTAV1_PRESET)}")
			print(f"SVT-AV1 픽셀 포맷: {self.get_svtav1_pix_fmt()}")
		print(f"CRF: {self.get_crf(video_codec)}")
		print(f"볼륨: {config.get(ConfigKey.VOLUME)}")
		print(f"오디오 비트레이트: {config.get(ConfigKey.AUDIO_BITRATE)}")
		print(f"default resolution: {self.resolution_mode.value}")


	def stop_current_encoding(self) -> bool:
		"""현재 진행 중인 인코딩을 중단하도록 요청합니다.

		Returns:
			bool: 중단 요청 성공 시 True, 진행 중인 인코딩이 없으면 False
		"""
		if (self.current_process is not None):
			self.stop_current = True
			return True
		return False


	def stop_all_encoding(self) -> bool:
		"""모든 인코딩을 중단하도록 요청합니다. 현재 진행 중인 작업도 중단됩니다.

		Returns:
			bool: 중단 요청 성공 시 True, 진행 중인 인코딩이 없으면 False
		"""
		self.stop_all = True
		if (self.current_process is not None):
			self.stop_current = True
			return True
		return False
