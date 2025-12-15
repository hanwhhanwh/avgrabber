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
	DEFAULT_INPUT_DIR: Final[str] = "/home/secc/tmp/k2"
	DEFAULT_OUTPUT_DIR: Final[str] = "/home/secc/tmp/_encoded"
	DEFAULT_SUBTITLE_DIR: Final[str] = "/home/secc/tmp/subs"
	DEFAULT_LOG_DIR: Final[str] = "logs"
	DEFAULT_CRF: Final[int] = 27
	DEFAULT_VOLUME: Final[float] = 1.15
	DEFAULT_AUDIO_BITRATE: Final[str] = "128k"

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
		self.status: FileStatus = status
		self.progress: ProgressInfo = ProgressInfo()


	def to_dict(self) -> Dict[str, Any]:
		"""
		딕셔너리로 변환

		Returns:
			파일 정보 딕셔너리
		"""
		return {
			"filename": self.filename,
			"status": self.status.value,
			"progress": {
				"frame": self.progress.frame,
				"fps": self.progress.fps,
				"size": self.progress.size,
				"time": self.progress.time,
				"bitrate": self.progress.bitrate,
				"speed": self.progress.speed
			}
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
		self._ensure_directories()


	def _ensure_directories(self) -> None:
		"""
		필요한 디렉토리 생성
		"""
		self.output_dir.mkdir(parents=True, exist_ok=True)
		self.log_dir.mkdir(parents=True, exist_ok=True)


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


	def get_video_files(self) -> List[Path]:
		"""
		입력 디렉토리에서 MP4 파일 목록 가져오기

		Returns:
			MP4 파일 경로 리스트
		"""
		if (not self.input_dir.exists()):
			return []

		return sorted(self.input_dir.glob("*.mp4"))


	def build_ffmpeg_command(self, input_file: Path, output_file: Path, subtitle_file: Optional[Path] = None) -> List[str]:
		"""
		FFmpeg 명령어 생성

		Args:
			input_file: 입력 파일 경로
			output_file: 출력 파일 경로
			subtitle_file: 자막 파일 경로

		Returns:
			FFmpeg 명령어 리스트
		"""
		cmd = [
			self.config.get(ConfigKey.FFMPEG_PATH),
			"-i", str(input_file)
		]

		if (subtitle_file is not None):
			cmd.extend(["-i", str(subtitle_file)])

		cmd.extend([
			"-f", "mp4",
			"-c:v", "libx265",
			"-crf:v", str(self.config.get(ConfigKey.CRF)),
			"-preset:v", "slow",
			"-tune:v", "ssim",
			"-af", f"volume={self.config.get(ConfigKey.VOLUME)}",
			"-c:a", "aac",
			"-b:a", self.config.get(ConfigKey.AUDIO_BITRATE)
		])

		if (subtitle_file is not None):
			cmd.extend(["-c:s", "mov_text"])

		cmd.extend(["-y", str(output_file)])

		return cmd


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
		input_file = self.input_dir / file_info.filename
		output_file = self.output_dir / file_info.filename
		subtitle_file = self.find_subtitle(input_file)

		file_info.status = FileStatus.IN_PROGRESS
		await websocket_manager.broadcast_status(self.get_all_status())

		cmd = self.build_ffmpeg_command(input_file, output_file, subtitle_file)

		log_file = self.log_dir / f"{input_file.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

		try:
			# with open(log_file, 'wb', encoding='utf-8') as log:
			with open(log_file, 'wb') as log:
				log.write(" ".join(cmd).encode())
				process = await asyncio.create_subprocess_exec(
					*cmd,
					stdout=subprocess.PIPE,
					stderr=subprocess.STDOUT
				)

				buffer = b""
				while True:
					chunk = await process.stdout.read(1)
					if (not chunk):
						break

					log.write(chunk)
					# if ((chunk != '\r') and (chunk != '\n')):
					if ((chunk != b'\r') and (chunk != b'\n')):
						buffer += chunk
						continue

					buffer += b'\n'
					line_str = buffer.decode('utf-8', errors='ignore')
					# log.write(line_str)
					# log.flush()
					buffer = b""

					if (self.parse_progress(line_str, file_info)):
						await websocket_manager.broadcast_status(self.get_all_status())

				await process.wait()

				if (process.returncode == 0):
					file_info.status = FileStatus.COMPLETED
					return True
				else:
					file_info.status = FileStatus.FAILED
					return False

		except Exception as e:
			print(f"인코딩 오류: {e}")
			file_info.status = FileStatus.FAILED
			return False
		finally:
			await websocket_manager.broadcast_status(self.get_all_status())


	def get_all_status(self) -> Dict[str, Any]:
		"""
		모든 파일 상태 반환

		Returns:
			파일 상태 딕셔너리
		"""
		return {
			"files": [f.to_dict() for f in self.files],
			"current_index": self.current_file_index
		}


	async def encode_all(self, websocket_manager: 'WebSocketManager') -> None:
		"""
		모든 파일 인코딩

		Args:
			websocket_manager: WebSocket 관리자
		"""
		video_files = self.get_video_files()
		self.files = [FileInfo(f.name) for f in video_files]

		await websocket_manager.broadcast_status(self.get_all_status())

		for idx, file_info in enumerate(self.files):
			self.current_file_index = idx
			await self.encode_file(file_info, websocket_manager)

		self.current_file_index = -1
		await websocket_manager.broadcast_status(self.get_all_status())



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
		self.active_connections.remove(websocket)


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
			except Exception:
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

	# 템플릿 설정
	templates = Jinja2Templates(directory=ConfigDef.TEMPLATES_DIR)


	@app.get("/")
	async def get_index(request: Request) -> HTMLResponse:
		"""
		메인 페이지 반환

		Returns:
			HTML 응답
		"""
		return templates.TemplateResponse(
			"index.html",
			{"request": request},
			status_code=status.HTTP_200_OK,
		)


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



def parse_arguments() -> argparse.Namespace:
	"""
	명령줄 인자 파싱

	Returns:
		파싱된 인자
	"""
	parser = argparse.ArgumentParser(description="FFmpeg 웹 기반 동영상 인코딩 시스템")
	parser.add_argument("--ffmpeg", type=str, help="FFmpeg 실행 파일 경로")
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
	print("FFmpeg 동영상 인코딩 시스템")
	print("="*70)
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