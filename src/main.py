# -*- coding: utf-8 -*-
# 영상 정보 관리 시스템 (FFmpeg 동영상 인코딩 / 웹 인터페이스)
# made : hbesthee@naver.com
# date : 2025-12-14

# Original Packages
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Final, List, Optional

import argparse
import asyncio
import json
import re
import subprocess
import traceback



# Third-party Packages
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, status
from fastapi.responses import HTMLResponse,	JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates





class ConfigKey:
	"""
	설정 파일 키 상수 정의
	"""
	FFMPEG_PATH: Final[str] = "ffmpeg_path"
	FFPROBE_PATH: Final[str] = "ffprobe_path"
	INPUT_DIR: Final[str] = "input_dir"
	OUTPUT_DIR: Final[str] = "output_dir"
	SUBTITLE_DIR: Final[str] = "subtitle_dir"
	LOG_DIR: Final[str] = "log_dir"
	CRF: Final[str] = "crf"
	VOLUME: Final[str] = "volume"
	AUDIO_BITRATE: Final[str] = "audio_bitrate"
	TEMPLATES_DIR: Final[str] = "templates_dir"



class ConfigDef:
	"""
	기본 설정 상수 정의
	"""
	CONFIG_FILE: Final[str] = "conf/encode.json"
	DEFAULT_FFMPEG: Final[str] = "ffmpeg"
	DEFAULT_FFPROBE: Final[str] = "ffprobe"
	DEFAULT_INPUT_DIR: Final[str] = "/home/secc/tmp/k2"
	DEFAULT_OUTPUT_DIR: Final[str] = "/home/secc/tmp/_encoded"
	DEFAULT_SUBTITLE_DIR: Final[str] = "/home/secc/tmp/subs"
	DEFAULT_LOG_DIR: Final[str] = "logs"
	DEFAULT_CRF: Final[int] = 27
	DEFAULT_VOLUME: Final[float] = 1.15
	DEFAULT_AUDIO_BITRATE: Final[str] = "128k"
	RESOLUTION_THRESHOLD: Final[int] = 1500000
	HD_THRESHOLD: Final[int] = 700000
	TARGET_WIDTH: Final[int] = 1280

	TEMPLATES_DIR: Final[str] = "templates/"
	CSS_DIR: Final[str] = "templates/css"
	IMAGES_DIR: Final[str] = "templates/images"
	JS_DIR: Final[str] = "templates/js"



class FileStatus(Enum):
	"""
	파일 인코딩 상태
	"""
	PENDING = "pending"
	IN_PROGRESS = "in_progress"
	COMPLETED = "completed"
	FAILED = "failed"
	STOPPED = "stopped"



class ProgressInfo:
	"""
	인코딩 진행 정보
	"""

	def __init__(self):
		"""
		ProgressInfo 초기화
		"""
		self.frame: int = 0
		self.fps: float = 0.0
		self.size: str = ""
		self.time: str = ""
		self.bitrate: str = ""
		self.speed: str = ""
		self.progress_percent: float = 0.0



class VideoInfo:
	"""
	동영상 정보
	"""

	def __init__(self):
		"""
		VideoInfo 초기화
		"""
		self.duration_seconds: float = 0.0
		self.resolution: str = ""
		self.width: int = 0
		self.height: int = 0
		self.codec: str = ""
		self.bitrate: str = ""
		self.fps: float = 0.0
		self.pixel_count: int = 0



class FileInfo:
	"""
	파일 정보
	"""

	def __init__(self, filename: str, status: FileStatus = FileStatus.PENDING):
		"""
		FileInfo 초기화

		Args:
			filename: 파일명
			status: 파일 상태
		"""
		self.filename: str = filename
		self.output_filename: str = ""
		self.status: FileStatus = status
		self.progress: ProgressInfo = ProgressInfo()
		self.video_info: VideoInfo = VideoInfo()
		self.subtitle_file: Optional[str] = None
		self.scale_filter: Optional[str] = None


	def to_dict(self) -> Dict[str, Any]:
		"""
		딕셔너리로 변환

		Returns:
			파일 정보 딕셔너리
		"""
		return {
			"filename": self.filename,
			"output_filename": self.output_filename,
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
			"subtitle": self.subtitle_file,
			"scale": self.scale_filter
		}



class ConfigManager:
	"""
	설정 관리 클래스
	"""

	def __init__(self, config_file: str = ConfigDef.CONFIG_FILE):
		"""
		ConfigManager 초기화

		Args:
			config_file: 설정 파일 경로
		"""
		self.config_file = Path(config_file)
		self.config: Dict[str, Any] = {}
		self._load_or_create_config()


	def _get_default_config(self) -> Dict[str, Any]:
		"""
		기본 설정 반환

		Returns:
			기본 설정 딕셔너리
		"""
		return {
			ConfigKey.FFMPEG_PATH: ConfigDef.DEFAULT_FFMPEG,
			ConfigKey.FFPROBE_PATH: ConfigDef.DEFAULT_FFPROBE,
			ConfigKey.INPUT_DIR: ConfigDef.DEFAULT_INPUT_DIR,
			ConfigKey.OUTPUT_DIR: ConfigDef.DEFAULT_OUTPUT_DIR,
			ConfigKey.SUBTITLE_DIR: ConfigDef.DEFAULT_SUBTITLE_DIR,
			ConfigKey.LOG_DIR: ConfigDef.DEFAULT_LOG_DIR,
			ConfigKey.CRF: ConfigDef.DEFAULT_CRF,
			ConfigKey.VOLUME: ConfigDef.DEFAULT_VOLUME,
			ConfigKey.AUDIO_BITRATE: ConfigDef.DEFAULT_AUDIO_BITRATE
		}


	def _load_or_create_config(self) -> None:
		"""
		설정 파일 로드 또는 생성
		"""
		if (self.config_file.exists()):
			with open(self.config_file, 'r', encoding='utf-8') as f:
				self.config = json.load(f)
			print(f"설정 파일 로드: {self.config_file}")
		else:
			self.config = self._get_default_config()
			self._save_config()
			print(f"기본 설정 파일 생성: {self.config_file}")


	def _save_config(self) -> None:
		"""
		설정 파일 저장
		"""
		self.config_file.parent.mkdir(parents=True, exist_ok=True)
		with open(self.config_file, 'w', encoding='utf-8') as f:
			json.dump(self.config, f, indent=2, ensure_ascii=False)


	def update_from_args(self, args: argparse.Namespace) -> None:
		"""
		명령줄 인자로 설정 업데이트

		Args:
			args: 명령줄 인자
		"""
		if (args.ffmpeg is not None):
			self.config[ConfigKey.FFMPEG_PATH] = args.ffmpeg
		if (args.ffprobe is not None):
			self.config[ConfigKey.FFPROBE_PATH] = args.ffprobe
		if (args.input is not None):
			self.config[ConfigKey.INPUT_DIR] = args.input
		if (args.output is not None):
			self.config[ConfigKey.OUTPUT_DIR] = args.output
		if (args.sub is not None):
			self.config[ConfigKey.SUBTITLE_DIR] = args.sub
		if (args.crf is not None):
			self.config[ConfigKey.CRF] = args.crf
		if (args.volume is not None):
			self.config[ConfigKey.VOLUME] = args.volume


	def get(self, key: str) -> Any:
		"""
		설정 값 가져오기

		Args:
			key: 설정 키

		Returns:
			설정 값
		"""
		return self.config.get(key)



class VideoEncoder:
	"""
	동영상 인코더 클래스
	"""

	def __init__(self, config: ConfigManager):
		"""
		VideoEncoder 초기화

		Args:
			config: 설정 관리자
		"""
		self.config = config
		self.input_dir = Path(config.get(ConfigKey.INPUT_DIR))
		self.output_dir = Path(config.get(ConfigKey.OUTPUT_DIR))
		self.subtitle_dir = Path(config.get(ConfigKey.SUBTITLE_DIR))
		self.log_dir = Path(config.get(ConfigKey.LOG_DIR))
		self.files: List[FileInfo] = []
		self.current_file_index: int = -1
		self.current_process: Optional[asyncio.subprocess.Process] = None
		self.stop_current: bool = False
		self.stop_all: bool = False
		self._ensure_directories()


	def _ensure_directories(self) -> None:
		"""
		필요한 디렉토리 생성
		"""
		self.output_dir.mkdir(parents=True, exist_ok=True)
		self.log_dir.mkdir(parents=True, exist_ok=True)


	async def get_video_info_with_ffprobe(self, video_file: Path) -> VideoInfo:
		"""
		ffprobe로 동영상 정보 추출

		Args:
			video_file: 동영상 파일 경로

		Returns:
			동영상 정보
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

			process = await asyncio.create_subprocess_exec(
				*cmd,
				stdout=subprocess.PIPE,
				stderr=subprocess.PIPE
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


	def find_subtitle(self, video_file: Path) -> Optional[Path]:
		"""
		동영상 파일에 대응하는 자막 파일 찾기

		Args:
			video_file: 동영상 파일 경로

		Returns:
			자막 파일 경로 또는 None
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


	def generate_output_filename(self, input_file: Path, video_info: VideoInfo, subtitle_file: Optional[Path]) -> str:
		"""
		출력 파일명 생성

		Args:
			input_file: 입력 파일 경로
			video_info: 동영상 정보
			subtitle_file: 자막 파일 경로

		Returns:
			출력 파일명
		"""
		pattern = re.compile(r'^([A-Z]{3,5}-\d{2,5})')
		match = pattern.match(input_file.stem)

		if (not match):
			return input_file.name

		base_name = match.group(1)

		if (video_info.pixel_count >= ConfigDef.HD_THRESHOLD):
			quality_suffix = "-HD"
		else:
			quality_suffix = "-SD"

		subtitle_suffix = "-S" if subtitle_file else ""

		return f"{base_name}{quality_suffix}{subtitle_suffix}.mp4"


	def calculate_scale_filter(self, video_info: VideoInfo) -> Optional[str]:
		"""
		스케일 필터 계산

		Args:
			video_info: 동영상 정보

		Returns:
			스케일 필터 문자열 또는 None
		"""
		if (video_info.pixel_count > ConfigDef.RESOLUTION_THRESHOLD):
			target_height = int(video_info.height * ConfigDef.TARGET_WIDTH / video_info.width)
			target_height = target_height - (target_height % 2)
			return f"scale={ConfigDef.TARGET_WIDTH}:{target_height}"
		return None


	async def get_video_files(self) -> List[Path]:
		"""
		입력 디렉토리에서 MP4 파일 목록 가져오기

		Returns:
			MP4 파일 경로 리스트
		"""
		if (not self.input_dir.exists()):
			return []

		return sorted(self.input_dir.glob("*.mp4"))


	async def prepare_files(self) -> None:
		"""
		파일 목록 준비 및 정보 수집
		"""
		video_files = await self.get_video_files()
		self.files = []

		for video_file in video_files:
			file_info = FileInfo(video_file.name)
			file_info.video_info = await self.get_video_info_with_ffprobe(video_file)
			file_info.subtitle_file = self.find_subtitle(video_file)
			file_info.scale_filter = self.calculate_scale_filter(file_info.video_info)
			file_info.output_filename = self.generate_output_filename(
				video_file,
				file_info.video_info,
				file_info.subtitle_file
			)
			self.files.append(file_info)


	def build_ffmpeg_command(self, file_info: FileInfo) -> List[str]:
		"""
		FFmpeg 명령어 생성

		Args:
			file_info: 파일 정보

		Returns:
			FFmpeg 명령어 리스트
		"""
		input_file = self.input_dir / file_info.filename
		output_file = self.output_dir / file_info.output_filename

		cmd = [
			self.config.get(ConfigKey.FFMPEG_PATH),
			"-i", str(input_file)
		]

		if (file_info.subtitle_file is not None):
			subtitle_path = self.subtitle_dir / file_info.subtitle_file.name
			cmd.extend(["-i", str(subtitle_path)])
		cmd.extend(["-f", "mp4"])
		if (True):
			cmd.extend(["-vf", "scale=1280:720"])

		cmd.extend([
			"-f", "mp4",
			"-c:v", "libx265",
			"-crf:v", str(self.config.get(ConfigKey.CRF)),
			"-preset:v", "slow",
			"-tune:v", "ssim"
		])

		if (file_info.scale_filter is not None):
			volume_filter = f"volume={self.config.get(ConfigKey.VOLUME)}"
			cmd.extend(["-vf", file_info.scale_filter, "-af", volume_filter])
		else:
			cmd.extend(["-af", f"volume={self.config.get(ConfigKey.VOLUME)}"])

		cmd.extend([
			"-c:a", "aac",
			"-b:a", self.config.get(ConfigKey.AUDIO_BITRATE)
		])

		if (file_info.subtitle_file is not None):
			cmd.extend(["-c:s", "mov_text"])

		cmd.extend(["-y", str(output_file)])

		return cmd


	def parse_time_to_seconds(self, time_str: str) -> float:
		"""
		시간 문자열을 초로 변환

		Args:
			time_str: 시간 문자열 (HH:MM:SS.MS)

		Returns:
			초 단위 시간
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
		"""
		FFmpeg 진행률 파싱

		Args:
			line: FFmpeg 출력 라인
			file_info: 파일 정보

		Returns:
			진행률 정보가 파싱되었는지 여부
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


	async def encode_file(self, file_info: FileInfo, websocket_manager: 'WebSocketManager') -> bool:
		"""
		단일 파일 인코딩

		Args:
			file_info: 파일 정보
			websocket_manager: WebSocket 관리자

		Returns:
			인코딩 성공 여부
		"""
		if (self.stop_all):
			return False

		file_info.status = FileStatus.IN_PROGRESS
		self.stop_current = False
		await websocket_manager.broadcast_status(self.get_all_status())

		cmd = self.build_ffmpeg_command(file_info)

		input_file = self.input_dir / file_info.filename
		log_file = self.log_dir / f"{input_file.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

		try:
			with open(log_file, 'wb') as log:
				log.write(" ".join(cmd).encode())
				self.current_process = await asyncio.create_subprocess_exec(
					*cmd,
					stdout=subprocess.PIPE,
					stderr=subprocess.STDOUT,
					creationflags=(
						subprocess.IDLE_PRIORITY_CLASS
						| subprocess.CREATE_NO_WINDOW
					)
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
							await websocket_manager.broadcast_status(self.get_all_status())
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
			await websocket_manager.broadcast_status(self.get_all_status())


	def get_all_status(self) -> Dict[str, Any]:
		"""
		모든 파일 상태 반환

		Returns:
			파일 상태 딕셔너리
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

		return {
			"files": [f.to_dict() for f in self.files],
			"current_index": self.current_file_index,
			"overall_progress": round(overall_progress, 1),
			"completed_count": completed,
			"total_count": total_files
		}


	async def encode_all(self, websocket_manager: 'WebSocketManager') -> None:
		"""
		모든 파일 인코딩

		Args:
			websocket_manager: WebSocket 관리자
		"""
		self.stop_all = False
		await self.prepare_files()
		await websocket_manager.broadcast_status(self.get_all_status())

		for idx, file_info in enumerate(self.files):
			if (self.stop_all):
				break

			if (file_info.status == FileStatus.COMPLETED):
				continue

			self.current_file_index = idx
			await self.encode_file(file_info, websocket_manager)

		self.current_file_index = -1
		await websocket_manager.broadcast_status(self.get_all_status())


	def stop_current_encoding(self) -> bool:
		"""
		현재 인코딩 중단

		Returns:
			중단 명령 성공 여부
		"""
		if (self.current_process is not None):
			self.stop_current = True
			return True
		return False


	def stop_all_encoding(self) -> bool:
		"""
		전체 인코딩 중단

		Returns:
			중단 명령 성공 여부
		"""
		self.stop_all = True
		if (self.current_process is not None):
			self.stop_current = True
			return True
		return False



class WebSocketManager:
	"""
	WebSocket 연결 관리 클래스
	"""

	def __init__(self):
		"""
		WebSocketManager 초기화
		"""
		self.active_connections: List[WebSocket] = []


	async def connect(self, websocket: WebSocket) -> None:
		"""
		WebSocket 연결 추가

		Args:
			websocket: WebSocket 연결
		"""
		await websocket.accept()
		self.active_connections.append(websocket)


	def disconnect(self, websocket: WebSocket) -> None:
		"""
		WebSocket 연결 제거

		Args:
			websocket: WebSocket 연결
		"""
		try:
			self.active_connections.remove(websocket)
		except:
			pass


	async def broadcast_status(self, status: Dict[str, Any]) -> None:
		"""
		모든 연결에 상태 브로드캐스트

		Args:
			status: 상태 정보
		"""
		disconnected = []
		for connection in self.active_connections:
			try:
				await connection.send_json(status)
			except Exception as e:
				print(f"broadcast_status error: {e}")
				traceback.print_exc()
				disconnected.append(connection)

		for connection in disconnected:
			self.disconnect(connection)



app = FastAPI()
websocket_manager = WebSocketManager()
encoder: Optional[VideoEncoder] = None
encoding_task: Optional[asyncio.Task] = None


def create_app() -> FastAPI:
	"""
	SECC UI를 위한 FastAPI 애플리케이션을 생성하고 설정합니다.

	Returns:
		FastAPI: 설정된 FastAPI 애플리케이션 객체입니다.
	"""
	global app

	# 정적 파일 마운트 (CSS, JS, 이미지 등)
	app.mount(
		"/css",
		StaticFiles(directory=ConfigDef.CSS_DIR),
		name="css",
	)
	app.mount(
		"/images",
		StaticFiles(directory=ConfigDef.IMAGES_DIR),
		name="images",
	)
	app.mount(
		"/js",
		StaticFiles(directory=ConfigDef.JS_DIR),
		name="js",
	)


@app.get("/")
async def get_index() -> HTMLResponse:
	"""
	메인 페이지 반환

	Returns:
		HTML 응답
	"""
	template_file = Path("templates/index.html")

	with open(template_file, 'r', encoding='utf-8') as f:
		html_content = f.read()
	return HTMLResponse(content=html_content)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
	"""
	WebSocket 엔드포인트

	Args:
		websocket: WebSocket 연결
	"""
	await websocket_manager.connect(websocket)

	if (encoder is not None):
		await websocket.send_json(encoder.get_all_status())

	try:
		while True:
			await websocket.receive_text()
	except WebSocketDisconnect:
		websocket_manager.disconnect(websocket)


@app.post("/start")
async def start_encoding() -> Dict[str, Any]:
	"""
	인코딩 시작

	Returns:
		결과 딕셔너리
	"""
	global encoding_task

	if (encoding_task is not None and not encoding_task.done()):
		return {"success": False, "message": "이미 인코딩이 진행 중입니다"}

	if (encoder is None):
		return {"success": False, "message": "인코더가 초기화되지 않았습니다"}

	encoding_task = asyncio.create_task(encoder.encode_all(websocket_manager))
	return {"success": True, "message": "인코딩을 시작했습니다"}


@app.post("/stop-current")
async def stop_current_encoding() -> Dict[str, Any]:
	"""
	현재 파일 인코딩 중단

	Returns:
		결과 딕셔너리
	"""
	if (encoder is None):
		return {"success": False, "message": "인코더가 초기화되지 않았습니다"}

	if (encoder.stop_current_encoding()):
		return {"success": True, "message": "현재 파일 인코딩을 중단합니다"}
	else:
		return {"success": False, "message": "진행 중인 인코딩이 없습니다"}


@app.post("/stop-all")
async def stop_all_encoding() -> Dict[str, Any]:
	"""
	전체 인코딩 중단

	Returns:
		결과 딕셔너리
	"""
	if (encoder is None):
		return {"success": False, "message": "인코더가 초기화되지 않았습니다"}

	if (encoder.stop_all_encoding()):
		return {"success": True, "message": "전체 인코딩을 중단합니다"}
	else:
		return {"success": False, "message": "진행 중인 인코딩이 없습니다"}


def parse_arguments() -> argparse.Namespace:
	"""
	명령줄 인자 파싱

	Returns:
		파싱된 인자
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
	return parser.parse_args()


def main():
	"""
	메인 함수
	"""
	global encoder

	args = parse_arguments()

	config = ConfigManager()
	config.update_from_args(args)

	encoder = VideoEncoder(config)

	print("\n" + "="*70)
	print("FFmpeg 웹 기반 동영상 인코딩 시스템")
	print("="*70)
	print(f"FFmpeg 경로: {config.get(ConfigKey.FFMPEG_PATH)}")
	print(f"FFprobe 경로: {config.get(ConfigKey.FFPROBE_PATH)}")
	print(f"입력 디렉토리: {config.get(ConfigKey.INPUT_DIR)}")
	print(f"출력 디렉토리: {config.get(ConfigKey.OUTPUT_DIR)}")
	print(f"자막 디렉토리: {config.get(ConfigKey.SUBTITLE_DIR)}")
	print(f"로그 디렉토리: {config.get(ConfigKey.LOG_DIR)}")
	print(f"CRF: {config.get(ConfigKey.CRF)}")
	print(f"볼륨: {config.get(ConfigKey.VOLUME)}")
	print(f"오디오 비트레이트: {config.get(ConfigKey.AUDIO_BITRATE)}")
	print("="*70)
	print(f"\n웹 인터페이스: http://localhost:{args.port}")
	print("="*70 + "\n")

	import uvicorn
	create_app()
	uvicorn.run(app, host="0.0.0.0", port=args.port)



if (__name__ == "__main__"):
	main()